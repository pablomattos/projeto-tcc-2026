import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import io
from scipy.signal import savgol_filter

# ======================================================
# DATASET EXTRAÍDO DA SUA BANCADA (Conforme image_9e1f0f.png)
# ======================================================
dados_brutos = """Freq(Hz),Magnitude_Ohm,Fase_Graus
1000,2160.00,0.00
2000,2128.29,-4.99
3000,1964.01,-4.58
4000,1963.75,-8.26
5000,1813.79,-3.37
6000,1813.79,-3.37
7000,1680.24,-3.25
8000,1692.37,-8.60
9000,1574.64,-8.49
10000,1574.64,-8.49
11000,1574.74,-5.83
12000,1478.11,-5.90
13000,1478.11,-5.90
14000,1473.19,-2.26
15000,1496.81,-7.57
16000,1496.81,-7.57
17000,1435.98,-7.76
18000,1426.15,-4.24
19000,1426.15,-4.24
20000,1426.15,-4.24
21000,1444.54,-5.84
22000,1444.54,-5.84
23000,1326.09,-7.45
24000,1309.43,-4.32
25000,1309.43,-4.32
26000,1309.43,-4.32
27000,1309.43,-4.32
28000,1288.79,-1.19
29000,1383.08,-5.30
30000,1383.08,-5.30
31000,1383.08,-5.30
32000,1356.27,-2.22
33000,1356.27,-2.22
34000,1356.27,-2.22
35000,1242.59,-4.54
36000,1271.94,-6.32
37000,1271.94,-6.32
38000,1339.44,-4.92
39000,1339.44,-4.92
40000,1297.87,-1.49
41000,1297.87,-1.49
42000,1297.87,-1.49
43000,1297.87,-1.49
44000,1297.87,-1.49
45000,1223.77,0.39
46000,1297.28,-4.18
47000,1297.28,-4.18
48000,1297.28,-4.18
49000,1297.28,-4.18
50000,1316.31,0.59
51000,1316.31,0.59
52000,1316.31,0.59
53000,1219.18,-3.14
54000,1219.18,-3.14
55000,1219.18,-3.14
56000,1228.54,1.89
57000,1228.54,1.89
58000,1323.33,-2.46
59000,1323.33,-2.46
60000,1323.33,-2.46
61000,1382.93,0.10
62000,1294.36,-4.22
63000,1294.36,-4.22
64000,1231.68,-1.65
65000,1231.68,-1.65
66000,1279.75,1.01
67000,1279.75,1.01
68000,1279.75,1.01
69000,1196.87,-4.15
70000,1243.19,-1.23
71000,1243.19,-1.23
72000,1243.19,-1.23
73000,1243.19,-1.23
74000,1180.46,0.79
75000,1217.41,3.64
76000,1217.41,3.64
77000,1150.59,-1.67
78000,1150.59,-1.67
79000,1150.59,-1.67
80000,1186.24,1.51
81000,1186.24,1.51
82000,1186.24,1.51
83000,1186.24,1.51
84000,1186.24,1.51
85000,1156.47,-1.54
86000,1156.47,-1.54
87000,1156.47,-1.54
88000,1156.47,-1.54
89000,1156.47,-1.54
90000,1187.25,2.20
91000,1187.25,2.20
92000,1187.25,2.20
93000,1137.30,-5.10
94000,1137.30,-5.10
95000,1160.87,-1.55
96000,1160.87,-1.55
97000,1084.47,-0.43
98000,1084.47,-0.43
99000,1101.70,3.32
100000,1182.07,2.46"""

df = pd.read_csv(io.StringIO(dados_brutos))

# ======================================================
# CÁLCULO DA CURVA DE TENDÊNCIA MATEMÁTICA
# ======================================================
# O filtro Savitzky-Golay elimina o dente de serra gerando uma resposta limpa semelhante ao teórico
window_size = 19  # Ajusta a largura de suavização (deve ser ímpar)
poly_order = 2   # Ordem do polinômio de ajuste

df['Tendencia_Magnitude'] = savgol_filter(df['Magnitude_Ohm'], window_size, poly_order)
df['Tendencia_Fase'] = savgol_filter(df['Fase_Graus'], window_size, poly_order)

# ======================================================
# EMISSÃO E EXPORTAÇÃO DOS VALORES DE TENDÊNCIA
# ======================================================
df_exportar = df[['Freq(Hz)', 'Tendencia_Magnitude', 'Tendencia_Fase']].copy()
df_exportar.columns = ['Frequencia(Hz)', 'Magnitude_Tendencia(Ohm)', 'Fase_Tendencia(°)']

# Salva em arquivo CSV
df_exportar.to_csv("dados_tendencia_bode.csv", index=False, encoding='utf-8')

# Exibe no terminal a tabela limpa para conferência
print("\n" + "="*60)
print("     VALORES CALCULADOS DA CURVA DE TENDÊNCIA (BODE) ")
print("="*60)
print(df_exportar.to_string(index=False, formatters={
    'Frequencia(Hz)': '{:,.0f}'.format,
    'Magnitude_Tendencia(Ohm)': '{:.2f}'.format,
    'Fase_Tendencia(°)': '{:.2f}'.format
}))
print("="*60)
print("✅ Arquivo 'dados_tendencia_bode.csv' gerado com sucesso!")

# ======================================================
# PLOTAGEM GRÁFICA PARA COMPARAÇÃO VISUAL
# ======================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
fig.patch.set_facecolor('#f4f4f4')

# Gráfico 1: Magnitude com Tendência
ax1.plot(df['Freq(Hz)'], df['Magnitude_Ohm'], color='#95a5a6', alpha=0.5, label='Bancada Bruto (Dente de Serra)')
ax1.plot(df['Freq(Hz)'], df['Tendencia_Magnitude'], color='#0066cc', linewidth=2.5, label='Curva de Tendência Suave')
ax1.set_title("Bode de Teste - Magnitude", fontsize=12, fontweight='bold')
ax1.set_xlabel("Frequência (Hz)")
ax1.set_ylabel("Magnitude |Z| (Ω)")
ax1.grid(True, which="both", ls="--")
ax1.legend()

# Gráfico 2: Fase com Tendência
ax2.plot(df['Freq(Hz)'], df['Fase_Graus'], color='#e74c3c', alpha=0.4, label='Bancada Bruto')
ax2.plot(df['Freq(Hz)'], df['Tendencia_Fase'], color='#990000', linewidth=2.5, label='Curva de Tendência Suave')
ax2.set_title("Bode de Teste - Fase", fontsize=12, fontweight='bold')
ax2.set_xlabel("Frequência (Hz)")
ax2.set_ylabel("Fase (°)")
ax2.set_ylim(-15, 5)
ax2.grid(True, which="both", ls="--")
ax2.legend()

plt.tight_layout()
plt.show()
