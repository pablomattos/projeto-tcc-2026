# ESPECIFICAÇÃO DE HARDWARE E LISTA DE MATERIAIS (BOM)

**Projeto:** Subsistema Central de Medição por Espectroscopia de Impedância  
**Chips de Controle:** Analog Devices AD5941 + Espressif Systems ESP32-WROOM-32E  
**Data da Documentação:** Junho de 2026  

---

## 1. Tabela de Componentes e Lista de Materiais (BOM)

A tabela abaixo descreve de forma analítica e ponto a ponto os componentes semicondutores, passivos e de precisão que compõem a malha central do circuito eletrônico:

| Item | Componente Eletrônico e Descrição Técnica | Part Number de Fábrica | Fabricante | Qtd |
| :---: | :--- | :---: | :---: | :---: |
| **1** | IC Analog Front End (AFE) para Espectroscopia de Impedância (LFCSP-48) | AD5941BCPZ | Analog Devices | 1 |
| **2** | Módulo Microcontrolador ESP32 DevKit v4 (Chip ESP32-WROOM-32E) | ESP32-DEVKITC-32E | Espressif Systems | 1 |
| **3** | Cristal de Quartzo de Alta Estabilidade 16.000 MHz 9pF SMD 3.2x2.5mm | ECS-160-9-33B-CWN-TR | ECS Inc. | 1 |
| **4** | Capacitor Cerâmico Multicamadas MLCC 12pF 25V C0G (NP0) SMD 0603 | C0603C0G1E120J030BA | TDK | 2 |
| **5** | Capacitor Cerâmico Multicamadas MLCC 10µF 16V X5R SMD 1206 (Bulk) | CC1206KFX5R7BB106 | YAGEO | 1 |
| **6** | Capacitor Cerâmico Multicamadas MLCC 1µF 16V X7R SMD 0603 (Reg LDO) | CC0603JRX77BB105 | YAGEO | 1 |
| **7** | Capacitor Cerâmico Multicamadas MLCC 0.1µF 16V X7R SMD 0603 (Bypass) | C0603JRX7R7BB104 | YAGEO | 2 |
| **8** | Resistor de Filme Fino de Ultra Precisão para Calibração 1.00 kΩ 0.1% 0603 | RC0603BR-071KL | YAGEO | 1 |

---

## 2. Notas de Implementação de Hardware e Engenharia

### A. Malha do Cristal e Temporização Síncrona (Itens 3 e 4)
* **Objetivo Técnico:** Mitigar o desvio (*drift*) de fase e frequência do motor interno da Transformada Discreta de Fourier (DFT) do AD5941.
* **Cálculo de Carga:** Os capacitores de 12 pF operam em malha em direção ao terra (GND). Eles foram dimensionados para balancear as capacitâncias parasitas das trilhas de cobre e pads físicos da placa de circuito impresso ($C_{stray} \approx 3\text{ pF}$), permitindo que o cristal enxergue exatamente a sua capacitância de carga nominal ideal de fábrica ($C_L = 9\text{ pF}$):
  $$C_L = \frac{C_1 \cdot C_2}{C_1 + C_2} + C_{stray} = \frac{12 \cdot 12}{12 + 12} + 3 = 6 + 3 = 9\text{ pF}$$
* **Estabilidade Térmica:** O uso mandatório do dielétrico **C0G (NP0)** garante coeficiente térmico nulo, impedindo oscilações de frequência causadas por variações na bancada de ensaios.

### B. Sistema de Filtragem de Potência e Desacoplamento (Itens 5, 6 e 7)
* **Filtragem Bulk (Item 5):** O capacitor de 10 µF (encapsulamento 1206) atua como acumulador de energia local na entrada principal de 3.3V. Ele absorve quedas de tensão transitórias bruscas geradas pelas demandas de corrente do rádio Wi-Fi e Bluetooth do ESP32.
* **Filtragem Bypass (Item 7):** Os capacitores de 0.1 µF (0603) eliminam os ruídos parasitas lógicos de alta frequência na faixa de MHz gerados pelo barramento digital SPI. Devem ser soldados fisicamente a menos de 1.5 mm de distância de cada pino de alimentação positiva analógica e digital do AD5941.
* **Estabilização LDO (Item 6):** O capacitor de 1 µF acoplado ao pino `Reg_DVDD` estabiliza o regulador de tensão linear interno de baixo dropout do chip analógico.

### C. Estágio Metrológico de Calibração (Item 8)
* **Resistor de Referência ($R_{cal}$):** O resistor de filme fino de 1.00 kΩ atua como o padrão de malha ratiométrica de ultra precisão do sistema. Sua tolerância estrita de **0.1%** minimiza erros de quantização sistemáticos do conversor analógico-digital (SAR ADC), servindo como o valor conhecido confiável de comparação para o cálculo de impedâncias complexas desconhecidas.