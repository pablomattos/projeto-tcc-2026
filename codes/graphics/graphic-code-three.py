import serial
import serial.tools.list_ports
import csv
import time
from datetime import datetime
from pathlib import Path
import signal
import numpy as np

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


class AD5933BodeRealtime:
    def __init__(self):
        script_dir = Path(__file__).parent.absolute()
        self.csv_file = script_dir / f"AD5933_Bode_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"

        print(f"📁 Script está em: {script_dir}")
        print(f"💾 CSV será salvo: {self.csv_file}")

        self.buffer = []
        self.last_save = time.time()
        self.save_interval = 60
        self.running = False
        self.ser = None

        self.freq_data = {}
        self.last_freq_received = None
        self.last_mean_impedance = None

        signal.signal(signal.SIGINT, self.signal_handler)

        self.fig = plt.figure(figsize=(14, 8))
        gs = self.fig.add_gridspec(2, 2, width_ratios=[1.2, 1.0])

        self.ax_mag = self.fig.add_subplot(gs[0, 0])
        self.ax_phase = self.fig.add_subplot(gs[1, 0], sharex=self.ax_mag)
        self.ax_nyq = self.fig.add_subplot(gs[:, 1])

        self.fig.suptitle("AD5933 - Bode e Nyquist em Tempo Real")

        self.line_mag_raw, = self.ax_mag.semilogx(
            [], [], color="lightsteelblue", linewidth=1.0, alpha=0.5, label="|Z| bruto"
        )
        self.line_mag_smooth, = self.ax_mag.semilogx(
            [], [], "b-", linewidth=1.8, marker="o", markersize=2.5, label="|Z| médio"
        )

        self.line_phase_raw, = self.ax_phase.semilogx(
            [], [], color="mistyrose", linewidth=1.0, alpha=0.5, label="Fase bruta"
        )
        self.line_phase_smooth, = self.ax_phase.semilogx(
            [], [], "r-", linewidth=1.8, marker="o", markersize=2.5, label="Fase média"
        )

        self.line_nyq_raw, = self.ax_nyq.plot(
            [], [], color="lightgray", linewidth=1.0, alpha=0.8, marker=".", markersize=3,
            label="Nyquist bruto"
        )
        self.line_nyq_smooth, = self.ax_nyq.plot(
            [], [], "g-", linewidth=1.8, marker="o", markersize=3, label="Nyquist suavizado"
        )
        self.point_nyq_last, = self.ax_nyq.plot(
            [], [], "ro", markersize=6, label="Último ponto"
        )

        self.ax_mag.set_ylabel("Impedância (Ohm)")
        self.ax_phase.set_ylabel("Fase (°)")
        self.ax_phase.set_xlabel("Frequência (Hz)")

        self.ax_nyq.set_xlabel("Re(Z) [Ohm]")
        self.ax_nyq.set_ylabel("-Im(Z) [Ohm]")
        self.ax_nyq.set_title("Nyquist")
        self.ax_nyq.axis("equal")

        self.ax_mag.grid(True, which="both", ls="--", alpha=0.4)
        self.ax_phase.grid(True, which="both", ls="--", alpha=0.4)
        self.ax_nyq.grid(True, which="both", ls="--", alpha=0.4)

        self.ax_mag.legend(loc="upper left")
        self.ax_phase.legend(loc="upper left")
        self.ax_nyq.legend(loc="best")

        self.status_text = self.fig.text(0.01, 0.985, "Aguardando dados...", fontsize=10, va="top")

    def signal_handler(self, sig, frame):
        print("\n⏹️ Parando...")
        self.running = False

    def find_esp32(self):
        ports = serial.tools.list_ports.comports()
        print("\n📡 Portas encontradas:")

        for port in ports:
            print(f"  {port.device}: {port.description}")
            desc = (port.description or "").lower()
            if any(x in desc for x in ["ch340", "cp210", "silicon", "usb serial", "uart"]):
                print(f"✅ ESP32: {port.device}")
                return port.device
        return None

    def connect(self):
        port = self.find_esp32()
        if not port:
            print("❌ ESP32 não encontrado! Conecte e tente novamente.")
            return False

        try:
            self.ser = serial.Serial(port, 115200, timeout=0.05)
            print(f"\n✅ Conectado: {port}")
            time.sleep(3)
            self.ser.reset_input_buffer()
            return True
        except Exception as e:
            print(f"❌ Erro: {e}")
            return False

    def smooth_series(self, values, window=9):
        if len(values) < 3:
            return values[:]

        if window < 3:
            return values[:]

        if len(values) < window:
            window = len(values) if len(values) % 2 == 1 else len(values) - 1
            if window < 3:
                return values[:]

        half = window // 2
        smoothed = []

        for i in range(len(values)):
            start = max(0, i - half)
            end = min(len(values), i + half + 1)
            local = values[start:end]
            smoothed.append(sum(local) / len(local))

        return smoothed

    def parse_line(self, line):
        line = line.strip()

        if not line:
            return None, None

        if line.startswith("MEDIA_IMPEDANCIA"):
            parts = line.split(",")
            if len(parts) >= 2:
                try:
                    return "mean", float(parts[1].split()[0])
                except ValueError:
                    return "mean", None
            return "mean", None

        if "," not in line:
            return None, None

        if any(x in line for x in ["Freq(Hz)", "Gain", "CALIBRA", "PRONTO", "TIMEOUT"]):
            return None, None

        parts = line.split(",")
        if len(parts) < 6:
            return None, None

        try:
            data = {
                "freq": int(float(parts[0])),
                "imp_avg": float(parts[1]),
                "phase_avg": float(parts[2]),
                "real_avg": float(parts[3]),
                "imag_avg": float(parts[4]),
                "mag_avg": float(parts[5]),
            }
            return "data", data
        except ValueError:
            return None, None

    def save_csv(self):
        if not self.buffer:
            return

        file_exists = self.csv_file.exists()

        with open(self.csv_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            if not file_exists:
                writer.writerow([
                    "Timestamp",
                    "Freq(Hz)",
                    "Imp_AVG(Ohm)",
                    "Fase_AVG(°)",
                    "Real_AVG(Ohm)",
                    "Imag_AVG(Ohm)",
                    "Mag_AVG"
                ])

            for row in self.buffer:
                writer.writerow(row)

        print(f"💾 Salvo {len(self.buffer)} linhas → {self.csv_file.name}")
        self.buffer.clear()

    def read_serial_non_blocking(self):
        if not self.ser or not self.ser.is_open:
            return

        while self.ser.in_waiting > 0:
            try:
                line = self.ser.readline().decode("utf-8", errors="ignore").rstrip()
                line_type, payload = self.parse_line(line)

                if line_type == "mean":
                    self.last_mean_impedance = payload
                    if payload is not None:
                        print(f"📈 Média da impedância: {payload:.3f} Ohm")

                elif line_type == "data":
                    data = payload
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

                    self.freq_data[data["freq"]] = data
                    self.last_freq_received = data["freq"]

                    self.buffer.append([
                        now,
                        data["freq"],
                        data["imp_avg"],
                        data["phase_avg"],
                        data["real_avg"],
                        data["imag_avg"],
                        data["mag_avg"],
                    ])

                    print(
                        f"📡 {data['freq']:6d} Hz | "
                        f"|Z|={data['imp_avg']:8.2f} Ω | "
                        f"φ={data['phase_avg']:7.2f}°"
                    )

            except Exception:
                break

    def update_plot(self, frame):
        if not self.running:
            return (
                self.line_mag_raw,
                self.line_mag_smooth,
                self.line_phase_raw,
                self.line_phase_smooth,
                self.line_nyq_raw,
                self.line_nyq_smooth,
                self.point_nyq_last,
            )

        self.read_serial_non_blocking()

        if self.freq_data:
            freqs = sorted(self.freq_data.keys())

            imp_vals = [self.freq_data[f]["imp_avg"] for f in freqs]
            phase_vals = [self.freq_data[f]["phase_avg"] for f in freqs]  # em graus

            # Smoothed
            imp_smooth = self.smooth_series(imp_vals, window=9)
            phase_smooth = self.smooth_series(phase_vals, window=7)

            # Converte fase para radianos
            phase_rad = [p * 3.14159265359 / 180.0 for p in phase_vals]
            phase_smooth_rad = [p * 3.14159265359 / 180.0 for p in phase_smooth]

            # Calcula Z = |Z| * e^{j phi} -> Re(Z) e Im(Z)
            real_vals = [imp_vals[i] * np.cos(phase_rad[i]) for i in range(len(freqs))]
            imag_vals = [imp_vals[i] * np.sin(phase_rad[i]) for i in range(len(freqs))]

            real_smooth = [imp_smooth[i] * np.cos(phase_smooth_rad[i]) for i in range(len(freqs))]
            imag_smooth = [imp_smooth[i] * np.sin(phase_smooth_rad[i]) for i in range(len(freqs))]

            # Nyquist: X = Re(Z), Y = -Im(Z)
            nyq_x_raw = real_vals
            nyq_y_raw = [-v for v in imag_vals]

            nyq_x_smooth = real_smooth
            nyq_y_smooth = [-v for v in imag_smooth]

            # update Bode
            self.line_mag_raw.set_data(freqs, imp_vals)
            self.line_mag_smooth.set_data(freqs, imp_smooth)

            self.line_phase_raw.set_data(freqs, phase_vals)
            self.line_phase_smooth.set_data(freqs, phase_smooth)

            # update Nyquist
            self.line_nyq_raw.set_data(nyq_x_raw, nyq_y_raw)
            self.line_nyq_smooth.set_data(nyq_x_smooth, nyq_y_smooth)
            self.point_nyq_last.set_data([nyq_x_raw[-1]], [nyq_y_raw[-1]])
            # Atualiza escalas
            self.ax_mag.relim()
            self.ax_mag.autoscale_view()

            self.ax_phase.relim()
            self.ax_phase.autoscale_view()

            self.ax_nyq.relim()
            self.ax_nyq.autoscale_view()

        if time.time() - self.last_save >= self.save_interval:
            self.save_csv()
            self.last_save = time.time()

        return (
            self.line_mag_raw,
            self.line_mag_smooth,
            self.line_phase_raw,
            self.line_phase_smooth,
            self.line_nyq_raw,
            self.line_nyq_smooth,
            self.point_nyq_last,
        )

    def start(self):
        if not self.connect():
            return

        self.running = True
        self.last_save = time.time()

        print("\n🚀 BODE + NYQUIST EM TEMPO REAL")
        print("📊 Curvas brutas + suavizadas | Ctrl+C para parar")
        print("-" * 70)

        self.ani = FuncAnimation(
            self.fig,
            self.update_plot,
            interval=100,
            blit=False,
            cache_frame_data=False
        )

        try:
            plt.tight_layout(rect=[0, 0, 1, 0.96])
            plt.show()
        finally:
            self.running = False

            if self.buffer:
                self.save_csv()

            if self.ser and self.ser.is_open:
                self.ser.close()

            print(f"\n✅ FINALIZADO! CSV: {self.csv_file}")


if __name__ == "__main__":
    app = AD5933BodeRealtime()
    app.start()