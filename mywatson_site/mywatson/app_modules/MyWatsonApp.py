import os
from . import AutomaticTagger, RetrieveAndRanker, Expansion, Learning
from mywatson_site.settings import MEDIA_ROOT
from mywatson.models import Face, FaceCluster
from mywatson.vars import FACE_IMAGES_FOLDER, DEFAULT_N_CLUSTERS


def tag_image(path):
    print("[MYWATSON] Tagging image", path)

    """
      Example of a tag:

      mid: /m/0838
      description: "water"
      score: 0.9120154976844788
      topicality: 0.9120154976844788
      """

    # tags = []

    # tags = AutomaticTagger.tag_image(path)
    tags = AutomaticTagger.get_image_info(path)

    # for info in infos:
    #    tags.append(tuple((info['description'], info['score'])))

    return tags


def batch_tag(paths, user):
    print("[MYWATSON] Executing batch tagging on", len(paths), "photos")
    """
    Input: list of paths
    Returns: dictionary of tags for each path

        Example:
            description: "water"
            score: 0.9120154976844788
    """

    tags = AutomaticTagger.batch_tag(paths, user)
    return tags


def get_results(query, user):

    """

    :param query: a string containing the user query
    :return:  list of the results for the query
    """

    if query:
        query = query.lower()
        query_terms = query.split()

        query_terms = Expansion.expand_query(query_terms, user)
        results = RetrieveAndRanker.get_results	(query_terms, user)

        return results

    else:
        return []


def get_all_cluster_groups(faces, min_n_cluster, max_n_cluster):
    return Learning.get_all_cluster_groups(faces, min_n_cluster, max_n_cluster)


def get_clusters(faces, n_clusters=DEFAULT_N_CLUSTERS):

    # TODO: Remove this Function

    """
    :param images: a list of django face objects
    :return: a list of facecluster objects
    """

    existing_clusters = FaceCluster.objects.filter(face__in=faces,
                                                    n_clusters=n_clusters)

    changes = False

    print("[CLUSTERING] Getting", n_clusters, "clusters")
    if len(existing_clusters) > 0:
        silhouette_avg = existing_clusters[0].silhouette_score
        print("[CLUSTERING] Found previously computed clusters")
        clusters = []
        for face in faces:

            # TODO: Compute multiple cluster groups for differente k's,
            # depending on the silhouette score and add the "K" and
            # "silhouette_score" fields to the table FaceCluster

            face_clusters = \
                FaceCluster.objects.filter(face=face, n_clusters=n_clusters)

            # If there is a face with no assigned cluster
            if len(face_clusters) == 0:
                print("[CLUSTERING] Found new face:", face.face)
                print("[CLUSTERING] Recomputing clusters...")
                clusters, n_clusters, silhouette_avg = \
                                Learning.compute_clusters(faces, n_clusters)
                changes = True
                break
            else:
                cluster_id = face_clusters.order_by('-pk')[0].cluster_id
                clusters.append(cluster_id)
    else:
        clusters, n_clusters, silhouette_avg = \
                                Learning.compute_clusters(faces, n_clusters)
        changes = True

    clusters = list(Learning.build_clusters(faces, clusters,
                                            n_clusters, changes, silhouette_avg))

    return clusters


def get_faces(photos):
    """
    photos: list of photo objects

    returns: a list of faces from the input photos
    """
    return Face.objects.select_related().filter(photo__in=photos)
