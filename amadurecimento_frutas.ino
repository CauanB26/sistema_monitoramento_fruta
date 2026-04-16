// Projeto: Detecção de Amadurecimento de Frutas
// Autores: Bernardo Cicchelli, Cauan Magalhaes Baptista
// IBMEC - Sistemas Embarcados

#include <LiquidCrystal.h>
#include <DHT.h>
#include <math.h>

// ─── Pinos ───────────────────────────────────────────
#define DHT_PIN     2
#define DHT_TYPE    DHT11
#define LDR_PIN     A0
#define NTC_PIN     A1
#define BUZZER_PIN  8

// LCD: RS, E, D4, D5, D6, D7
LiquidCrystal lcd(12, 11, 5, 4, 3, 6);

DHT dht(DHT_PIN, DHT_TYPE);

// ─── Constantes NTC ──────────────────────────────────
#define RESISTOR_NTC  10000.0  // resistor em série 10kΩ
#define BETA          3950.0   // coeficiente Beta do NTC 10k
#define TEMP_NOMINAL  25.0     // temperatura nominal (°C)
#define R_NOMINAL     10000.0  // resistência nominal a 25°C

// ─── Limiares de alerta ──────────────────────────────
#define TEMP_MAX      30.0   // °C — acima disso acelera amadurecimento
#define TEMP_MIN      10.0   // °C — abaixo disso risco de dano por frio
#define UMID_MAX      85.0   // % — umidade alta favorece fungos
#define UMID_MIN      50.0   // % — umidade baixa resseca a fruta
#define LUZ_MAX       800    // valor bruto A0 — muita luz = calor extra

// ─── Variáveis de controle ───────────────────────────
unsigned long ultimoDisplay = 0;
int telaAtual = 0;
bool alertaAtivo = false;

// ─── Setup ───────────────────────────────────────────
void setup() {
  Serial.begin(9600);
  dht.begin();


  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);

  analogWrite(9, 80);
  lcd.begin(16, 2);
  lcd.print("Monit. Frutas");
  lcd.setCursor(0, 1);
  lcd.print("Iniciando...");
  delay(2000);
  lcd.clear();

  Serial.println("=== Monitor de Amadurecimento de Frutas ===");
  Serial.println("Temp.Amb | Umid.Amb | Temp.Fruta | Luminosidade | Status");
}

// ─── Leitura do NTC ──────────────────────────────────
float lerTemperaturaFruta() {
  int raw = analogRead(NTC_PIN);
  if (raw == 0) return -99;

  float tensao = raw * (5.0 / 1023.0);
  float resistencia = RESISTOR_NTC * (5.0 / tensao - 1.0);

  float tempK = 1.0 / (
    (1.0 / (TEMP_NOMINAL + 273.15)) +
    (1.0 / BETA) * log(resistencia / R_NOMINAL)
  );

  return tempK - 273.15;
}

// ─── Status geral ────────────────────────────────────
String avaliarStatus(float tempAmb, float umid, float tempFruta, int luz) {
  if (tempAmb > TEMP_MAX || tempFruta > TEMP_MAX) return "ALERTA:CALOR";
  if (tempAmb < TEMP_MIN || tempFruta < TEMP_MIN) return "ALERTA:FRIO ";
  if (umid > UMID_MAX)                             return "ALERTA:UMIDO";
  if (umid < UMID_MIN)                             return "ALERTA:SECO ";
  if (luz > LUZ_MAX)                               return "ALERTA:LUZ  ";
  return "OK          ";
}

// ─── Buzzer de alerta ────────────────────────────────
void tocarAlerta(bool ativo) {
  if (ativo) {
    tone(BUZZER_PIN, 1000, 300);
  } else {
    noTone(BUZZER_PIN);
  }
}

// ─── Loop principal ──────────────────────────────────
void loop() {
  float tempAmb  = dht.readTemperature();
  float umid     = dht.readHumidity();
  float tempFruta = lerTemperaturaFruta();
  int   luz      = analogRead(LDR_PIN);

  // Verifica leitura do DHT
  if (isnan(tempAmb) || isnan(umid)) {
    lcd.clear();
    lcd.print("Erro no DHT11");
    Serial.println("ERRO: DHT11 nao respondeu");
    delay(2000);
    return;
  }

  String status = avaliarStatus(tempAmb, umid, tempFruta, luz);
  alertaAtivo = !status.startsWith("OK");
  tocarAlerta(alertaAtivo);

  // ─── Serial Monitor (para registro) ─────────────
  Serial.print(tempAmb);    Serial.print("°C | ");
  Serial.print(umid);       Serial.print("% | ");
  Serial.print(tempFruta);  Serial.print("°C | ");
  Serial.print(luz);        Serial.print(" | ");
  Serial.println(status);

  // ─── LCD: alterna telas a cada 3 segundos ────────
  if (millis() - ultimoDisplay >= 3000) {
    ultimoDisplay = millis();
    lcd.clear();

    switch (telaAtual) {
      case 0:
        // Tela 1: temperatura ambiente e umidade
        lcd.setCursor(0, 0);
        lcd.print("Amb:");
        lcd.print(tempAmb, 1);
        lcd.print((char)223); // símbolo de grau
        lcd.print("C");
        lcd.setCursor(0, 1);
        lcd.print("Umid:");
        lcd.print(umid, 1);
        lcd.print("%");
        break;

      case 1:
        // Tela 2: temperatura da fruta e luminosidade
        lcd.setCursor(0, 0);
        lcd.print("Fruta:");
        lcd.print(tempFruta, 1);
        lcd.print((char)223);
        lcd.print("C");
        lcd.setCursor(0, 1);
        lcd.print("Luz:");
        lcd.print(luz);
        break;

      case 2:
        // Tela 3: status geral
        lcd.setCursor(0, 0);
        lcd.print("Status:");
        lcd.setCursor(0, 1);
        lcd.print(status);
        break;
    }

    telaAtual = (telaAtual + 1) % 3;
  }

  delay(500);
}
