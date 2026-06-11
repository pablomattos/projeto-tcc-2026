---

# Mapeamento de Projetos e Aplicações com o CI AD5933

## 1. Mapeamento Bibliográfico: Trabalhos Utilizando o AD5933

A tabela abaixo sintetiza os principais estudos mapeados, abrangendo diversas áreas de aplicação que utilizam o AD5933 como núcleo de processamento de impedância.

| Autor Principal | Título do Trabalho | Resumo do Foco |
| --- | --- | --- |
| **García-Jaramillo** | *Design and Validation of a Portable AD5933-Based Impedance Analyzer for Smart Agriculture* | Monitoramento de qualidade de frutas. |
| **M. R. Yagoub** | *A Prototype Portable System for Bioelectrical Impedance Spectroscopy* | Bioimpedância hídrica em plantas (tomates). |
| **B. S. Kim** | *Portable impedance tomography system based on AD5933* | Sistema de EIT 8 canais para imagens 2D. |
| **A. D. M. S. et al.** | *Four-electrode bioimpedance measurement system using the AD5933* | Mitigação de artefatos de interface via 4 eletrodos. |
| **J. F. C. et al.** | *Portable System for Characterization of Electrode-Skin Interface* | Avaliação de sensores de biopotencial (ECG/EEG). |
| **W. A. B. et al.** | *Low-Cost Impedance Analyzer for Biceps Brachii Analysis* | Estudo de bioimpedância muscular vs. bancada. |
| **S. J. et al.** | *Development of an AD5933-based impedance calibration* | Detecção de danos estruturais (afrouxamento de parafusos). |
| **P. W. et al.** | *Multiplexed Platform for Organic Conductive Sensors* | Reconhecimento de gases com sensores condutores. |

---

## 2. Estudo Detalhado: 5 Trabalhos Selecionados

Para a análise aprofundada, selecionamos cinco projetos que demonstram diferentes modos de operação e a necessidade crítica de um *Analog Front-End* (AFE).

| Projeto | Modo de Operação | Parâmetros Principais | Objetivo Principal | Limitações do AD5933 |
| --- | --- | --- | --- | --- |
| **FruitMeter** | Varredura de Frequência | 10 Hz - 100 kHz; Ajuste de ganho e $R_{FB}$ | Qualidade de frutas | Baixa precisão em impedâncias baixas; ruído. |
| **Sistema EIT (Kim)** | Multicanal (8) | Varredura sequencial; Matrizes de dados | Tomografia 2D | Baixa velocidade; canal único (exige MUX). |
| **Monitoramento Estrutural** | Impedância Eletromecânica | Até 100 kHz; Ajuste de $R_{FB}$ e GF | Detecção de falhas | Dependência crítica de calibração; ruído. |
| **Simple-Z** | Varredura de frequência | 100 $\Omega$ a M$\Omega$; 10 mV - 1 V | Portabilidade de baixo custo | Amplitude limitada; offset DC. |
| **4-Eletrodos (IOP)** | Bioimpedância tisular | 5 kHz - 100 kHz | Mitigação de interface | Sensibilidade à impedância de contato. |

---

## 3. Análise Crítica e Necessidade de AFE

### 3.1 Limitações Nativas do AD5933

A revisão destes trabalhos revela que o AD5933 não é uma solução "plug-and-play" para aplicações de precisão devido a:

* **Interface de Entrada:** O ADC interno possui limitações de range, necessitando de ganho externo para sinais de baixa amplitude.
* **Componente DC:** A presença de offset DC pode saturar os estágios analógicos ou corromper a análise DFT.
* **Configuração de Eletrodos:** A topologia de dois eletrodos é inerentemente limitada pela impedância de contato, o que, para aplicações biomédicas, inviabiliza medições precisas.

### 3.2 O Papel do Analog Front-End (AFE)

Em todos os casos estudados, o desenvolvimento de um AFE customizado foi o diferencial para o sucesso do projeto. As funções executadas pelo AFE incluem:

* **Adaptação de Impedância:** Uso de amplificadores de instrumentação para isolar o DUT (*Device Under Test*).
* **Condicionamento de Sinal:** Filtragem passa-faixa e remoção de offset DC.
* **Segurança:** Isolamento galvânico (essencial em aplicações em humanos).
* **Expansão de Range:** Implementação de multiplexação (MUX) ou chaves analógicas para cobrir faixas de impedância fora do escopo original do chip.

---

## 4. Referências Selecionadas para Consulta

1. [FruitMeter: IEEE Xplore](https://ieeexplore.ieee.org/document/9408574)
2. [EIT System: PMC/NCBI](https://pmc.ncbi.nlm.nih.gov/articles/PMC9058721/)
3. [4-Eletrodos: IOPscience](http://iopscience.iop.org/0967-3334/34/4/391)
4. [Interface Pele/Eletrodo: PMC/NCBI](https://pmc.ncbi.nlm.nih.gov/articles/PMC12196835/)
5. [Monitoramento Estrutural: Elsevier/Measurement](https://doi.org/10.1016/j.measurement.2023.112527)

---

*Nota: Esta documentação consolida o embasamento teórico necessário para o seu TCC, destacando que a arquitetura do AFE é o fator determinante entre um protótipo de bancada e um instrumento de medição validado.*