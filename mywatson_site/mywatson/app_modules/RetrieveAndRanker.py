from nltk.stem.porter import PorterStemmer
from nltk.stem import WordNetLemmatizer
from mywatson.models import Photo, Tag
import re
import math
from sklearn.metrics.pairwise import cosine_similarity
import operator
from pprint import pprint
import numpy as np



stemmer = PorterStemmer()
lemmatizer = WordNetLemmatizer()


def pre_process_query(query_terms):
    """
    :param query_terms: list of query terms
    :return: list of processed query terms
    """

    processed = [stemmer.stem(term) for term in query_terms]
    processed += [lemmatizer.lemmatize(term) for term in query_terms]

    return processed


def get_results(query_terms, user):

    original_query = query_terms
    query_terms = original_query + pre_process_query(query_terms)
    query_terms = set(query_terms)
    print("[RETRIEVE & RANKER] Query terms:", query_terms)
    query_vec = []
    for term in query_terms:
        if term in original_query:
            query_vec.append(1)
        else:
            query_vec.append(0.7)
    # print("[RETRIEVE & RANKER] Query vector:", query_vec)

    tags = Tag.objects.filter(photo__user=user)
    bow = {}
    for tag in tags:
        photo = tag.photo_id
        if photo not in bow:
            bow[photo] = set()
        # weight = min(tag.score, Decimal(1))
        terms = set(tag.tag.lower().split(' '))
        bow[photo].update(terms)

    N = len(bow)
    idf = {}
    appearances = {}
    for _, terms in bow.items():
        for term in terms:
            if term not in idf:
                appearances[term] = 0
            appearances[term] += 1
            # idf[term] = math.log(N/appearances[term])

            # Using smoothing
            idf[term] = math.log(1 + N/appearances[term])

    # print("[RETRIEVE & RANKER] Appearances:", appearances)
    # print("[RETRIEVE & RANKER] idf:", idf)
    # print("[RETRIEVE & RANKER] BoW:", bow)
    bow_vectors = {}
    for photo in bow:
        vec = []
        for term in query_terms:
            if term in bow[photo]:
                # print("[RETRIEVE & RANKER] Term", term, "in BoW")
                vec.append(idf[term] if term in idf else 0)
            else:
                vec.append(0)
        # print("[RETRIEVE & RANKER] Vector for photo", photo, "is", vec)

        # full zero vectors are not appended
        if not all(v == 0 for v in vec):
            bow_vectors[photo] = vec
    # print("[RETRIVE & RANKER] BoW Vectors:", bow_vectors)
    similarities = {}
    for photo, vec in bow_vectors.items():
        similarities[photo] = cosine_similarity(np.array(query_vec).reshape(1, -1),
                                                np.array(vec).reshape(1, -1))[0][0]

    # print("[RETRIEVE & RANKER] Similarities:")
    # pprint(similarities)
    # print()

    sorted_results = [s[0] for s in sorted(similarities.items(), key=operator.itemgetter(1), reverse=True)]

    # print("[RETRIEVE & RANKER] Sorted results:")
    # pprint(sorted_results)
    # print()

    results = list(Photo.objects.filter(id__in=sorted_results, user=user))

    # Results do not come ordered from DB...
    results = [Photo.objects.get(id=photo_id)
                for photo_id in sorted_results]

    # print("[RETRIEVE & RANKER] Results with improved function:",
    #     [photo.id for photo in results])

    return results
