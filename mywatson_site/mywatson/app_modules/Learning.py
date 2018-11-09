import numpy as np
import os
import math

import tensorflow as tf

from keras.preprocessing import image
from keras.applications.vgg16 import preprocess_input
from keras_vggface.vggface import VGGFace

from keras_vggface import utils

from keras import backend as K
from keras.models import model_from_json

from mywatson_site.settings import MEDIA_ROOT
from mywatson.models import FaceCluster, Features
from django.core.exceptions import ObjectDoesNotExist


from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.metrics import silhouette_score
from mywatson.vars import ConsoleColors

import tempfile
import keras.models
import pickle
import json


os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
GLOBAL_MODEL = None
GLOBAL_GRAPH = None

###############################################################################
######################## 		MODEL HANDLING 			#######################
###############################################################################

def save_model(model, weight_file, model_file):

    print("[CLUSTERING] Saving weights to", weight_file)

    model.save_weights(weight_file)
    model_json = model.to_json()
    print("[CLUSTERING] Saving model to", model_file)
    with open(model_file, "w") as json_file:
        json_file.write(model_json)
    global GLOBAL_MODEL
    GLOBAL_MODEL = model

    """
    with open('_model.pkl', 'wb') as output_file:
        pickle.dump(model, output_file)
    """


def load_model(weight_file, model_file):

    global GLOBAL_MODEL
    if GLOBAL_MODEL is not None:
        print("[CLUSTERING] Found a model already instantiated!")
        return GLOBAL_MODEL

    with open(model_file, "r") as json_file:
        loaded_model_json = json_file.read()
        model = model_from_json(loaded_model_json)
        model.load_weights(weight_file)

    """
    with open('_model.pkl', 'rb') as input_file:
        model = pickle.load(input_file)
    """

    return model


def get_model():

    # FIXME: weights can't be saved in another directory
    # For now, they are saved in the project root
    MODEL_FILE = "model.json"
    WEIGHT_FILE = "weights.h5"

    try:
        print()
        print("[CLUSTERING] Loading model from file:", MODEL_FILE)
        model = load_model(WEIGHT_FILE, MODEL_FILE)
    except OSError as e:
        print("[CLUSTERING] No model found:", str(e))
        print("[CLUSTERING] Creating model...")
        # model = VGGFace(model='resnet50', input_shape=(224, 224, 3), include_top=False)

        # FIXME Everytime this model is changed, the old model files should be deleted!
        # model = VGGFace(model='vgg16', input_shape=(224, 224, 3), include_top=False)
        model = VGGFace(model='resnet50', input_shape=(224, 224, 3), include_top=False)
        try:
            save_model(model, WEIGHT_FILE, MODEL_FILE)
        except OSError as exc:
            print("[CLUSTERING] Could not save model:", str(exc))
    return model


###############################################################################
###############################################################################

MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model")
ENABLE_CUTOFF = False
GLOBAL_MODEL = get_model()
GLOBAL_GRAPH = tf.get_default_graph()



###############################################################################
######################## 	FEATURES HANDLING 			#######################
###############################################################################

def get_features(model, image_path):

    """
    :param model: the model used to extract features
    :param image_path: the path of the image to extract features from
    :return: a numpy array of features
    """

    img = image.load_img(image_path, target_size=(224, 224))
    img_data = image.img_to_array(img)
    img_data = np.expand_dims(img_data, axis=0)
    # img_data = preprocess_input(img_data)

    # version 1 for VGG16, version 2 for RESNET50 or SENET50
    img_data = utils.preprocess_input(img_data, version=2)

    with GLOBAL_GRAPH.as_default():
        feature = model.predict(img_data)
    feature_np = np.array(feature).flatten()
    return feature_np


def compute_features(model, faces):
    # images = [os.path.join(MEDIA_ROOT, str(face.face)) for face in faces]
    print("[CLUSTERING] Extracting features of", len(faces), "face images...")
    feature_list = []
    for face in faces:

        try:
            image_features = Features.objects.get(face=face).get_feature_list()
            feature_list.append(image_features)
        except ObjectDoesNotExist:
            image_path = os.path.join(MEDIA_ROOT, str(face.face))
            image_features = get_features(model, image_path)
            feature_list.append(image_features)
            new_features = Features.objects.create(face=face, feature=image_features.tolist())
            new_features.save()
    feature_list_np = np.array(feature_list)
    return feature_list_np


###############################################################################
######################## 	CLUSTERS HANDLING 			#######################
###############################################################################


def get_clusters(model, features, n_clusters):

    """
    :param images: a list of image paths
    :return: a list of clusters
    """

    # K.clear_session()
    # model = get_model()
    """
    print("[CLUSTERING] Extracting features of", len(images), "images...")
    feature_list = []
    for image_path in images:
        image_features = get_features(model, image_path)
        feature_list.append(image_features)
    feature_list_np = np.array(feature_list)
    """

    # print("[CLUSTERING] Clustering with", n_clusters, "clusters...")
    clustering_algorithm = AgglomerativeClustering(n_clusters=n_clusters, linkage='ward')
    # clustering_algorithm = KMeans(n_clusters=n_clusters, n_jobs=-1)
    clusters = clustering_algorithm.fit_predict(features)
    n_labels = len(set(clusters))

    # print("[CLUSTERING] Clusters for n =", n_clusters, ":", clusters)
    # print("[CLUSTERING] n_labels =", n_labels)

    if n_labels >= 2 and n_labels <= len(features) - 1:
        silhouette_avg = silhouette_score(features, clusters)
    else:
        silhouette_avg = 0
    if np.isnan(silhouette_avg):
        silhouette_avg = 0

    # print("[CLUSTERING] Silhouette score =", silhouette_avg)
    # print()

    return clusters, n_clusters, silhouette_avg


def compute_clusters(model, features, n_clusters):
    if len(features) > 1:
        clusters, n_clusters, silhouette_avg = \
                get_clusters(model, features, n_clusters)
    # Assign default cluster
    else:
        clusters = [0]
        n_clusters = 1
        silhouette_avg = 1
    return clusters, n_clusters, silhouette_avg


def get_new_clusters(cluster_list, faces, clusters, n_clusters, changes, silhouette_avg):

    user = faces[0].user
    old_clusters = list(FaceCluster.objects.filter(n_clusters=n_clusters, user=user))
    if not changes:
        cluster_list += old_clusters
        return cluster_list
    else:
        # print("[CLUSTERING] Rebuilding clusters...")
        delete_cluster_group(n_clusters, user)

        # print("[CLUSTERING] Old clusters:", old_clusters)
        for (cluster, face) in list(zip(clusters, faces)):
            # TODO: Improve old_name getting
            # Idea: look for an existing face, and then the name of the
            # cluster which that face belongs
            cluster_name = "Cluster " + str(cluster)
            for old_cluster in old_clusters:

                if old_cluster.face_id == face.id:
                    cluster_name = old_cluster.name
                break

            face_cluster = FaceCluster(n_clusters=n_clusters,
                                        cluster_id=cluster,
                                        user=face.user,
                                        face=face,
                                        name=cluster_name,
                                        silhouette_score=silhouette_avg)

            cluster_list.append(face_cluster)

    return cluster_list


def build_clusters(faces, clusters, n_clusters, changes, silhouette_avg):
    """
    If no changes to the clusters were made, return the existing clusters.
    Else, delete the old cluster group and rebuild it
    """

    user = faces[0].user
    old_clusters = list(FaceCluster.objects.filter(n_clusters=n_clusters, user=user))
    if not changes:
        return old_clusters
    else:
        # print("[CLUSTERING] Rebuilding clusters...")
        new_clusters = []
        delete_cluster_group(n_clusters, user)

        # print("[CLUSTERING] Old clusters:", old_clusters)
        for (cluster, face) in list(zip(clusters, faces)):
            # TODO: Improve old_name getting
            # Idea: look for an existing face, and then the name of the
            # cluster which that face belongs
            cluster_name = "Cluster " + str(cluster)
            for old_cluster in old_clusters:

                if old_cluster.face_id == face.id:
                    cluster_name = old_cluster.name
                break

            face_cluster = FaceCluster.objects.create(n_clusters=n_clusters,
                                        cluster_id=cluster,
                                        user=face.user,
                                        face=face,
                                        name=cluster_name,
                                        silhouette_score=silhouette_avg)
            new_clusters.append(face_cluster)
        return new_clusters


def delete_cluster_group(n_clusters, user):
    # print("[CLUSTERING] Deleting cluster group", n_clusters, "from user", user)
    FaceCluster.objects.filter(n_clusters=n_clusters, user=user).delete()


###############################################################################
######################## 			MAIN LOOP 			#######################
###############################################################################

def get_all_cluster_groups(faces, min_n_cluster, max_n_cluster):

    all_cluster_groups = []
    # K.clear_session()
    model = None
    features = None


    # Fundamento: os maiores valores estão na vizinhança do número
    #   correcto de clusters

    # Ideia: ir modificando a ordem de tentativas
    # Primeiramente, testam-se os limites dos clusters (1º, ultimo e meio)
    # Escolher aquele que tem o maior score, e comecar a descer/subir o
    #   numero de clusters a partir dai

    # Parar quando, ao subir, o score comecar a descer


    # Mudar aqui a primeira ordem de tentativas
    ratio = -0.25
    minimum_clusters = 25
    balance_threshold = round(ratio*len(faces) - minimum_clusters)
    offset = round(len(faces) / 4)
    print("[CLUSTERING] Offset is " + ConsoleColors.OKBLUE + str(offset) + ConsoleColors.ENDC)
    print("[CLUSTERING] Balance threshold is " + ConsoleColors.OKBLUE + str(balance_threshold) + ConsoleColors.ENDC)


    middle_n_cluster = round(len(faces)/ 2)
    min_n_cluster = middle_n_cluster - offset
    max_n_cluster = middle_n_cluster + offset

    cluster_try_order = [min_n_cluster, max_n_cluster]
    if middle_n_cluster not in cluster_try_order:
        cluster_try_order.append(middle_n_cluster)


    higher_n = 0
    higher_score = 0
    balance = 0

    deleted = False
    from_middle = False
    cluster_list = []
    reference_cluster_group = False

    cluster_try_order = list(set([c for c in cluster_try_order if c >= 0]))
    cluster_try_order.sort()
    last_n_cluster = cluster_try_order[-1]
    tried = []

    for n_clusters in cluster_try_order:

        # Se este cluster group ja foi computado, passar ao proximo
        if n_clusters in tried or n_clusters <= 0:
            continue
        else:
            tried.append(n_clusters)

        print("[CLUSTERING] Checking cluster group:", end=" ")
        # for c in cluster_try_order:
        #     if c == n_clusters:
        #         print(ConsoleColors.OKGREEN + ">" + str(c) + "<" + ConsoleColors.ENDC, end=" ")
        #
        #     elif c == min_n_cluster or c == max_n_cluster:
        #         print(ConsoleColors.WARNING + str(c) + ConsoleColors.ENDC, end=" ")
        #     else:
        #         print(c, end=" ")

        idx = cluster_try_order.index(n_clusters)
        show_number = 5

        if idx > show_number:
            print("...", end=" ")
        for c in cluster_try_order[max(0,idx-show_number):idx]:
            print(c, end=" ")
        print(ConsoleColors.OKGREEN + ">" + str(n_clusters) + "<" + ConsoleColors.ENDC, end=" ")
        for c in cluster_try_order[idx+1:idx+show_number+1]:
            print(c, end=" ")
        if idx + show_number < len(cluster_try_order):
            print("...", end=" ")

        existing_clusters = FaceCluster.objects.filter(face__in=faces,
                                                        n_clusters=n_clusters)

        changes = False

        if len(existing_clusters) > 0 and not changes:
            print("Found previously computed clusters ...", end=" ")

            silhouette_avg = existing_clusters[0].silhouette_score
            clusters = []

            for face in faces:

                face_clusters = \
                    FaceCluster.objects.filter(face=face, n_clusters=n_clusters)

                # If there is a face with no assigned cluster
                if len(face_clusters) == 0:
                    print("Found new face:", face.face)
                    print("[CLUSTERING] Recomputing clusters...")

                    if model is None:
                        model = get_model()
                    if features is None:
                        features = compute_features(model, faces)

                    clusters, n_clusters, silhouette_avg = \
                            compute_clusters(model, features, n_clusters)
                    changes = True

                    break
                else:
                    cluster_id = face_clusters.order_by('-pk')[0].cluster_id
                    clusters.append(cluster_id)
        else:
            if model is None:
                model = get_model()
            if features is None:
                features = compute_features(model, faces)

            clusters, n_clusters, silhouette_avg = \
                            compute_clusters(model, features, n_clusters)
            changes = True

        print("(" + str(silhouette_avg) + ")", end=" ")

        if changes and not deleted:
            FaceCluster.objects.filter(user=faces[0].user).delete()
            deleted = True


        cluster_list = get_new_clusters(cluster_list, faces, clusters, n_clusters, changes, silhouette_avg)
        if len(faces) == 1:
            break


        #######################################################################
        # Reached the end of the current trying list
        #   Now to find the direction
        #######################################################################

        neighbours = []
        # if changes and from_middle and n_clusters == last_n_cluster:
        if reference_cluster_group and changes and n_clusters == last_n_cluster:

            # if higher_n > middle_n_cluster:
            if higher_n > reference_cluster_group:
                # neighbours = list(range(last_n_cluster + 2, max_n_cluster - 1))
                neighbours = [c for c in list(range(higher_n + 1, len(faces)+1)) if c not in tried]
                direction = 'higher'
            else:
                # neighbours = list(range(middle_n_cluster - 2, min_n_cluster, -1))
                neighbours = [c for c in list(range(higher_n - 1, 0, -1)) if c not in tried]
                direction = 'lower'
            cluster_try_order += neighbours

            balance = 0
            print("\n[CLUSTERING] Local maxima is likely " + \
                ConsoleColors.OKBLUE + direction + ConsoleColors.ENDC,
                    "than the reference cluster group " + \
                ConsoleColors.OKBLUE + str(reference_cluster_group) + ConsoleColors.ENDC)
            print("[CLUSTERING] Added neighbours:", neighbours, '\n')

        else:


            # Se foi achado um grupo melhor, guarda esse novo grupo
            if silhouette_avg > higher_score:
                higher_n = n_clusters
                higher_score = silhouette_avg
                balance += 1
                print(ConsoleColors.OKGREEN + str(balance) + ConsoleColors.ENDC)

            # Se o score desceu em relacao ao melhor
            else:
                # If the score is starting to drop and it was rising before
                #    i.e. this is a local maxima, stop
                balance -= 1
                print(ConsoleColors.FAIL + str(balance) + ConsoleColors.ENDC)

                # Se houve subida suficiente e agora esta a descer, parar o loop
                if balance <= balance_threshold and ENABLE_CUTOFF:
                    print("\n[CLUSTERING] Stopped clustering after finding the "
                        "local maxima cluster group: " + ConsoleColors.OKGREEN + \
                        str(higher_n) + ConsoleColors.ENDC + " with a score of " +\
                        ConsoleColors.OKGREEN + str(higher_score) + ConsoleColors.ENDC)
                    break



        #######################################################################
        # Only executed in the beggining, i.e to see which point begins
        #######################################################################

        # last element of the initial try-vector
        # i.e if the three 'extremities' were checked

        initial_neighbours = []
        # if changes and n_clusters == last_n_cluster and not from_middle:
        if changes and n_clusters == last_n_cluster and not reference_cluster_group:
            if higher_n == max_n_cluster - 1:
                # initial_neighbours = list(range(higher_n - 1, min_n_cluster + 1, -1))
                initial_neighbours = list((higher_n - 1, higher_n + 1))
                last_n_cluster = initial_neighbours[-1] # to remove
                end = 'last'
            elif higher_n == min_n_cluster:
                # initial_neighbours = list(range(min_n_cluster + 1, max_n_cluster - 1))
                initial_neighbours = list((higher_n - 1, higher_n + 1))
                last_n_cluster = initial_neighbours[-1] # to remove
                end = 'first'
            else:
                # from_middle = True
                initial_neighbours = list((higher_n - 1, higher_n + 1))
                last_n_cluster = initial_neighbours[-1]
                end = 'middle'

            reference_cluster_group = higher_n
            balance = 0
            cluster_try_order += initial_neighbours
            print("\n[CLUSTERING] Best place to start clustering from: " + \
                ConsoleColors.OKGREEN + str(end) + ConsoleColors.ENDC)
            print("[CLUSTERING] Added initial neighbours:", initial_neighbours, '\n')

        #######################################################################


    #######################################################################
    # Adding the extremities
    # Only done at the end, when all "necessary" clusters have been computed
    #######################################################################

    if changes:
        extremities = [1, len(faces)]
        for e in extremities:
            if e not in tried:
                clusters, n_clusters, silhouette_avg = compute_clusters(model, features, e)
                cluster_list = get_new_clusters(cluster_list, faces, clusters, n_clusters, changes, silhouette_avg)
    #     FaceCluster.objects.bulk_create(cluster_list)
    all_cluster_groups = cluster_list

    return all_cluster_groups, changes
