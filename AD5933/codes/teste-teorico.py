import os
import csv
import numpy as np
import matplotlib.pyplot as plt

# ======================================================
# PARÂMETROS DO CIRCUITO (VALORES NOMINAIS)
# ======================================================
R1 = 1080.0  # Resistor em série (Ohm)
R2 = 1080.0  # Resistor do paralelo (Ohm)
C = 22e-9    # Capacitor do paralelo (Farad -> 22nF)

# Geração de frequências com intervalos lineares exatos de 1kHz (1000Hz a 100000Hz)
freqs = np.arange(1000, 101000, 1000)
w = 2 * np.pi * freqs  # Frequência angular (rad/s)

# ======================================================
# MODELAGEM MATEMÁTICA DA IMPEDÂNCIA COMPLEXA
# ======================================================
# Zp = R2 / (1 + j * w * R2 * C)
Z_paralelo = R2 / (1 + 1j * w * R2 * C)

# Z_total = R1 + Zp
Z_total = R1 + Z_paralelo

# Extração dos parâmetros estruturados
z_real = np.real(Z_total)
z_imag = np.imag(Z_total)
magnitude = np.abs(Z_total)
fase_graus = np.degrees(np.angle(Z_total))

# ======================================================
# SALVAMENTO DOS DADOS EM ARQUIVO CSV
# ======================================================
csv_filename = "simulacao_teorica_linear.csv"

with open(csv_filename, mode='w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    # Cabeçalho estruturado conforme solicitado anteriormente
    writer.writerow(["Frequencia_Hz", "Z_Real", "Z_Imaginario", "Fase_Graus", "Magnitude_Ohm"])
    
    # Grava linha por linha os passos de 1kHz
    for i in range(len(freqs)):
        writer.writerow([freqs[i], z_real[i], z_imag[i], fase_graus[i], magnitude[i]])

print(f"✅ Simulação linear concluída! Dados salvos em: {csv_filename}")

# ======================================================
# PLOTAGEM DOS GRÁFICOS TEÓRICOS
# ======================================================
fig = plt.figure(figsize=(15, 5))
fig.patch.set_facecolor('#f0f0f0')

# 1. Bode - Magnitude (Alterado para escala linear no eixo X para combinar com o passo)
ax_mag = fig.add_subplot(1, 3, 1)
ax_mag.plot(freqs, magnitude, color='#1f77b4', marker='o', markersize=3, linewidth=2, label='Teórico')
ax_mag.set_title("Bode Teórico - Magnitude (Linear)")
ax_mag.set_xlabel("Frequência (Hz)")
ax_mag.set_ylabel("Impedância (|Z| [Ω])")
ax_mag.grid(True, which="both", ls="--")
ax_mag.set_xlim(1000, 100000)
ax_mag.set_ylim(900, 2100)

# 2. Bode - Fase (Linear no eixo X)
ax_phase = fig.add_subplot(1, 3, 2)
ax_phase.plot(freqs, fase_graus, color='#ff7f0e', marker='o', markersize=3, linewidth=2, label='Teórico')
ax_phase.set_title("Bode Teórico - Fase (Linear)")
ax_phase.set_xlabel("Frequência (Hz)")
ax_phase.set_ylabel("Fase (φ [°])")
ax_phase.grid(True, which="both", ls="--")
ax_phase.set_xlim(1000, 100000)
ax_phase.set_ylim(-15, 5)

# 3. Diagrama de Nyquist
ax_nyquist = fig.add_subplot(1, 3, 3)
ax_nyquist.plot(z_real, -z_imag, color='#9467bd', marker='o', markersize=3, linewidth=2, label='Teórico')
ax_nyquist.set_title("Diagrama de Nyquist Teórico")
ax_nyquist.set_xlabel("Z' (Real [Ω])")
ax_nyquist.set_ylabel("-Z'' (Imaginário [Ω])")
ax_nyquist.grid(True, which="both", ls="--")

# Mantém a proporção 1:1 circular do plano complexo
ax_nyquist.set_aspect('equal', adjustable='datalim')

plt.tight_layout()
plt.show()