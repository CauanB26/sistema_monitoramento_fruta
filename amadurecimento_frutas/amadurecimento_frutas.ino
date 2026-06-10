#include <DHT.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <esp_wifi.h>

#if __has_include("arduino_secrets.h")
#include "arduino_secrets.h"
#else
#warning "Crie arduino_secrets.h a partir de arduino_secrets.example.h"
#define WIFI_SSID ""
#define WIFI_PASSWORD ""
#define THINGSPEAK_WRITE_API_KEY ""
#endif

// ─── ThingSpeak ──────────────────────────────────────
#define SERVER   "http://api.thingspeak.com/update"

// ─── Pinos ───────────────────────────────────────────
#define DHT_PIN    4
#define DHT_TYPE   DHT11
#define LDR_PIN    36
#define MQ3_PIN    39
#define MQ135_PIN  35

DHT dht(DHT_PIN, DHT_TYPE);

// ─── Setup ───────────────────────────────────────────
void setup() {
  Serial.begin(9600);
  dht.begin();

  Serial.println("Aquecendo sensores MQ (2 minutos)...");
  delay(120000);
  Serial.println("Pronto!");

  WiFi.disconnect(true);
  delay(1000);
  WiFi.mode(WIFI_STA);
  esp_wifi_set_ps(WIFI_PS_NONE);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  Serial.print("Conectando ao Wi-Fi");
  int tentativas = 0;
  while (WiFi.status() != WL_CONNECTED && tentativas < 40) {
    delay(500);
    Serial.print(".");
    tentativas++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWi-Fi conectado!");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nFalha ao conectar! Continuando sem Wi-Fi...");
  }
}

// ─── Envio para ThingSpeak ───────────────────────────
void enviarThingSpeak(float temp, float umid, int luz, int mq3, int mq135) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Wi-Fi desconectado — pulando envio");
    return;
  }

  HTTPClient http;
  String url = String(SERVER) +
               "?api_key=" + THINGSPEAK_WRITE_API_KEY +
               "&field1=" + String(temp) +
               "&field2=" + String(umid) +
               "&field3=" + String(luz) +
               "&field4=" + String(mq3) +
               "&field5=" + String(mq135);

  http.begin(url);
  int httpCode = http.GET();

  if (httpCode > 0) {
    Serial.println("Enviado! HTTP: " + String(httpCode));
  } else {
    Serial.println("Erro no envio: " + String(httpCode));
  }
  http.end();
}

// ─── Loop principal ──────────────────────────────────
void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Reconectando Wi-Fi...");
    WiFi.disconnect(true);
    delay(1000);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    delay(5000);
    return;
  }

  float temp  = dht.readTemperature();
  float umid  = dht.readHumidity();
  int luz     = analogRead(LDR_PIN);
  int mq3     = analogRead(MQ3_PIN);
  int mq135   = analogRead(MQ135_PIN);

  if (isnan(temp) || isnan(umid)) {
    Serial.println("Erro no DHT11!");
    delay(2000);
    return;
  }

  Serial.println("─────────────────────────────");
  Serial.print("Temp:    "); Serial.print(temp);  Serial.println("°C");
  Serial.print("Umid:    "); Serial.print(umid);  Serial.println("%");
  Serial.print("Luz:     "); Serial.println(luz);
  Serial.print("MQ-3:    "); Serial.println(mq3);
  Serial.print("MQ-135:  "); Serial.println(mq135);

  enviarThingSpeak(temp, umid, luz, mq3, mq135);

  delay(15000);
}
