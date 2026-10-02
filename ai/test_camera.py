"""
Test Camera Stream - Verifies OpenCV can read from the IP camera URL
"""
import cv2
import time

# Hardcode the URL for testing to avoid path issues
CAMERA_STREAM_URL = "http://192.168.8.151:4444/video"

def test_camera():
    print(f"[CAMERA TEST] Connecting to: {CAMERA_STREAM_URL}")
    print("[CAMERA TEST] Please wait... (It might take 5-10 seconds)")
    
    # OpenCV VideoCapture
    cap = cv2.VideoCapture(CAMERA_STREAM_URL)
    
    # Check if camera opened successfully
    if not cap.isOpened():
        print("[CAMERA TEST] ✗ FAILED: Could not open camera stream.")
        print("[CAMERA TEST] 💡 Tip: Make sure the Android IP Camera app is running and phone is on the same WiFi.")
        return
    
    print("[CAMERA TEST] ✓ SUCCESS: Camera stream opened!")
    print("[CAMERA TEST] A window will open. Press 'q' on your keyboard to quit.")
    
    # Continuously read and show frames
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if ret:
            frame_count += 1
            # Show the frame in a window
            cv2.imshow("DEM3T3R V1 Live Camera", frame)
            
            # Print status every 30 frames so we know it's working
            if frame_count % 30 == 0:
                print(f"[CAMERA TEST] Successfully captured {frame_count} frames...")
            
            # Press 'q' to quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        else:
            print("[CAMERA TEST] ⚠ WARNING: Failed to read frame")
            break
            
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    print(f"[CAMERA TEST] Test completed. Total frames captured: {frame_count}")

if __name__ == "__main__":
    test_camera()