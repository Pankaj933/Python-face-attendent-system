import cv2
import os
import time

# ==============================
# SETTINGS
# ==============================

CAMERA_INDEX = 1
DATASET_DIR = "dataset"
TOTAL_IMAGES = 30

# ==============================
# USER DETAILS
# ==============================

person_id = input("Enter Person ID: ").strip()
person_name = input("Enter Person Name: ").strip()

if not person_id or not person_name:
    print("❌ ID aur Name dono required hain.")
    exit()

# Folder name
person_folder = os.path.join(
    DATASET_DIR,
    person_id
)

os.makedirs(person_folder, exist_ok=True)

# ==============================
# CAMERA
# ==============================

camera = cv2.VideoCapture(CAMERA_INDEX)

if not camera.isOpened():
    print("❌ DroidCam open nahi ho raha.")
    exit()

# ==============================
# FACE DETECTOR - YUNET
# ==============================

model_path = "face_detection_yunet_2026may.onnx"

if not os.path.exists(model_path):
    print("❌ YuNet model file nahi mili:")
    print(model_path)
    camera.release()
    exit()

detector = cv2.FaceDetectorYN.create(
    model_path,
    "",
    (320, 320),
    0.6,
    0.3,
    5000
)

print()
print("===================================")
print("       FACE REGISTRATION")
print("===================================")
print(f"ID   : {person_id}")
print(f"Name : {person_name}")
print()
print("Camera ke saamne face rakho.")
print("Images automatically capture hongi.")
print("Q press karke cancel kar sakte ho.")
print("===================================")

image_count = 0
last_capture_time = 0

while True:

    ret, frame = camera.read()

    if not ret:
        print("❌ Camera se frame nahi mil raha.")
        break

    height, width = frame.shape[:2]

    detector.setInputSize((width, height))

    _, faces = detector.detect(frame)

    # Face detected
    if faces is not None and len(faces) > 0:

        # Sabse bada face select karo
        face = max(
            faces,
            key=lambda f: f[2] * f[3]
        )

        x, y, w, h = face[:4].astype(int)

        # Face box
        cv2.rectangle(
            frame,
            (x, y),
            (x + w, y + h),
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            f"Face Detected - {image_count}/{TOTAL_IMAGES}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

        # Capture every 0.25 second
        current_time = time.time()

        if (
            current_time - last_capture_time >= 0.25
            and image_count < TOTAL_IMAGES
        ):

            # Face crop
            face_crop = frame[
                max(0, y):min(height, y + h),
                max(0, x):min(width, x + w)
            ]

            if face_crop.size > 0:

                image_count += 1

                filename = os.path.join(
                    person_folder,
                    f"{image_count}.jpg"
                )

                cv2.imwrite(
                    filename,
                    face_crop
                )

                print(
                    f"✅ Image {image_count}/{TOTAL_IMAGES} saved"
                )

                last_capture_time = current_time

    else:

        cv2.putText(
            frame,
            "Face camera ke saamne lao",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )

    cv2.imshow(
        "Automated Attendance - Face Registration",
        frame
    )

    # Q = cancel
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

    # Registration complete
    if image_count >= TOTAL_IMAGES:
        print()
        print("===================================")
        print("✅ FACE REGISTRATION COMPLETE")
        print(f"Total Images: {image_count}")
        print(f"Saved In: {person_folder}")
        print("===================================")

        time.sleep(2)
        break


camera.release()
cv2.destroyAllWindows()