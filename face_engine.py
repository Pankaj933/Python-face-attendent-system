import os
import cv2
import numpy as np


BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


YUNET_MODEL = os.path.join(
    BASE_DIR,
    "face_detection_yunet_2026may.onnx"
)


SFACE_MODEL = os.path.join(
    BASE_DIR,
    "face_recognition_sface_2021dec.onnx"
)


# ==========================================
# LOAD MODELS
# ==========================================

detector = cv2.FaceDetectorYN.create(
    YUNET_MODEL,
    "",
    (320, 320),
    0.9,
    0.3,
    5000
)


recognizer = cv2.FaceRecognizerSF.create(
    SFACE_MODEL,
    ""
)


# ==========================================
# DETECT FACE
# ==========================================

def detect_face(image):

    height, width = image.shape[:2]

    detector.setInputSize(
        (width, height)
    )

    _, faces = detector.detect(image)

    if faces is None:
        return None

    if len(faces) == 0:
        return None

    if len(faces) > 1:
        raise ValueError(
            "Ek image mein ek hi face hona chahiye."
        )

    return faces[0]


# ==========================================
# CREATE FACE EMBEDDING
# ==========================================

def create_embedding(image):

    face = detect_face(image)

    if face is None:
        return None

    aligned_face = recognizer.alignCrop(
        image,
        face
    )

    feature = recognizer.feature(
        aligned_face
    )

    return feature.astype(
        np.float32
    )


# ==========================================
# COMPARE TWO FACES
# ==========================================

def compare_faces(
    embedding1,
    embedding2
):

    score = recognizer.match(
        embedding1,
        embedding2,
        cv2.FaceRecognizerSF_FR_COSINE
    )

    return float(score)