// =============================================
// Hosyond ESP32 - Stable v3 for Boris
// =============================================

#include <WiFi.h>
#include <WebServer.h>

const char* ssid = "";           // ← Hotspot SSID
const char* password = "";

// Pins
#define PAN_PIN   13
#define TILT_PIN  12
#define IN1  25
#define IN2  26
#define IN3  27
#define IN4  14
#define ENA  32   
#define ENB  33   

int panPos = 90;
int tiltPos = 90;
int currentSpeed = 180;

WebServer server(80);

void writeServo(int pin, int angle) {
  int pulse = map(angle, 0, 180, 1638, 8192);
  ledcWrite(pin, pulse);
}

void stopMotors() {
  digitalWrite(IN1, LOW); digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW); digitalWrite(IN4, LOW);
}

void setSpeed(int spd) {
  ledcWrite(ENA, spd); 
  ledcWrite(ENB, spd);
  currentSpeed = spd;
}

void forward()  { digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW);  digitalWrite(IN3, LOW);  digitalWrite(IN4, HIGH); }
void backward() { digitalWrite(IN1, LOW);  digitalWrite(IN2, HIGH); digitalWrite(IN3, HIGH); digitalWrite(IN4, LOW); }
void turnLeft() { digitalWrite(IN1, LOW);  digitalWrite(IN2, HIGH); digitalWrite(IN3, LOW);  digitalWrite(IN4, HIGH); }
void turnRight(){ digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW);  digitalWrite(IN3, HIGH); digitalWrite(IN4, LOW); }

void handleRoot() {
  String html = R"rawliteral(
<!DOCTYPE html><html><head><title>Rover Control</title>
<style>body{background:#111;color:#0f0;text-align:center;font-family:Arial;}</style> 
</head><body> 
<h1>Rover Control</h1> 
<button onclick="send('panLeft')">Pan Left</button> 
<button onclick="send('panRight')">Pan Right</button><br><br> 
<button onclick="send('tiltUp')">Tilt Up</button> 
<button onclick="send('tiltDown')">Tilt Down</button><br><br> 
<button onclick="send('forward')">Forward</button><br> 
<button onclick="send('left')">Left</button> 
<button onclick="send('stop')" style="background:red;color:white;">STOP</button> 
<button onclick="send('right')">Right</button><br> 
<button onclick="send('backward')">Backward</button><br><br> 
<button onclick="send('slow')">Slow</button> 
<button onclick="send('medium')">Medium</button> 
<button onclick="send('fast')">Fast</button> 
<script>function send(cmd){fetch('/'+cmd);}</script> 
</body></html>
)rawliteral";
  server.send(200, "text/html", html);
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n=== Hosyond 32 Stable v3 for Boris ===");

  pinMode(IN1, OUTPUT); pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT); pinMode(IN4, OUTPUT);
  
  ledcAttach(ENA, 5000, 8); 
  ledcAttach(ENB, 5000, 8);
  ledcAttach(PAN_PIN, 50, 16);
  ledcAttach(TILT_PIN, 50, 16);

  stopMotors();
  setSpeed(215);
  writeServo(PAN_PIN, panPos);
  writeServo(TILT_PIN, tiltPos);

  // ---------- WiFi connection with timeout + diagnostics ----------
  WiFi.mode(WIFI_STA);          // явно режим клиента, без AP-режима
  WiFi.disconnect(true);
  delay(100);
  WiFi.begin(ssid, password);
  Serial.print("Connecting to ");
  Serial.println(ssid);

  unsigned long startAttempt = millis();
  const unsigned long WIFI_TIMEOUT = 15000;  // 15 секунд максимум на попытку

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    if (millis() - startAttempt > WIFI_TIMEOUT) {
      Serial.println("\n❌ WiFi connection FAILED");
      Serial.print("Status code: ");
      Serial.println(WiFi.status());
      // 0=IDLE 1=NO_SSID_AVAIL 3=CONNECTED 4=CONNECT_FAILED
      // 5=CONNECTION_LOST 6=DISCONNECTED
      Serial.println("Retrying in 3 sec...");
      delay(3000);
      WiFi.disconnect(true);
      delay(100);
      WiFi.begin(ssid, password);
      startAttempt = millis();
    }
  }

  Serial.println("\n✅ WiFi Connected!");
  Serial.println("IP Address : " + WiFi.localIP().toString());
  Serial.println("MAC Address: " + WiFi.macAddress());
  Serial.print("Signal RSSI: ");
  Serial.println(WiFi.RSSI());
  // ------------------------------------------------------------------

  server.on("/", handleRoot);
  server.on("/panLeft",  [](){ panPos = constrain(panPos + 15, 0, 180); writeServo(PAN_PIN, panPos); server.send(200); });
  server.on("/panRight", [](){ panPos = constrain(panPos - 15, 0, 180); writeServo(PAN_PIN, panPos); server.send(200); });
  server.on("/tiltUp",   [](){ tiltPos = constrain(tiltPos + 15, 0, 180); writeServo(TILT_PIN, tiltPos); server.send(200); });
  server.on("/tiltDown", [](){ tiltPos = constrain(tiltPos - 15, 0, 180); writeServo(TILT_PIN, tiltPos); server.send(200); });

  server.on("/forward",  [](){ forward();  server.send(200); });
  server.on("/backward", [](){ backward(); server.send(200); });
  server.on("/left",     [](){ turnLeft(); server.send(200); });
  server.on("/right",    [](){ turnRight();server.send(200); });
  server.on("/stop",     [](){ stopMotors(); server.send(200); });
  server.on("/slow",     [](){ setSpeed(170); server.send(200); });
  server.on("/medium",   [](){ setSpeed(215); server.send(200); });
  server.on("/fast",     [](){ setSpeed(255); server.send(200); });

  server.begin();
  Serial.println("Web Server Ready!");
}

void loop() {
  server.handleClient();
}
