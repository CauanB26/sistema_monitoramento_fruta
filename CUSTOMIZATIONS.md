# Customizações e Esforços de Desenvolvimento

Este documento descreve as adaptações e desenvolvimentos personalizados realizados no projeto de monitoramento de amadurecimento de frutas em relação ao software e hardware padrão.

---

## 1. Cálculo de temperatura pelo NTC via equação de Steinhart-Hart (modelo β)

**O que foi feito:** Em vez de utilizar tabelas de lookup ou bibliotecas prontas para termistores NTC, implementamos manualmente a equação do modelo β diretamente no firmware:

```cpp
float tempK = 1.0 / (
  (1.0 / (TEMP_NOMINAL + 273.15)) +
  (1.0 / BETA) * log(resistencia / R_NOMINAL)
);
return tempK - 273.15;
```

**Por quê é uma customização:** A leitura analógica bruta do Arduino retorna um valor ADC (0–1023) que precisa ser convertido em tensão, depois em resistência (via divisor de tensão), e finalmente em temperatura usando a equação física do termistor. Esse processo não é fornecido por nenhuma biblioteca padrão do Arduino para NTC genérico. Todo o pipeline de conversão foi escrito do zero e os parâmetros (β = 3950, R_nominal = 10 kΩ, T_nominal = 25 °C) foram ajustados ao componente físico utilizado.

---

## 2. Display LCD com rotação automática de telas

**O que foi feito:** O display 16×2 alterna automaticamente entre três telas distintas a cada 3 segundos, sem bloquear o loop principal (uso de `millis()` em vez de `delay()`):

- Tela 0: temperatura ambiente + umidade
- Tela 1: temperatura da fruta + luminosidade
- Tela 2: status geral do sistema

**Por quê é uma customização:** O uso padrão da biblioteca `LiquidCrystal` exibe informações estáticas. A lógica de rotação temporal com `millis()` foi desenvolvida para maximizar a informação exibida em um display de apenas 2 linhas, mantendo o firmware responsivo (sem `delay()` longo no loop principal).

---

## 3. Sistema de alerta sonoro baseado em múltiplas condições

**O que foi feito:** A função `avaliarStatus()` analisa simultaneamente quatro variáveis (temperatura ambiente, temperatura da fruta, umidade e luminosidade) e retorna um código de status legível. O buzzer é acionado via `tone()` apenas quando alguma condição de alerta é detectada.

**Por quê é uma customização:** A lógica de priorização das condições de alerta (calor > frio > úmido > seco > luz) e os limiares escolhidos foram definidos com base em pesquisa bibliográfica sobre armazenamento pós-colheita de frutas tropicais, e não correspondem a nenhum exemplo ou biblioteca pré-existente.

---

## 4. Limiares agronômicos personalizados

**O que foi feito:** Os limiares de alerta foram definidos com base na literatura agronômica:

| Parâmetro | Limiar | Fonte de referência |
|---|---|---|
| Temperatura máxima | 30 °C | Temperatura acima da qual a maioria das frutas tropicais acelera a respiração celular e o amadurecimento |
| Temperatura mínima | 10 °C | Abaixo deste valor ocorre dano por frio (*chilling injury*) em frutas sensíveis como banana e mamão |
| Umidade máxima | 85 % | Acima deste valor há proliferação de fungos e bactérias |
| Umidade mínima | 50 % | Abaixo deste valor ocorre desidratação da fruta |
| Luminosidade máxima (ADC) | 800 | Valor empírico calibrado para o LDR utilizado, correspondendo a exposição solar direta |

**Por quê é uma customização:** A parametrização não foi extraída de nenhum exemplo genérico; os valores foram pesquisados, adaptados ao contexto local (frutas tropicais, clima brasileiro) e calibrados experimentalmente para o sensor LDR utilizado.

---

## 5. Log serial estruturado para análise de dados

**O que foi feito:** O sistema emite continuamente, via Serial (9600 bps), uma linha de log com todos os parâmetros e o status em formato tabular:

```
Temp.Amb | Umid.Amb | Temp.Fruta | Luminosidade | Status
25.30°C | 62.00% | 23.80°C | 412 | OK
```

**Por quê é uma customização:** Esse formato foi definido para facilitar a captura dos dados no Serial Monitor ou em scripts Python para análise posterior, possibilitando a geração de gráficos e histórico de condições. Não é uma funcionalidade padrão de nenhuma biblioteca utilizada.

---

## 6. Controle de brilho do LCD por PWM

**O que foi feito:** O pino 9 (PWM) é utilizado com `analogWrite(9, 80)` para controlar o brilho do backlight do LCD com intensidade reduzida (valor 80/255 ≈ 31%), economizando energia e reduzindo o aquecimento do componente.

**Por quê é uma customização:** O uso padrão do LCD liga o backlight diretamente em 5 V com brilho máximo. O controle por PWM foi adicionado para adequar o brilho ao ambiente de uso e demonstrar controle fino de periféricos.
