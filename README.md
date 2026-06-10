# Fruit Ripening Monitor

Sistema embarcado e IoT de baixo custo para monitorar condições ambientais associadas ao amadurecimento de frutas em um recipiente fechado.

**Autores:** Bernardo Cicchelli, Cauan Magalhaes Baptista  
**Disciplina:** IBM3119 - Projeto de Sistemas Embarcados  
**Instituicao:** IBMEC  
**Ano:** 2026

## Objetivo

O projeto mede, registra e visualiza variaveis relacionadas ao armazenamento e amadurecimento de frutas:

- temperatura ambiente;
- umidade relativa;
- luminosidade;
- sinal bruto do sensor MQ-3, usado como indicador relativo de compostos volateis/alcool;
- sinal bruto do sensor MQ-135, usado como indicador relativo de gases/VOCs.

As leituras sao enviadas para o ThingSpeak e analisadas em Python por meio de graficos interativos. O foco do prototipo e acompanhar tendencias ao longo do tempo, identificar perturbacoes no ambiente fechado e comparar o comportamento dos sensores durante o experimento.

## Hardware Utilizado

| Componente | Funcao | Conexao |
|---|---|---|
| ESP32 | Microcontrolador com Wi-Fi integrado | USB / 5 V |
| DHT11 | Temperatura e umidade ambiente | GPIO 4 |
| LDR | Luminosidade ambiente | GPIO 36 |
| MQ-3 | Indicador relativo de alcool/VOCs | GPIO 39 |
| MQ-135 | Indicador relativo de gases/VOCs | GPIO 35 |
| Recipiente transparente | Ambiente de armazenamento da fruta | - |

> Observacao: os sensores MQ sao lidos por `analogRead()`. Sem calibracao com curva do sensor, resistencia de carga, temperatura/umidade de compensacao e gas de referencia, os valores devem ser tratados como **ADC bruto/indicador relativo**, nao como ppm absoluto.

## Software Utilizado

### Firmware

- Arduino IDE 2.x ou PlatformIO;
- framework Arduino para ESP32;
- biblioteca `DHT sensor library`;
- bibliotecas nativas do ESP32: `WiFi.h`, `HTTPClient.h` e `esp_wifi.h`.

Arquivo principal:

```text
amadurecimento_frutas/amadurecimento_frutas.ino
```

O firmware:

1. inicializa o DHT11 e aguarda 2 minutos para aquecimento dos sensores MQ;
2. conecta o ESP32 ao Wi-Fi;
3. le temperatura, umidade, luminosidade, MQ-3 e MQ-135;
4. envia as cinco leituras ao ThingSpeak a cada 15 segundos;
5. imprime logs no Serial Monitor para depuracao.

### Analise e visualizacao

- Python 3.10+;
- `requests`;
- `numpy`;
- `pandas`;
- `matplotlib`;
- `python-dotenv`.

Arquivo principal:

```text
plot_amadurecimento.py
```

O script:

1. busca dados pela API do ThingSpeak ou carrega `dados.json` local;
2. converte timestamps para `America/Sao_Paulo`;
3. remove leituras nulas e outliers pelo metodo IQR;
4. plota temperatura, umidade, luminosidade, MQ-3 e MQ-135;
5. permite filtrar sensores, selecionar intervalo de tempo e exportar PNG.

## Configuracao

### 1. Credenciais do firmware

Copie o arquivo de exemplo:

```text
amadurecimento_frutas/arduino_secrets.example.h
```

para:

```text
amadurecimento_frutas/arduino_secrets.h
```

e preencha:

```cpp
#define WIFI_SSID "nome_da_rede"
#define WIFI_PASSWORD "senha_da_rede"
#define THINGSPEAK_WRITE_API_KEY "sua_write_api_key"
```

O arquivo `arduino_secrets.h` fica fora do Git para evitar vazamento de senha e chave de escrita.

### 2. Variaveis do Python

Crie um arquivo `.env` na raiz do projeto:

```env
THINGSPEAK_CHANNEL_ID=seu_channel_id
THINGSPEAK_READ_API_KEY=sua_read_api_key
```

### 3. Dependencias Python

```bash
pip install -r requirements.txt
```

## Como Executar

### Firmware

1. Instale a placa ESP32 no Arduino IDE.
2. Instale a biblioteca `DHT sensor library`.
3. Crie `amadurecimento_frutas/arduino_secrets.h`.
4. Abra `amadurecimento_frutas/amadurecimento_frutas.ino`.
5. Selecione a placa ESP32 e a porta correta.
6. Faca upload.
7. Abra o Serial Monitor em 9600 bps.

### Graficos

Ultimos 2 dias:

```bash
python plot_amadurecimento.py
```

Intervalo especifico:

```bash
python plot_amadurecimento.py --start 2026-06-10T00:00:00 --end 2026-06-10T23:59:59
```

## Customizacoes e Implementacoes do Grupo

Esta secao descreve os esforcos de desenvolvimento realizados para adaptar componentes, bibliotecas e servicos genericos ao prototipo.

### Integracao ESP32 + ThingSpeak

O firmware coleta dados no ESP32 e envia automaticamente ao ThingSpeak por requisicoes HTTP. Em vez de apenas imprimir leituras no Serial Monitor, o codigo monta uma URL com cinco campos, valida a conexao Wi-Fi, envia os dados ao canal remoto e registra o codigo HTTP de resposta.

### Reconexao Wi-Fi durante o experimento

O loop principal verifica se o ESP32 continua conectado. Em caso de queda, o firmware tenta reconectar antes de voltar a coletar e enviar dados. Isso reduz perda de dados em experimentos longos quando o roteador oscila ou quando o ESP32 perde sinal temporariamente.

### Aquecimento inicial dos sensores MQ

O firmware aguarda 2 minutos antes de iniciar as leituras dos sensores MQ-3 e MQ-135. Esse tempo de aquecimento ajuda a estabilizar o elemento sensivel dos sensores MQ e reduz leituras iniciais artificiais.

### Leitura multissensor

O sistema coleta cinco canais em um unico fluxo:

| Campo ThingSpeak | Variavel | Sensor | Tipo de dado |
|---|---|---|---|
| `field1` | temperatura ambiente | DHT11 | graus Celsius |
| `field2` | umidade ambiente | DHT11 | %RH |
| `field3` | luminosidade | LDR | ADC bruto |
| `field4` | indicador de alcool/VOCs | MQ-3 | ADC bruto |
| `field5` | indicador de gases/VOCs | MQ-135 | ADC bruto |

Essa combinacao integra sensor digital, leituras analogicas e envio IoT. Os sinais MQ foram tratados como indicadores relativos, adequados para comparar tendencias sem afirmar concentracao absoluta em ppm.

### Analise Python com API e fallback local

O script `plot_amadurecimento.py` busca dados diretamente da API do ThingSpeak. Se a API falhar, ele tenta carregar um arquivo local `dados.json`. Assim, o mesmo codigo atende tanto a coleta online quanto a analise offline.

### Limpeza de dados por IQR

O script remove outliers usando intervalo interquartil (IQR) nas colunas numericas. Essa etapa reduz o impacto de picos espurios comuns em sensores de baixo custo e melhora a leitura das tendencias principais.

### Visualizacao interativa

O grafico inclui series brutas, media movel centralizada, checkboxes para ligar/desligar sensores, slider de intervalo temporal e exportacao para PNG. Isso permite navegar por janelas especificas, comparar sensores e gerar imagens para relatorio e apresentacao.

### Tratamento de eventos de abertura do pote

Os dados mostram quedas abruptas de umidade e sinais MQ quando o recipiente e aberto para fotografar a fruta. O projeto documenta esse comportamento como uma perturbacao experimental causada por troca de ar. Na avaliacao, esses eventos podem ser marcados, sombreados no grafico ou removidos de janelas comparativas para preservar a interpretacao do amadurecimento em pote fechado.

### Separacao de credenciais

As credenciais de Wi-Fi e chave de escrita do ThingSpeak ficam em `arduino_secrets.h`, enquanto as credenciais de leitura do Python ficam no `.env`. Isso torna o repositorio mais adequado para entrega e compartilhamento, evitando expor senhas ou chaves de API no codigo versionado.

## Avaliacao Experimental

Durante os testes, o pote fechado apresentou acumulacao de umidade e aumento nos sinais MQ, comportamento esperado em um microambiente com fruta. Quando o pote foi aberto para fotografias, houve queda brusca em umidade e nos sinais MQ por causa da troca de ar com o ambiente externo.

Esse comportamento nao invalida o projeto: ele deve ser tratado como uma perturbacao experimental. Na analise, os momentos de abertura do pote devem ser marcados ou desconsiderados por alguns minutos, para que a comparacao principal use trechos em que o recipiente permaneceu fechado.

Exemplo observado em 10/06/2026, por volta de 15:23 no horario de Sao Paulo:

| Variavel | Antes da abertura | Depois da abertura | Variacao |
|---|---:|---:|---:|
| Temperatura | 26,21 C | 25,93 C | -1,1% |
| Umidade | 77,10% | 66,60% | -13,6% |
| Luminosidade | 129,40 ADC | 89,40 ADC | -30,9% |
| MQ-3 | 1720,60 ADC | 1349,80 ADC | -21,6% |
| MQ-135 | 1339,20 ADC | 979,30 ADC | -26,9% |

## Estrutura do Repositorio

```text
.
├── amadurecimento_frutas/
│   ├── amadurecimento_frutas.ino
│   └── arduino_secrets.example.h
├── artigo_SBrT.tex
├── .env.example
├── plot_amadurecimento.py
├── README.md
├── requirements.txt
└── .gitignore
```