from google.cloud import vision
from google.cloud.vision import types
import webcolors
import os
import re

from . import security
import hashlib

###############################################################################


def closest_colour(requested_colour):
    min_colours = {}
    # change html4 to css3, css21, ...
    for key, name in webcolors.html4_hex_to_names.items():
        r_c, g_c, b_c = webcolors.hex_to_rgb(key)
        rd = (r_c - requested_colour[0]) ** 2
        gd = (g_c - requested_colour[1]) ** 2
        bd = (b_c - requested_colour[2]) ** 2
        min_colours[(rd + gd + bd)] = name
    return min_colours[min(min_colours.keys())]


def get_colour_name(requested_colour):
    try:
        closest_name = actual_name = webcolors.rgb_to_name(requested_colour)
    except ValueError:
        closest_name = closest_colour(requested_colour)
        actual_name = None
    return actual_name, closest_name

###############################################################################


client = vision.ImageAnnotatorClient()
MAXIMUM_BATCH_SIZE_BYTES = 10485760


def get_image(image_path, user):

    # username = user.username
    # key = hashlib.sha256(username.encode('utf-8')).digest()
    # print("Decrypting", image_path)
    # security.decrypt_file(key, image_path + '.enc', image_path)

    with open(image_path, 'rb') as image_file:
        content = image_file.read()

    image = types.Image(content=content)
    return image


def get_labels(image):
    response = client.label_detection(image=image)
    labels = response.label_annotations

    labels_info = []
    for label in labels:
        info = {}
        info['description'] = label.description
        if info['description'] == '':
            continue
        info['score'] = label.score
        labels_info.append(info)
    return labels_info


def get_text(image):
    text = {}
    text['description'] = client.document_text_detection(image=image).full_text_annotation.text.strip()
    text['score'] = 1
    if text['description'] == '':
        return []
    return [text]


def get_logos(image):
    logos = []
    for logo in client.logo_detection(image=image).logo_annotations:
        info = {}
        info['description'] = logo.description
        if info['description'] == '':
            continue
        info['score'] = logo.score
        logos.append(info)
    return logos


def get_colors(image):
    colors = client.image_properties(image=image).image_properties_annotation.dominant_colors.colors
    dominant = []
    for color in colors:
        c = color.color
        rgb = (c.red, c.green, c.blue)

        actual_name, closest_name = get_colour_name(rgb)

        color_info = {}
        color_info['description'] = closest_name
        color_info['score'] = color.score
        color_info['fraction'] = color.pixel_fraction

        if closest_name not in [color['description'] for color in dominant]:
            dominant.append(color_info)
    return dominant


def get_landmarks(image):
    landmarks = []
    for landmark in client.landmark_detection(image=image).landmark_annotations:
        info = {}
        info['description'] = landmark.description
        if info['description'] == '':
            continue
        info['score'] = landmark.score
        landmarks.append(info)
    return landmarks


def get_web_entities(image):
    entities = []
    for entity in client.web_detection(image=image).web_detection.web_entities:
        info = {}
        info['description'] = entity.description
        if info['description'] == '':
            continue
        info['score'] = entity.score
        entities.append(info)
    return entities


def get_faces(image, threshold=0):
    faces = []

    for face in client.face_detection(image=image).face_annotations:
        info = {}
        if face.detection_confidence > threshold:
            info['description'] = 'person'
            info['score'] = face.detection_confidence
            coords = list(face.bounding_poly.vertices)
            info['box'] = tuple((coords[0].x, coords[0].y, coords[2].x, coords[2].y))
            faces.append(info)
    return faces

################################################################################


def tag_image(image_path):

    """
    Arg: image path
    Returns: a list of labels
    """
    image = get_image(image_path)
    response = client.label_detection(image=image)
    labels = response.label_annotations

    labels_info = []
    for label in labels:
        info = {}
        info['description'] = label.description
        info['score'] = label.score
        labels_info.append(info)

    print("FROM TAG_IMAGE:\n", labels_info)
    print()

    return labels_info

# TODO: Improve get_text and get_labels...
INFO_EXTRACTION_FUNCTIONS = [get_labels, get_text, get_logos,
                             get_colors, get_landmarks, get_web_entities, get_faces]


def get_image_info(image_path):
    info = []

    image = get_image(image_path)
    for extractor in INFO_EXTRACTION_FUNCTIONS:
        # info.append(extractor(image))
        info += extractor(image)
    return info


##############################################################################
#                              FEATURE EXTRACTION                            #
##############################################################################


FEATURES = ['FACE_DETECTION',
                 'LANDMARK_DETECTION', 'LOGO_DETECTION',
                 'LABEL_DETECTION', 'TEXT_DETECTION',
                 # 'DOCUMENT_TEXT_DETECTION',
                 'IMAGE_PROPERTIES', 'WEB_DETECTION']
FACE_THRESHOLD = 0
IGNORE_LIST = ['person']


def add_description_and_score(info, type, category):
    for t in type:
        if t.description != '' and t.description not in IGNORE_LIST:
            info.append({'description': t.description,
                         'score': t.score,
                         'category': category})
    return info


def add_colors(info, colors):
    dominant = []
    for color in colors:
        c = color.color
        rgb = (c.red, c.green, c.blue)

        actual_name, closest_name = get_colour_name(rgb)

        color_info = {}
        color_info['description'] = closest_name
        color_info['score'] = color.score
        color_info['fraction'] = color.pixel_fraction
        color_info['category'] = 'color'

        if closest_name not in [color['description'] for color in dominant]:
            dominant.append(color_info)
    info += dominant
    return info


def add_faces(info, faces, threshold=FACE_THRESHOLD):
    for face in faces:
        face_info = {}
        if face.detection_confidence > threshold:
            face_info['description'] = 'person'
            face_info['score'] = face.detection_confidence
            coords = list(face.bounding_poly.vertices)
            face_info['box'] = \
                tuple((coords[0].x, coords[0].y, coords[2].x, coords[2].y))

            face_info['category'] = 'face'
            info.append(face_info)

    return info


def add_text(info, text):

    # to remove multiple whitespace
    if len(list(text)) == 0:
        return info
    text = text[0].description
    text = text.strip()
    text = re.sub('\n', ' ', text)
    text = re.sub(' +', ' ', text)

    text_info = {}
    text_info['description'] = text
    text_info['score'] = 1
    if text_info['description'] == '':
        return info

    text_info['category'] = 'text'
    info.append(text_info)

    return info


def get_all_info(response):

    """
    For each image, info is a list of features that describe that image.
    Each feature is a dictionary containing, at least,
        the description of that feature ('description') or characteristic and
        the confidence score ('score').
    It may also have a bounding box ('box') e.g. if it is a face.

    Example:
        info['cat01.jpg'] = [{'description': 'white cat', 'score: 0.96'}, ...]
    """

    faces = response.face_annotations
    landmarks = response.landmark_annotations
    logos = response.logo_annotations
    labels = response.label_annotations
    text = response.text_annotations
    # doc_text = response.full_text_annotation
    colors = response.image_properties_annotation.dominant_colors.colors
    web_entities = response.web_detection.web_entities

    info = []

    type_categories = {'face': faces,
					   'landmark': landmarks,
					   'logo': logos,
					   'label': labels,
					   'text': text,
					   'color': colors,
					   'web entity': web_entities}

    # for type in [labels, landmarks, logos, web_entities]:
	#     print(type)
	#     info = add_description_and_score(info, type)

    for category in ['label', 'landmark', 'logo', 'web entity']:
	    type = type_categories[category]
	    info = add_description_and_score(info, type, category)

    info = add_colors(info, colors)
    info = add_faces(info, faces)
    info = add_text(info, text)

    return info

##############################################################################
#                                BATCH TAGGING                               #
##############################################################################


def build_requests(paths, user):
    requests = []
    for idx, image_path in enumerate(paths):
        if os.path.isdir(image_path):
            continue
        print("[TAGGER] Building request", idx + 1, "of", len(paths))
        request = {}
        features = []

        for feature_type in FEATURES:
            feature = {}
            feature['type'] = feature_type
            # feature['maxResults'] = 5
            # feature['model'] = 'builtin/latest'
            features.append(feature)

        request['image'] = get_image(image_path, user)
        request['features'] = features
        requests.append(request)
    return requests


def batch_requests(requests, batch_size=15):
    i = 0
    done = False
    batches = []
    request_size = 0

    while not done:
        print("[TAGGER] Batching requests,", len(batches),
                "batches completed, with",
                max(len(requests) - len(batches) * batch_size, 0),
                "requests to go")
        batch = []
        batch_size_bytes = 0

        # When to stop building the current batch
        while (batch_size_bytes + request_size) <= MAXIMUM_BATCH_SIZE_BYTES \
                and len(batch) < batch_size:

            request = requests[i]
            batch.append(request)

            if i == len(requests) - 1:
                done = True
                break

            i += 1

            batch_size_bytes = sum(len(req['image'].content) for req in batch)
            request_size = len(requests[i]['image'].content)
        print("[TAGGER] Built batch with", len(batch), "images")
        batches.append(batch)

    print("[TAGGER]", len(batches), "batches were built")


    # while not done:
    #     print("[TAGGER] Batching requests,", len(batches),
    #         "batches completed, with",
    #         max(len(requests) - len(batches) * batch_size, 0), "requests to go")
    #     batch = []
    #
    #     #####################
    #     #   Batch building  #
    #     #####################
    #     for j in range(i, i + batch_size):
    #
    #         batch_size_bytes = sum(len(k['image'].content) for k in batch)
    #         request_size = len(requests[j]['image'].content)
    #
    #         if batch_size_bytes + request_size > MAXIMUM_BATCH_SIZE_BYTES:
    #             break
    #
    #         batch.append(requests[j])
    #         if j >= len(requests) - 1:
    #             done = True
    #             break
    #     batches.append(batch)
    #
    #     i += batch_size
    return batches


def batch_tag(paths, user):

    client = vision.ImageAnnotatorClient()
    requests = build_requests(paths, user)
    print(client)
    batches = batch_requests(requests, batch_size=15)
    all_responses = []
    for idx, batch in enumerate(batches):
        print("[TAGGER] Annotating batch", idx + 1, "of", len(batches))
        responses = client.batch_annotate_images(batch)
        all_responses.append(responses)

    tags = {}
    idx = 0
    for batch in all_responses:
        responses = batch.responses
        for response in responses:
            print("[TAGGER] Extracting information from photo", idx + 1,
                "of", len(paths))
            # image = paths[idx]
            tags[idx] = get_all_info(response)
            idx += 1
    return tags
