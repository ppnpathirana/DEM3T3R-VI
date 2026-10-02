"""
DEM3T3R V1 Backend Server - TCP + WebSocket + Dual High-Performance Video Streams
Supports:
  1. USB Cam (Rover Onboard ESP32-S3 USB UVC Camera / Local USB)
  2. Wi-Fi Cam (Field IP Camera / Smartphone Wi-Fi Webcam / RTSP)
"""
import socket
import json
import threading
import requests
import urllib3
import time
import os
import cv2
import numpy as np
from flask import Flask, Response, send_from_directory, jsonify, request
from flask_socketio import SocketIO, emit

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__, static_folder='dist', static_url_path='')
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuration & Camera Endpoints
esp32_ip = "192.168.8.151"
USB_CAM_URL = f"http://{esp32_ip}/stream"
WIFI_CAM_URL = "https://192.168.8.151:4444/video"
ACTIVE_CAM = "usb"  # "usb" | "wifi"

telemetry_data = {}
camera_lock = threading.Lock()

def create_placeholder_frame(cam_label="USB CAM", url="", status_text="Connecting to Camera..."):
    """Generate a clean dark cybernetic HUD placeholder frame when camera is connecting"""
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    # Background gradient styling
    img[:] = (18, 22, 28)
    
    # Grid lines
    for y in range(0, 480, 40):
        cv2.line(img, (0, y), (640, y), (28, 34, 44), 1)
    for x in range(0, 640, 40):
        cv2.line(img, (0, x), (640, x), (28, 34, 44), 1)
        
    # Crosshair HUD
    accent_color = (0, 255, 136) if "USB" in cam_label else (224, 64, 160)
    cv2.drawMarker(img, (320, 240), accent_color, cv2.MARKER_CROSS, 40, 1)
    cv2.circle(img, (320, 240), 60, accent_color, 1)
    
    # Header & Text
    cv2.putText(img, f"DEM3T3R V1 ROVER HUD - {cam_label.upper()}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.65, accent_color, 2)
    cv2.putText(img, f"UPLINK: {url}", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 180, 180), 1)
    cv2.putText(img, status_text, (180, 245), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
    
    # Timestamp
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    cv2.putText(img, ts, (440, 460), cv2.FONT_HERSHEY_SIMPLEX, 0.45, accent_color, 1)
    
    _, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 70])
    return buffer.tobytes()

# --- Generic MJPEG Generator for a specific camera source ---
def generate_camera_stream(source_type="usb"):
    """Generate MJPEG stream for either 'usb' or 'wifi' camera"""
    global USB_CAM_URL, WIFI_CAM_URL, esp32_ip
    
    while True:
        target_url = USB_CAM_URL if source_type == "usb" else WIFI_CAM_URL
        cam_title = "Rover USB Cam" if source_type == "usb" else "Field Wi-Fi Cam"
        
        try:
            with requests.get(target_url, stream=True, verify=False, timeout=3.5) as response:
                if response.status_code == 200:
                    bytes_data = bytes()
                    for chunk in response.iter_content(chunk_size=2048):
                        bytes_data += chunk
                        a = bytes_data.find(b'\xff\xd8')
                        b = bytes_data.find(b'\xff\xd9')
                        
                        if a != -1 and b != -1:
                            jpg = bytes_data[a:b+2]
                            bytes_data = bytes_data[b+2:]
                            yield (b'--frame\r\n'
                                   b'Content-Type: image/jpeg\r\n\r\n' + jpg + b'\r\n')
        except Exception:
            # If USB Cam network stream fails, attempt local OpenCV USB camera on PC
            if source_type == "usb":
                try:
                    cap = cv2.VideoCapture(0)
                    if cap.isOpened():
                        ret, frame = cap.read()
                        cap.release()
                        if ret:
                            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                            yield (b'--frame\r\n'
                                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                            time.sleep(0.04)
                            continue
                except Exception:
                    pass
            
            # Yield HUD placeholder
            placeholder = create_placeholder_frame(
                cam_label=cam_title, 
                url=target_url, 
                status_text=f"Waiting for {cam_title} Uplink..."
            )
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + placeholder + b'\r\n')
            time.sleep(0.5)

@app.route('/video_feed')
def video_feed():
    """Live video feed with query param ?cam=usb or ?cam=wifi (default: ACTIVE_CAM)"""
    cam = request.args.get('cam', ACTIVE_CAM).lower()
    if cam not in ['usb', 'wifi']:
        cam = ACTIVE_CAM
    return Response(generate_camera_stream(cam), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed/usb')
def video_feed_usb():
    """Direct route for USB Camera Stream"""
    return Response(generate_camera_stream('usb'), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed/wifi')
def video_feed_wifi():
    """Direct route for Wi-Fi IP Camera Stream"""
    return Response(generate_camera_stream('wifi'), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/camera_config', methods=['GET', 'POST'])
def camera_config():
    """Get or update dual camera configuration"""
    global USB_CAM_URL, WIFI_CAM_URL, ACTIVE_CAM, esp32_ip
    if request.method == 'POST':
        data = request.get_json() or {}
        with camera_lock:
            if 'usb_url' in data:
                USB_CAM_URL = data['usb_url']
            if 'wifi_url' in data:
                WIFI_CAM_URL = data['wifi_url']
            if 'active_cam' in data and data['active_cam'] in ['usb', 'wifi']:
                ACTIVE_CAM = data['active_cam']
        return jsonify({
            'status': 'ok',
            'usb_url': USB_CAM_URL,
            'wifi_url': WIFI_CAM_URL,
            'active_cam': ACTIVE_CAM
        })
        
    return jsonify({
        'usb_url': USB_CAM_URL,
        'wifi_url': WIFI_CAM_URL,
        'active_cam': ACTIVE_CAM,
        'esp32_ip': esp32_ip
    })

# --- Dashboard Routes ---
@app.route('/')
def index():
    return send_from_directory('dashboard', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('dashboard', path)

# --- WebSocket Events ---
@socketio.on('connect')
def handle_connect():
    print("[WS] ✅ Dashboard connected")
    emit('connection_status', {'status': 'connected', 'message': 'Connected to DEM3T3R V1 Dual-Cam Backend'})
    if telemetry_data:
        emit('sensor_data', telemetry_data)

@socketio.on('disconnect')
def handle_disconnect():
    print("[WS] ❌ Dashboard disconnected")

@socketio.on('set_camera')
def handle_set_camera(data):
    """Switch active camera via WebSocket"""
    global ACTIVE_CAM
    cam = (data.get('camera') or '').lower()
    if cam in ['usb', 'wifi']:
        with camera_lock:
            ACTIVE_CAM = cam
        print(f"[CAMERA] 📷 Active Camera switched to: {ACTIVE_CAM.upper()}")
        emit('camera_changed', {'active_cam': ACTIVE_CAM}, broadcast=True)

# --- TCP Server for ESP32 ---
def run_tcp_server():
    """Listen for ESP32 telemetry data & auto-discover camera IP"""
    global esp32_ip, USB_CAM_URL
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('0.0.0.0', 5000))
    sock.listen(2)
    print("[TCP] ✓ Server listening on port 5000")
    
    while True:
        try:
            client, addr = sock.accept()
            print(f"[TCP] ✓ ESP32 connected from {addr}")
            
            with camera_lock:
                esp32_ip = addr[0]
                USB_CAM_URL = f"http://{esp32_ip}/stream"
                print(f"[CAMERA] 📷 Auto-configured USB Cam Stream: {USB_CAM_URL}")
                
            threading.Thread(target=handle_esp32_client, args=(client,), daemon=True).start()
        except Exception as e:
            print(f"[TCP] Error: {e}")

def handle_esp32_client(client):
    """Handle incoming ESP32 data"""
    global telemetry_data
    buffer = ""
    while True:
        try:
            data = client.recv(1024).decode('utf-8')
            if not data:
                break
            
            buffer += data
            
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                if line.strip():
                    try:
                        msg = json.loads(line.strip())
                        msg_type = msg.get('type')
                        if msg_type == 'telemetry':
                            telemetry_data = msg
                            socketio.emit('sensor_data', msg)
                        elif msg_type in ['hello', 'handshake']:
                            ip = msg.get('ip')
                            if ip:
                                global esp32_ip, USB_CAM_URL
                                with camera_lock:
                                    esp32_ip = ip
                                    USB_CAM_URL = f"http://{ip}/stream"
                            print(f"[TCP] ESP32 hello: device={msg.get('device')} IP={ip} USB_Stream={USB_CAM_URL}")
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            print(f"[TCP] Client error: {e}")
            break
    
    client.close()
    print("[TCP] ESP32 disconnected")

# --- Main ---
if __name__ == '__main__':
    tcp_thread = threading.Thread(target=run_tcp_server, daemon=True)
    tcp_thread.start()
    
    print("=" * 60)
    print("🌾 DEM3T3R V1 Dual-Camera Backend Server Online")
    print("=" * 60)
    print("Dashboard:        http://localhost:5001")
    print("USB Cam Stream:   http://localhost:5001/video_feed?cam=usb")
    print("Wi-Fi Cam Stream: http://localhost:5001/video_feed?cam=wifi")
    print(f"ESP32 USB URL:    {USB_CAM_URL}")
    print(f"Wi-Fi Cam URL:    {WIFI_CAM_URL}")
    print("WebSocket:        ws://localhost:5001")
    print("=" * 60)
    
    socketio.run(app, host='0.0.0.0', port=5001, allow_unsafe_werkzeug=True)