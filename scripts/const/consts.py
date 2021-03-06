import os

SCRIPT_ROOT_DIR = os.getcwd()

ROOT_DIR = os.path.dirname(SCRIPT_ROOT_DIR)

IMAGE_DIR = os.path.join(ROOT_DIR, 'images')

ANTI_SPOOFING_MODELS_DIR = os.path.join(ROOT_DIR, "models", "anti_spoof_models")

DATA_DIR = os.path.join(ROOT_DIR, "data")

FACE_DETECTION_CAFFE_MODEL = os.path.join(ROOT_DIR, "models", "face_detection_model", "Widerface-RetinaFace.caffemodel")

FACE_DETECTION_CAFFE_WEIGHTS = os.path.join(ROOT_DIR, "models", "face_detection_model", "deploy.prototxt")

FACE_DISTANCE_THRESHOLD = 0.5

UNKNOWN = "unknow"

SKIP_FRAMES = 5

PICKEL_FILE_NAME = "face_encodings.pkl"

FACE_ID_NO_PEOPLE_EXIST = -1

FACE_ID_MORE_THAN_ONE_PEOPLE = -2

FACE_ID_ENCODING_SUCESS = 0