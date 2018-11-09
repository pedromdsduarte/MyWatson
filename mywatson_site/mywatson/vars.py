import os
from mywatson_site.settings import BASE_DIR, MEDIA_ROOT, MEDIA_URL

CROPPED_IMAGES_FOLDER = os.path.join(BASE_DIR, 'public', 'cropped')
FACE_IMAGES_FOLDER = os.path.join(MEDIA_ROOT, 'faces')

TAG_MAX_SIZE = 97
IMG_MAX_SIZE_BYTES = 10000000

DEFAULT_N_CLUSTERS = 2


class ConsoleColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
