# Fruit Ripening Monitor — Sistema Embarcado de Monitoramento de Amadurecimento de Frutas

**Autores:** Bernardo Cicchelli, Cauan Magalhães Baptista  
**Disciplina:** IBM3119 — Projeto de Sistemas Embarcados  
**Instituição:** IBMEC  
**Ano:** 2026

---

## Descrição do Projeto

Este projeto implementa um sistema embarcado de baixo custo para monitoramento em tempo real das condições ambientais que influenciam o processo de amadurecimento de frutas. O sistema realiza leituras contínuas de temperatura ambiente, umidade relativa do ar, temperatura superficial da fruta e intensidade luminosa, exibindo os dados em um display LCD e emitindo alertas sonoros sempre que algum parâmetro ultrapassa os limiares de segurança definidos.

O objetivo é fornecer ao produtor ou ao consumidor um indicativo simples e confiável sobre se as condições de armazenamento das frutas estão adequadas, prevenindo perdas por deterioração precoce ou danos por temperatura/umidade inadequadas.

---

## Hardware Utilizado

| Componente | Descrição | Conexão |
|---|---|---|
| **Arduino Mega 2560** | Microcontrolador principal (ATmega2560, 16 MHz, 5 V) | — |
| **DHT11** | Sensor digital de temperatura e umidade ambiente | Pino digital 2 |
| **NTC 10kΩ (β = 3950)** | Termistor NTC para medição da temperatura superficial da fruta | Pino analógico A1 |
| **LDR** | Fotorresistor para medição da intensidade luminosa | Pino analógico A0 |
| **LCD 16×2 (HD44780)** | Display de cristal líquido para exibição dos dados | Pinos 12, 11, 5, 4, 3, 6 |
| **Buzzer passivo** | Alerta sonoro em caso de condição inadequada | Pino digital 8 |
| **Resistor 10 kΩ** | Divisor de tensão para o NTC | A1 (em série com NTC) |
| **Potenciômetro** | Controle do brilho do LCD (backlight via PWM no pino 9) | Pino 9 (PWM) |

### Diagrama de ligação (descrição textual)

```
DHT11  → D2 (sinal), 5V, GND
NTC    → A1 (ponto médio do divisor: NTC entre A1 e GND; Resistor 10kΩ entre 5V e A1)
LDR    → A0 (ponto médio do divisor: LDR entre 5V e A0; Resistor 10kΩ entre A0 e GND)
LCD    → RS=12, E=11, D4=5, D5=4, D6=3, D7=6; V0 (contraste) via potenciômetro
Buzzer → D8 (positivo), GND
PWM    → D9 (backlight LCD)
```

---

## Software Utilizado

| Item | Versão / Detalhes |
|---|---|
| **Arduino IDE** | 2.x |
| **Linguagem** | C++ (Arduino framework) |
| **Biblioteca LiquidCrystal** | Padrão Arduino (HD44780) |
| **Biblioteca DHT sensor library** | Adafruit DHT Sensor Library |
| **Biblioteca math.h** | Padrão C — usada para `log()` no cálculo Steinhart-Hart |

### Descrição do firmware

O firmware (`amadurecimento_frutas.ino`) opera em loop contínuo com as seguintes etapas:

1. **Leitura dos sensores** — DHT11 (temperatura ambiente e umidade), NTC via divisor de tensão (temperatura da fruta), LDR (luminosidade).
2. **Cálculo da temperatura pelo NTC** — equação de Steinhart-Hart simplificada (modelo β) para converter a resistência medida em temperatura em °C.
3. **Avaliação do status** — comparação dos valores com limiares pré-definidos; retorna um código de status (`OK`, `ALERTA:CALOR`, `ALERTA:FRIO`, `ALERTA:UMIDO`, `ALERTA:SECO`, `ALERTA:LUZ`).
4. **Alerta sonoro** — buzzer acionado com `tone()` quando qualquer condição de alerta é detectada.
5. **Display LCD rotativo** — três telas alternadas a cada 3 segundos: (1) temperatura ambiente + umidade; (2) temperatura da fruta + luminosidade; (3) status geral.
6. **Registro serial** — todos os valores são enviados via Serial (9600 bps) para log e depuração.

### Limiares de alerta

| Parâmetro | Limiar mínimo | Limiar máximo | Justificativa |
|---|---|---|---|
| Temperatura (ambiente e fruta) | 10 °C | 30 °C | Faixas seguras para armazenamento da maioria das frutas tropicais |
| Umidade relativa | 50 % | 85 % | Abaixo resseca; acima favorece fungos |
| Luminosidade (valor ADC bruto) | — | 800 | Exposição excessiva à luz eleva temperatura interna |

---

## Modelo de Inteligência Computacional

Este projeto não utiliza um modelo de inteligência computacional dedicado (como redes neurais ou aprendizado de máquina). A lógica de decisão é baseada em **regras determinísticas** com limiares fixos derivados da literatura agronômica sobre armazenamento de frutas. Essa abordagem foi escolhida por ser suficiente para o escopo do protótipo e por garantir execução em tempo real no microcontrolador ATmega2560 com recursos limitados.

Como trabalho futuro, um modelo de regressão ou classificação treinado com dados históricos poderia ser embarcado (utilizando TinyML / TensorFlow Lite for Microcontrollers) para prever o estado de amadurecimento com maior precisão.

---

## Como compilar e carregar

1. Instale o **Arduino IDE 2.x**.
2. Instale as bibliotecas via Library Manager:
   - `DHT sensor library` (Adafruit)
   - `LiquidCrystal` (já incluída no IDE)
3. Abra `amadurecimento_frutas.ino`.
4. Selecione a placa **Arduino Mega 2560** e a porta COM correta.
5. Clique em **Upload**.
6. Abra o **Serial Monitor** a 9600 bps para acompanhar os logs.

---

## Estrutura do repositório

```
.
├── amadurecimento_frutas.ino   # Firmware principal
├── README.md                   # Documentação do hardware e software
├── CUSTOMIZATIONS.md           # Customizações e esforços de desenvolvimento
└── artigo_SBrT.tex             # Artigo científico no modelo SBrT (PDF enviado ao professor)
```

---

## Licença

Projeto acadêmico — uso livre para fins educacionais.
