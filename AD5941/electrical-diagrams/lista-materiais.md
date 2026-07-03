Aqui está a tabela da **Lista de Materiais (BOM)** atualizada e expandida. Adicionei uma coluna exclusiva especificando exatamente em quais pinos do encapsulamento **LFCSP de 48 pinos** do AD5941 cada componente passivo e de suporte deve ser conectado.

---

# ESPECIFICAÇÃO DE HARDWARE E LISTA DE MATERIAIS (BOM)

**Projeto:** Subsistema Central de Medição por Espectroscopia de Impedância

**Chips de Controle:** Analog Devices AD5941 + Espressif Systems ESP32-WROOM-32E

**Data da Documentação:** Junho de 2026

---

## 1. Tabela de Componentes e Lista de Materiais (BOM)

A tabela abaixo descreve de forma analítica os componentes que compõem a malha central do circuito eletrônico, detalhando sua pinagem física de destino no AD5941:

| Item | Componente Eletrônico e Descrição Técnica | Part Number de Fábrica | Fabricante | Qtd | Pinos de Conexão no AD5941 (LFCSP-48) |
| --- | --- | --- | --- | --- | --- |
| **1** | IC Analog Front End (AFE) para Espectroscopia de Impedância (LFCSP-48) | AD5941BCPZ | Analog Devices | 1 | *Componente Principal* |
| **2** | Módulo Microcontrolador ESP32 DevKit v4 (Chip ESP32-WROOM-32E) | ESP32-DEVKITC-32E | Espressif Systems | 1 | Pinos 15 (CS), 16 (SCLK), 17 (MOSI), 18 (MISO), 19 (GPIO0/IRQ) e 22 (RESET). |
| **3** | Cristal de Quartzo de Alta Estabilidade 16.000 MHz 9pF SMD 3.2x2.5mm | ECS-160-9-33B-CWN-TR | ECS Inc. | 1 | Entre o **Pino 11 (XTALI)** e o **Pino 12 (XTALO)**. |
| **4** | Capacitor Cerâmico Multicamadas MLCC 12pF 25V C0G (NP0) SMD 0603 | C0603C0G1E120J030BA | TDK | 2 | Um capacitor do **Pino 11 (XTALI) para o DGND**; um do **Pino 12 (XTALO) para o DGND**. |
| **5** | Conector Borne KRE para Sensores/Eletrodos, 6 vias, Passo 7.5mm, Entrada Vertical | DB128V-7.5-6P-GN-S | Degson | 1 | Roteado diretamente para os pinos analógicos de medição: **47 (CE0), 48 (RE0), 46 (DE0), 45 (SE0), 39 (AIN0)** e malha de **AGND**. |
| **6** | Resistor de Filme Fino de Ultra Precisão para Calibração 1.00 kΩ 0.1% 0603 ($R_{CAL}$) | RC0603BR-071KL | YAGEO | 1 | Conectado diretamente entre o **Pino 32 (RCAL0)** e o **Pino 33 (RCAL1)**. |
| **7** | Resistor de Filme Espesso para Pull-up de Linha Digital 10 kΩ 5% SMD 0603 | RC0603JR-0710KL | YAGEO | 1 | Entre o **Pino 22 (RESET)** e a linha de alimentação digital **IOVDD (Pino 26)**. |
| **8** | Capacitor Cerâmico Multicamadas MLCC 10µF 16V X5R SMD 1206 (Bulk AVDD) | CC1206KFX5R7BB106 | YAGEO | 1 | Conectado na entrada principal de alimentação analógica comum entre os **Pinos 30 e 41 (AVDD) para o AGND**. |
| **9** | Capacitor Cerâmico Multicamadas MLCC 4.7µF 16V X5R SMD 0603 (Bulk DVDD e VREF 1.82V) | CC0603KRX5R7BB475 | YAGEO | 2 | **Capacitor 1:** Do **Pino 6 (DVDD) para o DGND**.<br>

<br>**Capacitor 2:** Do **Pino 43 (VREF_1V82) para o AGND**. |
| **10** | Capacitor Cerâmico Multicamadas MLCC 470nF 16V X7R SMD 0603 (Desacoplamento de Reguladores) | CC0603KRX7R7BB474 | YAGEO | 4 | **Capacitor 1:** Do **Pino 4 (VREF_2V5) para o AGND**.<br>

<br>**Capacitor 2:** Do **Pino 5 (AVDD_REG) para o AGND**.<br>

<br>**Capacitor 3:** Do **Pino 14 (DVDD_REG_1V8) para o DGND**.<br>

<br>**Capacitor 4:** Do **Pino 31 (VBIAS_CAP) para o AGND**. |
| **11** | Capacitor Cerâmico Multicamadas MLCC 100nF 16V X7R SMD 0603 (Bypass e Filtros LPTIA/DACs) | C0603JRX7R7BB104 | YAGEO | 7 | Dispostos individualmente:<br>

<br>• 1x no **Pino 30 (AVDD)** para o AGND<br>

<br>• 1x no **Pino 41 (AVDD)** para o AGND<br>

<br>• 1x no **Pino 26 (IOVDD)** para o DGND<br>

<br>• 1x instalado **entre o Pino 2 (RC0_1) e o Pino 3 (RC0_0)**<br>

<br>• 1x do **Pino 8 (VBIAS0) para o AGND**<br>

<br>• 1x do **Pino 9 (VZERO0) para o AGND**<br>

<br>• 1x do **Pino 40 (AIN4/LPF0) para o AGND** |

---

## 2. Resumo das Diretrizes de Conexão Física (PCB Layout)

* **Malhas de Terra (GND):** Atente-se para conectar os capacitores vinculados ao **DGND** (pinos 13, 23, 25) no plano de terra digital, e os capacitores vinculados ao **AGND** (pinos 29, 42, 44) no plano de terra analógico.
* **Proximidade:** Todos os capacitores do **Item 11** (Bypass de 100 nF) e do **Item 10** (Filtros de reguladores de 470 nF) devem ficar o mais perto possível (menos de 1,5 mm) de seus respectivos pinos para garantir a imunidade a ruídos elétricos de alta frequência.
* **Resistor de Calibração ($R_{CAL}$):** O pino 32 e o pino 33 não devem possuir trilhas longas ou ramificadas até o resistor de precisão para evitar que a própria resistência da trilha interfira na calibração ratiométrica do sistema.