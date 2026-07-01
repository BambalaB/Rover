# Roll & See — Dual Rover System

Student-Originated Software Project — Spring 2026
The Evergreen State College

Two identical 4WD Wi-Fi controlled rovers with real-time video streaming and an advanced desktop control interface.

## Concept

The "Roll & See" system allows a user to drive the rovers, control a pan/tilt camera mounted on top, and view live video feeds — using both manual buttons and an intuitive click-to-move mapping interface.

Each rover uses a dual-ESP32 architecture:
- one ESP32 handles motor control and servos
- the second (Freenove ESP32-S3-CAM) streams MJPEG video

A custom Python Tkinter GUI serves as the central control station.

## Key Features

- Dual-rover hardware assembly (LewanSoul chassis, L298N motor drivers, SG90 pan/tilt servos, power stabilization with capacitors)
- Reliable Wi-Fi communication using a mobile hotspot
- Real-time video streaming from both rovers
- Tkinter GUI with four tabs:
  - **Main Control** — movement buttons, speed control, pan/tilt
  - **Mapping & Plotting** — live video with click-to-move zones
  - **Data & Logs** — SQLite command history with frequency and timeline graphs
  - **System Monitor** — live CPU and memory usage
- "Both" mode — sends synchronized commands to both rovers simultaneously
- Robust logging of every command for later analysis

## Project Structure

- `32_MainMove_v3_1.ino` — ESP32 firmware for motor and servo control
- `Esp32_S3BestVideo_v3.ino` — ESP32-S3-CAM firmware for video streaming
- `rover_gui4.py` — Python GUI: control, mapping, logging, system monitoring

## Requirements

- Arduino IDE (for flashing ESP32)
- Python 3.x
- Libraries: tkinter, sqlite3, threading (standard library), opencv-python (for CV)

## Technologies

Embedded systems programming (Wi-Fi, HTTP servers, camera control, PWM motor/servo control), advanced Python GUI development with threading and real-time data handling, SQLite database design and integration.

## Future Enhancements

- WebSocket streaming for smoother, lower-latency video
- Autonomous modes (obstacle avoidance, line following, waypoint navigation)
- Battery voltage monitoring and low-battery alerts in the GUI
- Joystick/gamepad support
- Upgrade to Raspberry Pi for advanced computer vision
- Mapping and SLAM capabilities for true exploration functionality

## Team

- **Boris Bambalaev** — Mapping & Plotting development lead. Research and development, programming of mapping and plotting integration in rover(s) and GUI. Assisted with prototype hardware assembly, joint testing sessions, and provided collaborative ideas and feedback throughout development.
- **James Hornum** — Hardware development and programming lead. Prototype hardware assembly, ESP32 programming, GUI development, database integration, documentation, and primary testing/debugging.

## Authors

Boris Bambalaev, James Hornum — Student-Originated Software, Spring 2026
