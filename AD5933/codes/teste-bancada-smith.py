import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import io
import skrf as rf
from scipy.signal import savgol_filter

# ======================================================
# LEITURA DOS DADOS COPIADOS DA BANCADA
# ======================================================
dados_bancada = """Freq(Hz),Impedancia(Ohm),Fase(°)
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
14000,1478.11,-5.90
15000,1496.81,-7.57
16000,1496.81,-7.57
17000,1496.81,-7.57
18000,1426.15,-4.24
19000,1426.15,-4.24
20000,1426.15,-4.24
21000,1444.54,-5.84
22000,1444.54,-5.84
23000,1326.09,-7.45
24000,1326.09,-7.45
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
35000,1356.27,-2.22
36000,1213.85,-1.40
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
53000,1316.31,0.59
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
73000,1180.46,0.79
74000,1180.46,0.79
75000,1180.46,0.79
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
95000,1084.47,-0.43
96000,1084.47,-0.43
97000,1160.87,-1.55
98000,1084.47,-0.43
99000,1101.70,3.32
100000,1182.07,2.46"""

df = pd.read_csv(io.StringIO(dados_bancada))

# ======================================================
# PROCESSAMENTO DOS DADOS DE IMPEDÂNCIA COMPLEXA
# ======================================================
fase_rad = np.radians(df['Fase(°)'])

# Z = R + jX 
# Convertido explicitamente para array NumPy (.to_numpy()) para evitar AttributeError no Pandas
z_complexo = (df['Impedancia(Ohm)'] * np.cos(fase_rad) + 1j * (df['Impedancia(Ohm)'] * np.sin(fase_rad))).to_numpy()

# Suavização com o filtro Savitzky-Golay utilizando as propriedades do array NumPy (.real e .imag)
z_real_suave = savgol_filter(z_complexo.real, window_length=15, polyorder=2)
z_imag_suave = savgol_filter(z_complexo.imag, window_length=15, polyorder=2)
z_suave = z_real_suave + 1j * z_imag_suave

# ======================================================
# CONFIGURAÇÃO DA IMPEDÂNCIA DE REFERÊNCIA (Z0)
# ======================================================
Z0 = 2160.0  

# Definição do vetor de frequência para a estrutura de redes do scikit-rf
freq = rf.Frequency(start=1000, stop=100000, npoints=len(df), unit='hz')
net_bruta = rf.Network(frequency=freq, z=z_complexo.reshape(-1, 1, 1), z0=Z0)
net_suave = rf.Network(frequency=freq, z=z_suave.reshape(-1, 1, 1), z0=Z0)

# ======================================================
# PLOTAGEM DO DIAGRAMA DE SMITH
# ======================================================
# ======================================================
# PLOTAGEM DO DIAGRAMA DE SMITH
# ======================================================
plt.figure(figsize=(8, 8))
ax = plt.subplot(111)

# Renderiza as linhas guia da Carta de Smith (parâmetros extras removidos)
rf.plotting.smith(ax=ax, draw_labels=True)

# Definição correta dos labels usando o padrão do matplotlib
ax.set_xlabel('Componente Real')
ax.set_ylabel('Componente Imaginário')

# Plota os coeficientes de reflexão parciais (pontos brutos de bancada)
ax.scatter(net_bruta.s[:, 0, 0].real, net_bruta.s[:, 0, 0].imag, 
           color='#cc3333', alpha=0.5, s=15, label='Medido (Bancada)')

# Plota a curva contínua suavizada (linha de tendência)
ax.plot(net_suave.s[:, 0, 0].real, net_suave.s[:, 0, 0].imag, 
        color='#003399', linewidth=2.5, label='Curva de Tendência')

# Destaca geometricamente os extremos geométricos do Sweep (1 kHz a 100 kHz)
ax.scatter(net_suave.s[0, 0, 0].real, net_suave.s[0, 0, 0].imag, color='green', s=60, zorder=5, label='Início (1 kHz)')
ax.scatter(net_suave.s[-1, 0, 0].real, net_suave.s[-1, 0, 0].imag, color='black', s=60, zorder=5, label='Fim (100 kHz)')

# Título e legenda
plt.title(rf"Carta de Smith - Resposta da Bancada (Normalizado para $Z_0$ = {Z0} $\Omega$)", fontsize=12, fontweight='bold', pad=20)
plt.legend(loc='upper left')
plt.tight_layout()
plt.show()