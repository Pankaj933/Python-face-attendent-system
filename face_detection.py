import os
import cv2

model_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "face_detection_yunet_2026may.onnx"
)

if not os.path.exists(model_path):
    print("❌ YuNet model file nahi mili:")
    print(model_path)
    exit()

print("✅ Model mil gaya:")
print(model_path)

camera = cv2.VideoCapture(1)

if not camera.isOpened():
    print("❌ Camera open nahi ho raha.")
    exit()

detector = cv2.FaceDetectorYN.create(
    model_path,
    "",
    (320, 320),
    0.9,
    0.3,
    5000
)

print("✅ Face Detection Start")
print("Q press karke camera band karo.")

while True:

    ret, frame = camera.read()

    if not ret:
        print("❌ Camera se frame nahi mil raha.")
        break

    height, width = frame.shape[:2]

    detector.setInputSize((width, height))

    _, faces = detector.detect(frame)

    if faces is not None:

        for face in faces:

            x, y, w, h = face[:4].astype(int)

            cv2.rectangle(
                frame,
                (x, y),
                (x + w, y + h),
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame,
                "Face Detected",
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

    cv2.imshow(
        "Automated Attendance - Face Detection",
        frame
    )

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()