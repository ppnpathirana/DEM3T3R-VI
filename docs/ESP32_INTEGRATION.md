# ESP32 hardware integration

The supported application entry point is `backend/ws_server.py`. Build the React
dashboard with `npm run build`, then run `python backend/ws_server.py`.
The desktop launcher uses this same backend. `main.py` and `server.py` are older
entry points and are not the integrated application.

## Wi-Fi connection

The firmware in `esp32/esp32_master/esp32_master.ino` connects to the computer at
its configured `TCP_SERVER_IP`, port 5000. Set that address to the computer's LAN
IPv4 address before uploading the firmware. Wi-Fi credentials are in the sketch.
Keep the computer and rover on the same network and allow inbound TCP 5000 and
5001 through the computer's firewall on the private network.

Alternatively, set `ESP32_HOST=<rover-IP>` in the root `.env`. The backend connects
to the ESP32's existing TCP server on port 8080 (override with `ESP32_TCP_PORT`).
The address of the computer in the sketch is not the ESP32's own Wi-Fi address.
The revised sketch must be compiled and uploaded to enable acknowledgements,
timed pumping, USB commands and connection-loss shutdown.

Open `http://<computer-IP>:5001` from another device. For Vite development, use
port 5173. For an Android build, set `VITE_BACKEND_URL=http://<computer-IP>:5001`
in `.env.local` before building and synchronizing Capacitor. This URL is public
frontend configuration; never put API secrets into VITE variables.

## Pin mapping from the sketch

| Device | ESP32 GPIO |
|---|---|
| Left BTS7960 RPWM / LPWM / R_EN / L_EN | 10 / 11 / 12 / 13 |
| Right BTS7960 RPWM / LPWM / R_EN / L_EN | 15 / 16 / 17 / 18 |
| R1 pump / R2 solenoid 1 / R3 solenoid 2 / R4 spare | 4 / 5 / 6 / 7 |
| BME280 and BH1750 SDA / SCL | 21 / 47 |
| Soil probes 1 / 2 | 2 / 3 |
| Ultrasonic trigger / echo | 8 / 9 |
| Battery ADC / UV ADC | 1 / 14 |
| GPS RX / TX | 41 / 42 |

Relays are active LOW. These are software pin assignments, not a verified wiring
diagram. Sensor voltage compatibility, motor power, grounding and calibration
must be checked against the actual hardware. Only one ultrasonic sensor is
sampled; there is no implemented rear range sensor.

## Protocol and feedback

TCP and USB use one JSON object per newline. Telemetry maps raw soil readings
separately from moisture percentages, preserves GPS and motor speeds, and reports
relay states from the device. A sent command is not treated as measured feedback.
Firmware ACK means the command handler applied outputs; it does not prove
physical motor movement or water flow.

The backend sends a heartbeat every 500 ms. Revised firmware shuts down motors
and relays after 3 seconds without a control message. Pump commands are capped
at 10 seconds. This software watchdog does not replace a physical emergency stop.

## Camera limitation

The supplied sketch has no implemented USB UVC capture driver. Its old streaming
loop sent no image bytes and blocked networking. It now returns HTTP 503 promptly.
Use `CAMERA_URL=<actual external camera stream>` until a camera driver is added.

## Bench validation

1. Upload the revised sketch and verify fresh telemetry in the dashboard.
2. With wheels raised, test each direction and stop; verify reported motor speeds.
3. Test relays individually with water only; confirm pump timeout.
4. Disconnect the backend and confirm outputs stop within the watchdog interval.
5. Reconnect; confirm outputs stay off until a new command is issued.

## Desktop checks before the bench test

Open the existing desktop shortcut. The launcher checks `/api/health` directly,
bypassing system proxies, and allows up to 120 seconds for startup. The dashboard
and backend start in manual mode. The health endpoint distinguishes application
readiness from ESP32 connectivity and reports telemetry age.

The dashboard emergency stop now latches in the backend across clients. It also
latches when the last dashboard disconnects or received ESP32 telemetry expires.
Reset the stop explicitly after reconnecting. Resetting never turns actuators on.
Autonomous mode requires fresh hardware telemetry. Missing acknowledgements stop
the autonomous sequence instead of reporting simulated success.

The crop selector lists the 16 actual model files. Model inference tests use
controlled model output to verify action parsing; they do not measure accuracy.

Automated protocol tests: `python -m unittest discover -s tests -p test_hardware_integration.py`.
Physical movement, wiring, sensor calibration and firmware compilation require
separate verification on the actual board.
