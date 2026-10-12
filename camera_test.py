import cv2

for camera_index in range(5):

    camera = cv2.VideoCapture(camera_index)

    if camera.isOpened():
        print(f"✅ Camera index {camera_index} available")

        ret, frame = camera.read()

        if ret:
            cv2.imshow(f"Camera {camera_index}", frame)
            print(f"📷 Camera {camera_index} working")

            cv2.waitKey(2000)
            cv2.destroyAllWindows()

    camera.release()

print("Camera test complete.")