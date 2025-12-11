import cv2

# Open the default webcam (0)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    raise IOError("Cannot open webcam")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # ---- Your image processing pipeline goes HERE ----
    # Example (convert to grayscale):
    processed = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    #----------------------------------------------------
    # Display live feed and processed frame
    cv2.imshow("Live Video", frame)
    cv2.imshow("Processed Frame", processed)

    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
