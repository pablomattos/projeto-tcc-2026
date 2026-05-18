import serial
import csv
import math
import os
import time
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# =========================
# CONFIGURAÇÕES
# =========================
SERIAL_PORT = "COM3"          # ajuste conforme seu PC
BAUDRATE = 115200
TIMEOUT = 0                   # leitura não bloqueante

FREQ_MIN = 10000
FREQ_MAX = 100000

CSV_FILE = "esp32_ad5933_tempo_real.csv"

# =========================
# PREPARAÇÃO DO CSV
# =========================
file_exists = os.path.isfile(CSV_FILE)

csv_file = open(CSV_FILE, mode="a", newline="", encoding="utf-8")
csv_writer = csv.writer(csv_file)

if not file_exists:
    csv_writer.writerow([
        "timestamp",
        "sweep_id",
        "frequency_hz",
        "impedance_ohm",
        "phase_deg",
        "z_real_ohm",
        "z_imag_ohm"
    ])
    csv_file.flush()

# =========================
# SERIAL
# =========================
ser = serial.Serial(
    port=SERIAL_PORT,
    baudrate=BAUDRATE,
    timeout=TIMEOUT,
    write_timeout=0
)
ser.reset_input_buffer()

# =========================
# ESTADO
# =========================
sweep_id = 0
freqs = []
mags = []
phases = []
serial_buffer = ""

# =========================
# GRÁFICO
# =========================
plt.ion()
fig, (ax_mag, ax_phase) = plt.subplots(2, 1, figsize=(10, 8))

def kilo_formatter(value, pos):
    if value >= 1000:
        return f"{value/1000:.0f}k" if value % 1000 == 0 else f"{value/1000:.1f}k"
    return f"{value:.0f}"

ax_mag.set_title("Bode em tempo real - varredura atual")
ax_mag.set_ylabel("|Z| (ohms)")
ax_mag.set_xscale("log")
ax_mag.set_xlim(FREQ_MIN, FREQ_MAX)
ax_mag.grid(True, which="both", ls="--", alpha=0.5)
ax_mag.yaxis.set_major_formatter(mticker.FuncFormatter(kilo_formatter))

ax_phase.set_xlabel("Frequência (Hz)")
ax_phase.set_ylabel("Fase (graus)")
ax_phase.set_xscale("log")
ax_phase.set_xlim(FREQ_MIN, FREQ_MAX)
ax_phase.grid(True, which="both", ls="--", alpha=0.5)

line_mag, = ax_mag.plot([], [], 'o-', color='blue', label='|Z|', markersize=4)
line_phase, = ax_phase.plot([], [], 'o-', color='red', label='Fase', markersize=4)

ax_mag.legend()
ax_phase.legend()

fig.tight_layout()
fig.canvas.draw()
fig.canvas.flush_events()

def nova_varredura():
    global freqs, mags, phases
    freqs = []
    mags = []
    phases = []

    line_mag.set_data([], [])
    line_phase.set_data([], [])

    ax_mag.relim()
    ax_mag.autoscale_view(scaley=True)
    ax_phase.relim()
    ax_phase.autoscale_view(scaley=True)

def processar_linha(line):
    global sweep_id, freqs, mags, phases

    line = line.strip()
    if not line:
        return

    print(line)

    if "INICIANDO VARREDURA" in line:
        sweep_id += 1
        nova_varredura()
        return

    if line.startswith("✅") or line.startswith("🔄") or line.startswith("💾") or line.startswith("🎯"):
        return

    parts = line.split(",")
    if len(parts) != 3:
        return

    try:
        freq = float(parts[0])
        impedance = float(parts[1])
        phase_deg = float(parts[2])
    except ValueError:
        return

    if not (FREQ_MIN <= freq <= FREQ_MAX):
        return

    phase_rad = math.radians(phase_deg)
    z_real = impedance * math.cos(phase_rad)
    z_imag = impedance * math.sin(phase_rad)

    timestamp = datetime.now().isoformat(timespec="milliseconds")
    csv_writer.writerow([
        timestamp,
        sweep_id,
        freq,
        impedance,
        phase_deg,
        z_real,
        z_imag
    ])

    if len(freqs) % 5 == 0:
        csv_file.flush()

    freqs.append(freq)
    mags.append(impedance)
    phases.append(phase_deg)

    dados_ordenados = sorted(zip(freqs, mags, phases), key=lambda x: x[0])
    f_plot = [x[0] for x in dados_ordenados]
    z_plot = [x[1] for x in dados_ordenados]
    p_plot = [x[2] for x in dados_ordenados]

    line_mag.set_data(f_plot, z_plot)
    line_phase.set_data(f_plot, p_plot)

    ax_mag.relim()
    ax_mag.autoscale_view(scaley=True)

    ax_phase.relim()
    ax_phase.autoscale_view(scaley=True)

    ax_mag.yaxis.set_major_formatter(mticker.FuncFormatter(kilo_formatter))

    fig.canvas.draw_idle()
    fig.canvas.flush_events()

print("Aguardando dados do ESP32...")

try:
    ultimo_update = time.perf_counter()

    while True:
        waiting = ser.in_waiting
        if waiting > 0:
            chunk = ser.read(waiting).decode("utf-8", errors="ignore")
            serial_buffer += chunk

            while "\n" in serial_buffer:
                line, serial_buffer = serial_buffer.split("\n", 1)
                processar_linha(line)

        agora = time.perf_counter()
        if agora - ultimo_update >= 0.02:   # ~50 FPS de atualização visual
            plt.pause(0.001)
            ultimo_update = agora

        time.sleep(0.001)

except KeyboardInterrupt:
    print("\nEncerrando...")

finally:
    csv_file.flush()
    ser.close()
    csv_file.close()
    plt.ioff()
    plt.show()