/* HACKATOHM — PROTOTIPO DE BANCADA, SEM ADEQUACAO INDUSTRIAL
 * Arduino IDE + ESP32 + bibliotecas Adafruit MLX90614 e Adafruit BusIO.
 * Ligacao EXEMPLO para breakout compativel com 3,3 V:
 * ESP32 3V3 -> VCC | GND -> GND | GPIO21 -> SDA | GPIO22 -> SCL.
 * Nunca instalar junto de condutores energizados sem projeto eletrico aprovado.
 */
#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <Adafruit_MLX90614.h>

const char* WIFI_SSID = "SEU_WIFI";
const char* WIFI_SENHA = "SUA_SENHA";
const char* URL_SERVIDOR = "http://192.168.0.100:8000/api/reading"; // ajuste para o IP do computador
const char* CHAVE_API = ""; // configure se usar HACKATOHM_API_KEY
const char* ESCOVA = "E01";
Adafruit_MLX90614 ir = Adafruit_MLX90614();

void setup() {
  Serial.begin(115200);
  Wire.begin(21, 22);
  if (!ir.begin()) {
    Serial.println("MLX90614 nao detectado. Revise a alimentacao e conexoes I2C.");
    while (true) delay(1000);
  }
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_SENHA);
  Serial.print("Conectando ao Wi-Fi");
  for (int i = 0; i < 30 && WiFi.status() != WL_CONNECTED; ++i) {
    delay(500); Serial.print('.');
  }
  Serial.println();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    WiFi.reconnect();
    delay(3000);
    return;
  }
  const double temperatura = ir.readObjectTempC();
  const double ambiente = ir.readAmbientTempC();
  if (isnan(temperatura) || isnan(ambiente)) {
    Serial.println("Leitura invalida, amostra descartada.");
    delay(2000); return;
  }
  char corpo[256];
  snprintf(corpo, sizeof(corpo), "{\"escova\":\"%s\",\"temperatura_c\":%.2f,\"ambiente_c\":%.2f}",
           ESCOVA, temperatura, ambiente);
  HTTPClient http;
  http.begin(URL_SERVIDOR);
  http.addHeader("Content-Type", "application/json");
  if (strlen(CHAVE_API)) http.addHeader("X-API-Key", CHAVE_API);
  http.setTimeout(4000);
  const int codigo = http.POST(String(corpo));
  Serial.printf("Temp: %.2f C | ambiente sensor: %.2f C | HTTP: %d\n", temperatura, ambiente, codigo);
  http.end();
  delay(3000);
}
