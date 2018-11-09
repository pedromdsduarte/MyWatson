from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views import generic
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseForbidden, JsonResponse
from django.urls import reverse
from django import forms
from django.http import Http404

from django.shortcuts import render_to_response
from django.template import RequestContext

from .models import Photo, Tag, InvertedIndex, Face, FaceCluster, UserPreferences
from .forms import ImageUploadForm

from .app_modules import MyWatsonApp, security
from mywatson_site.settings import BASE_DIR, MEDIA_ROOT
import os
from PIL import Image
from sorl.thumbnail import ImageField
from django.core.files.images import ImageFile
from .vars import *

import urllib.parse

import json
from django.core import serializers

import html

from django.template.defaulttags import register

import hashlib


###############################################################################

def handler404(request, exception, template_name='404.html'):
    response = render_to_response('404.html', {},
                                  context_instance=RequestContext(request))
    response.status_code = 404
    return response


def handler500(request, exception, template_name='500.html'):
    response = render_to_response('500.html', {},
                                  context_instance=RequestContext(request))
    response.status_code = 500
    return response

###############################################################################


def sizeof_fmt(num, suffix='B'):
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def get_user_id(request):
	return request.user.id


def new_face(photo, box, tag):
	image_path_tokens = photo.image.url.split("/")
	image_path_file = image_path_tokens[-1]
	ext = image_path_file.split(".")[-1]
	# face_file_name = image_path_file.split(".")[0] + "_face_0." + ext
	face_file_name = image_path_file.split(".")[0]
	user_name = photo.user.username
	face_folder = os.path.join(FACE_IMAGES_FOLDER, user_name)

	if not os.path.exists(face_folder):
		os.makedirs(face_folder)

	face = Face.objects.create(user=photo.user, tag=tag)
	id = face.id

	# django_face_file_path = user folder to save the face image: "faces/Watson"
	django_face_file_path = os.path.join("faces", user_name)

	# face_file_name: "pedro_1_face_99.jpg"
	face_file_name = face_file_name + "_face_" + str(id) + "." + ext

	# face_path = full path of the file
	face_path = os.path.join(FACE_IMAGES_FOLDER, user_name, face_file_name)

	crop(photo.image, box, face_path)

	# face.face = relative path to the media folder: "faces\Watson\pedro_face.jpg"

	face.face = os.path.join(django_face_file_path, face_file_name).replace("\\", "/")
	face.photo = photo
	face.save()


def new_tag(photo, tag, category='label', score=1, bounding_box=None):
	# TODO: Check if a tag with this text already exists
	# if it does, fail?

	# TODO: This function is probably not needed anymore

	if bounding_box is not None:
		x1 = bounding_box[0]
		y1 = bounding_box[1]
		x2 = bounding_box[2]
		y2 = bounding_box[3]
		new_tag = Tag.objects.create(tag=tag, score=score, photo=photo,
									startX=x1, startY=y1,
									endX=x2, endY=y2)
		if tag == 'person':
			new_face(photo, bounding_box, new_tag)

	else:

		# Now: If a tag with the same name already exists in this photo,
		# do not assign the new one
		# FIXME: Better way to do this?

		if len(Tag.objects.filter(photo=photo, tag=tag)) == 0:
			new_tag = Tag.objects.create(tag=tag, score=score, photo=photo, category=category)
			InvertedIndex.objects.create(tag=new_tag, photo=photo)
			return new_tag


def remove_tag(photo, tag_id):
	# Tag.objects.filter(photo=photo, tag=tag).delete()
	Tag.objects.get(pk=tag_id).delete()


def remove_photo(photo_id):
	Photo.objects.get(pk=photo_id).delete()


def add_tags(photo):

	path = os.path.join(BASE_DIR, 'public', os.path.normpath(photo.image.url)[1:])

	tags = MyWatsonApp.tag_image(path)

	print()

	for tag in tags:
		"""
		Only the description t[0] and score t[1]
		are needed for now
		"""

		# tag = Tag.objects.create(tag=t[0], score=t[1], photo=photo)
		# new_tag(photo, t[0], t[1])

		# TODO: remove repeated tags
		# TODO: differentiate type of tag? (landmark, text, color)???
		print(tag)
		description = (tag['description'][:TAG_MAX_SIZE] + '...') \
		 				if len(tag['description']) > TAG_MAX_SIZE \
						else tag['description']

		box = tag['box'] if 'box' in tag else None
		new_tag(photo, description, score=tag['score'], bounding_box=box)


def add_batch_tags(photos, user):

    paths = []
    for photo in photos:

        path = os.path.join(BASE_DIR, 'public', os.path.normpath(photo.image.url)[1:])
        path = urllib.parse.unquote(path)
        if os.stat(path).st_size <= IMG_MAX_SIZE_BYTES:
            paths.append(path)
        else:
            print("[TAGGING] ERROR: File is too big! Discarding...")
            print("(" + path + ")\n")
    if len(paths) <= 0:
        print("[TAGGING] No image was tagged.")
        return

    all_tags = MyWatsonApp.batch_tag(paths, user)
    tags_to_create = []
    descriptions = {}

    for i in range(len(photos)):
        photo = photos[i]
        tags = all_tags[i]
        for tag in tags:
            print(tag)
            description = (tag['description'][:TAG_MAX_SIZE] + '...') \
			 				if len(tag['description']) > TAG_MAX_SIZE \
							else tag['description']

            box = tag['box'] if 'box' in tag else None
            if box is None:
                box = [None] * 4
            x1 = box[0]
            y1 = box[1]
            x2 = box[2]
            y2 = box[3]

            category = tag['category']
            score = tag['score']
            new_tag = Tag(tag=description, category=category, score=score,
							startX=x1, startY=y1,
							endX=x2, endY=y2,
							photo=photo)

            if photo not in descriptions:
                descriptions[photo] = []

			# If a photo already has a tag, do not add the same
			# unless it is a person with a bounding box
            if description not in descriptions[photo] or \
						(description == 'person' and x1 is not None):

                descriptions[photo].append(description)
                tags_to_create.append(new_tag)

			# new_tag(photo, description, score=tag['score'], bounding_box=box)
    Tag.objects.bulk_create(tags_to_create)

    for tag in tags_to_create:
        if tag.tag == 'person' and tag.startX is not None:

			# Prevent duplicate tags containing the same face
			# This is only needed due to the bulk_create() call
            Tag.objects.get(
				photo=tag.photo,
				tag=tag.tag,
				startX=tag.startX,
				startY=tag.startY,
				endX=tag.endX,
				endY=tag.endY).delete()
            tag.save()
            box = [tag.startX, tag.startY, tag.endX, tag.endY]
            print("[MYWATSON] Extracting person face from", tag.photo)
            new_face(tag.photo, box, tag)


def crop(image_path, bounding_box, saved_location, resized_resolution=None):
	"""
	@param image_path: The path to the image to edit
	@param bounding_box: A tuple of x/y coordinates (x1, y1, x2, y2)
	@param saved_location: Path to save the cropped image
	"""

	image_obj = Image.open(image_path)

	# Ratio between the canvas on the browser and the original image
	if resized_resolution is not None:
		Rx = image_obj.width / resized_resolution[0]
		Ry = image_obj.height / resized_resolution[1]

		"""
		This method resizes the bounding box to the original ratio
		"""
		coords = (round(Rx * bounding_box[0]), round(Ry * bounding_box[1]),
				round(Rx * bounding_box[2]), round(Ry * bounding_box[3]))
	else:
		coords = bounding_box

	"""
	This method crops the resized image
	"""
	# coords = bounding_box
	# resized_image = image_obj.resize(resized_resolution, Image.ANTIALIAS)
	# cropped_img = resized_image.crop(coords)

	cropped_img = image_obj.crop(coords)
	cropped_img.save(saved_location)
	return coords


def get_next_number_file(folder, name):
	same_name_files = []
	for f in os.listdir(folder):
		if f.startswith(name.lower()):
			same_name_files.append(f)

	"""
	Gets the next number to append to the path
	e.g. if the last file was 'sun_3.jpg', this file will be 'sun_4.jpg'
	"""

	number = int(same_name_files[-1].split('.')[0].split('_')[-1]) + 1
	return number


def add_new_tag(photo, tag, bounding_box, resized_resolution):

	#############################################
	# In case of a person...
	#############################################
	is_person = False

	if ":" in tag:
		tokens = tag.split(":")
		if tokens[0] == "person":
			is_person = True
			tag = tokens[-1].strip()
			folder = FACE_IMAGES_FOLDER

	else:
		folder = CROPPED_IMAGES_FOLDER
	save_location = os.path.join(folder, tag.lower() + '_0.jpg')



	if os.path.exists(save_location):
		# number = get_next_number_file(folder, name)
		"""
		Gets the images that correspond to the same tag
		"""
		same_name_files = []
		for f in os.listdir(folder):
			if f.startswith(tag.lower()):
				same_name_files.append(f)

		"""
		Gets the next number to append to the path
		e.g. if the last file was 'sun_3.jpg', this file will be 'sun_4.jpg'
		"""

		number = int(same_name_files[-1].split('.')[0].split('_')[-1]) + 1
		save_location = os.path.join(folder, tag.lower()+'_'+str(number)+'.jpg')

	coords = crop(photo.image, bounding_box, save_location, resized_resolution=resized_resolution)
	new_tag(photo, tag, bounding_box=coords)

	if is_person:
		Face.objects.create(face=save_location, photo=photo)

	return

###############################################################################


class GalleryView(generic.ListView):
	template_name = 'mywatson/index.html'
	context_object_name = 'photos'

	def get_queryset(self):
		return Photo.objects.filter(user=self.request.user).order_by('-date_modified')


class DetailView(generic.DetailView):
	model = Photo
	template_name = 'mywatson/photo_details.html'
	context_object_name = 'photo'

	next_photo = None
	previous_photo = None
	tags = []
	width = 0
	height = 0

	def post(self, request, *args, **kwargs):

		photo = get_object_or_404(Photo, pk=self.kwargs['pk'], user_id=self.request.user.id)

		if request.POST.get('remove_tag'):
			tag = request.POST.get('tag_id')
			print("[DEBUG] Removing tag", tag)
			remove_tag(photo, tag)

		elif request.POST.get('remove_photo'):
			photo_id = request.POST.get('photo')
			print("[DEBUG] Removing photo", photo_id)
			deleted_photo = self.get_object()

			remove_photo(photo_id)

			photo = self.next_photo

			if deleted_photo == photo:
				photo = self.previous_photo
			if deleted_photo == photo:
				return HttpResponseRedirect(reverse('mywatson:index'))

		elif request.POST.get('new_tag'):
			tag = request.POST.get('new_tag')
			print("[DEBUG] Adding tag", tag)
			new_id = new_tag(photo, tag).id
			return JsonResponse({'new_tag_id': new_id})

		elif request.POST.get('retag'):
			id = int(request.POST.get('retag'))
			print("[DEBUG] Retagging photo", str(id))
			image_to_retag = Photo.objects.get(id=id)

			Tag.objects.filter(photo_id=id).delete()
			add_batch_tags([image_to_retag], request.user)

			return HttpResponseRedirect(reverse('mywatson:photo', args=[photo.id]))

		return HttpResponseRedirect(reverse('mywatson:photo', args=[photo.id]))

	def get_object(self):

		photos = Photo.objects.filter(user=self.request.user).order_by('-date_modified')

		photo = get_object_or_404(Photo, pk=self.kwargs['pk'], user_id=self.request.user.id)

		photos_list = list(photos)

		if photos.last() == photo:
			self.previous_photo = photos_list[photos_list.index(photo) - 1]
			self.next_photo = photo

		elif photos.first() == photo:
			self.previous_photo = photo
			self.next_photo = photos_list[photos_list.index(photo)+1]

		else:
			self.previous_photo = photos_list[photos_list.index(photo)-1]
			self.next_photo = photos_list[photos_list.index(photo)+1]

		self.tags = Tag.objects.filter(photo=photo)

		# username = str(self.request.user)
		# key = hashlib.sha256(username.encode('utf-8')).digest()
		# security.decrypt_file(key, photo.image.path + '.enc', photo.image.path)

		img = Image.open(photo.image)
		self.width = img.width
		self.height = img.height

		return photo


class QueryResultsView(generic.ListView):
	template_name = 'mywatson/results.html'
	context_object_name = 'results'
	previous_query = "Search"

	def get_queryset(self):
		"""
		Should return the photos that correspond to the query
		"""

		query = self.request.GET.get('q')
		user = self.request.user
		self.previous_query = query

		# Results from all users
		results = MyWatsonApp.get_results(query, user)

		# TODO: Remove
		# user_results = [res for res in results if res.user.id == self.request.user.id]

		return results


class AddTagView(generic.DetailView):

	Model = Photo
	template_name = 'mywatson/add_tag.html'
	context_object_name = 'photo'

	def get_object(self):
		photo = get_object_or_404(Photo, pk=self.kwargs['pk'], user_id=self.request.user.id)
		return photo

	def post(self, request, *args, **kwargs):
		print("\n ---- DATA RECEIVED ----\n")

		tag = request.POST.get('tag')
		startX = float(request.POST.get('startX'))
		startY = float(request.POST.get('startY'))
		endX = float(request.POST.get('endX'))
		endY = float(request.POST.get('endY'))
		resized_w = int(request.POST.get('resized_w'))
		resized_h = int(request.POST.get('resized_h'))

		bounding_box = [startX, startY, endX, endY]

		print('PHOTO ID:', request.POST.get('photo_id'))
		print('TAG:', tag)
		print('startX:', startX)
		print('startY:', startY)
		print('endX:', endX)
		print('endY:', endY)
		print('resized_w:', resized_w)
		print('resized_h:', resized_h)

		print("\n------------------------\n")

		photo = get_object_or_404(Photo, pk=self.kwargs['pk'], user_id=self.request.user.id)
		resized_resolution = [resized_w, resized_h]

		add_new_tag(photo, tag, bounding_box, resized_resolution)

		return HttpResponseRedirect(reverse('mywatson:photo', args=[photo.id]))


class ClusterView(generic.ListView):
	template_name = 'mywatson/people.html'

	# Dictionary: nclusters -> List of FaceCluster objects
	context_object_name = 'clusters'
	groups = {}
	n_clusters = -1
	groups_json = {}
	media_url = os.path.basename(MEDIA_ROOT)
	min_clusters = 1
	max_clusters = 6

	def group_clusters(self, clusters):
		# groups: n_clusters -> dictionary of faceclusters
		# groups[n_clusters]: cluster_id -> list of faces

		for cluster in clusters:
			n_cluster = cluster.n_clusters
			if n_cluster not in self.groups:
				self.groups[n_cluster] = {}

			cluster_id = cluster.cluster_id
			if cluster_id not in self.groups[n_cluster]:
				self.groups[n_cluster][cluster_id] = []
			if cluster not in self.groups[n_cluster][cluster_id]:
				self.groups[n_cluster][cluster_id].append(cluster)

	def get_queryset(self):

		"""
		Should return the photos that have people in it
		"""

		results = MyWatsonApp.get_results("person", self.request.user)
		# user_results = \
		# 	[res for res in results if res.user.id == self.request.user.id]
		faces = MyWatsonApp.get_faces(results)
		if len(faces) == 0:
			return []
		all_clusters = []

		# groups, clusters = MyWatsonApp.get_clusters(faces)

		self.groups = {}
		self.max_clusters = len(faces)

		all_cluster_groups, changes = \
			MyWatsonApp.get_all_cluster_groups(faces,
												self.min_clusters,
												self.max_clusters)
		if changes:
			FaceCluster.objects.bulk_create(all_cluster_groups)


		all_clusters.append(all_cluster_groups)
		self.group_clusters(all_cluster_groups)

		# Get the user preference on the number of clusters to display
		try:
			self.n_clusters = \
				UserPreferences.objects.get(user=self.request.user).n_clusters
		except UserPreferences.DoesNotExist:
			print("[DEBUG] User had no preferences yet! Creating...")
			UserPreferences.objects.create(user=self.request.user,
											n_clusters=-1)

		# Prepare data to send to template
		self.groups_json = serializers.serialize('json',
				list(FaceCluster.objects.filter(user=self.request.user)))
		self.groups_json = json.loads(self.groups_json)
		for fc in self.groups_json:
			face = Face.objects.get(id=fc['fields']['face'])
			fc['fields']['face_url'] = \
				str(face.face)
			fc['fields']['photo_url'] = \
				str(reverse('mywatson:photo', kwargs={'pk': face.photo.id}))
		self.groups_json = json.dumps(self.groups_json)

		return all_clusters

	def post(self, request, *args, **kwargs):

		"""
		Handles the changes made by the user on the clusters
		"""

		clusters = json.loads(request.POST.get('clusters'))
		cluster_names = json.loads(request.POST.get('cluster_names'))
		n_clusters = len(clusters)

		print("\n ---- DATA RECEIVED ----\n")
		print("Clusters:", clusters)
		print("Cluster names:", cluster_names)
		print("N-Clusters:", n_clusters)
		print("\n ----- END OF DATA ----- \n")

		user = request.user
		old_face_clusters = FaceCluster.objects.filter(n_clusters=n_clusters,
														user=user)
		diff_clusters = {}
		diff_names = {}
		new_clusters = {}

		inv_clusters = dict((v, k) for k in clusters for v in clusters[k])

		# Check if anything was changed
		for ofc in old_face_clusters:
			cid = str(ofc.cluster_id)

			if cluster_names[cid] == '':
				if ofc.name == '':
					cluster_names[cid] = 'Cluster ' + str(cid)
				else:
					cluster_names[cid] = ofc.name
			cluster_names[cid] = html.escape(cluster_names[cid])
			if cid not in diff_clusters:
				diff_clusters[cid] = []
			diff_clusters[cid].append(str(ofc.face_id))

			if ofc.face_id not in new_clusters:
				# new_clusters[ofc.face_id] = cid
				new_clusters[ofc.face_id] = inv_clusters[str(ofc.face_id)]

			if cid not in diff_names:
				diff_names[cid] = str(ofc.name)
		user_preferences = UserPreferences.objects.get(user=user)
		user_preferences.n_clusters = n_clusters
		user_preferences.save()

		# If nothing was changed, simply return
		if cluster_names == diff_names and clusters == diff_clusters:
			print("[DEBUG] No changes were made to the clusters")
			return HttpResponse()
		else:
			for ofc in old_face_clusters:
				ofc.cluster_id = new_clusters[ofc.face_id]
				ofc.name = cluster_names[str(ofc.cluster_id)]

				# If it is a user-generated cluster, give it maximum score
				if cluster_names == diff_names and clusters != diff_clusters:
					ofc.silhouette_score = 1
				ofc.save()

				# If the user gave the cluster a name, assign the name to all
				# the photos in the cluster
				if not ofc.name.startswith("Cluster"):
					photo = Face.objects.get(id=ofc.face_id).photo
					new_tag(photo, ofc.name)
			return HttpResponse()


@login_required
def get_people(request):
	return render(request, 'mywatson/get_people.html')

##########################################################################


images_to_tag = []


@login_required
def upload_photo(request):
	if request.method == 'POST':

		if request.POST.get('upload_done') and request.POST.get('upload_done') == 'true':
			global images_to_tag
			add_batch_tags(images_to_tag, request.user)
			images_to_tag = []
			data = {'tagging_complete': True}
			return JsonResponse(data)
		else:

			form = ImageUploadForm(request.POST, request.FILES)
			file = request.FILES.get('image')

			if form.is_valid():

				photo = Photo(image=file, user=request.user)
				photo.save()

				# photo_path = photo.image.url.replace('/', '\\')
				photo_path = photo.image.url
				photo_path = urllib.parse.unquote(photo_path)
				file_path = os.path.join(BASE_DIR, 'public') + photo_path

				#
				# username = request.user.username
				# key = hashlib.sha256(username.encode('utf-8')).digest()
				# security.encrypt_file(key, file_path)
				data = {'is_valid': True,
						'name': str(file),
						'url': photo.image.url,
						'size': sizeof_fmt(os.stat(file_path).st_size)}
				images_to_tag.append(photo)
			else:
				print("[DEBUG] Form not valid")
				data = {'is_valid': False,
						'size': sizeof_fmt(os.stat(file_path).st_size)}

			return JsonResponse(data)

	else:
		form = ImageUploadForm()
		return render(request, 'mywatson/upload_page.html', {'form': form})


# TODO: Retrieve & Rank decente
# TODO: Query Expansion


@register.filter
def get_item(dictionary, key):
	return dictionary.get(key)
