import serial
import serial.tools.list_ports
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# ==========================================================
# CLASSE PRINCIPAL
# ==========================================================

class AD5933RealtimeBode:

    def __init__(self):

        self.ser = None
        self.running = False

        # ==================================================
        # DICIONÁRIO DAS FREQUÊNCIAS
        # ==================================================

        self.freq_data = {}

        # ==================================================
        # FIGURA
        # ==================================================

        self.fig = plt.figure(figsize=(14, 8))

        gs = self.fig.add_gridspec(
            2,
            2,
            width_ratios=[1.2, 1]
        )

        self.ax_mag = self.fig.add_subplot(gs[0, 0])
        self.ax_phase = self.fig.add_subplot(gs[1, 0])
        self.ax_nyquist = self.fig.add_subplot(gs[:, 1])

        self.fig.suptitle(
            "AD5933 - Bode + Nyquist em Tempo Real"
        )

        # ==================================================
        # LIMITES FIXOS DO EIXO X
        # ==================================================

        self.ax_mag.set_xlim(10000, 100000)
        self.ax_phase.set_xlim(10000, 100000)

        # ==================================================
        # LINHAS BODE
        # ==================================================

        self.line_mag_raw, = self.ax_mag.semilogx(
            [],
            [],
            color="lightsteelblue",
            linewidth=1.0,
            alpha=0.5,
            label="|Z| bruto"
        )

        self.line_mag_smooth, = self.ax_mag.semilogx(
            [],
            [],
            "b-",
            linewidth=1.8,
            marker="o",
            markersize=3,
            label="|Z| suavizado"
        )

        self.line_phase_raw, = self.ax_phase.semilogx(
            [],
            [],
            color="mistyrose",
            linewidth=1.0,
            alpha=0.5,
            label="Fase bruta"
        )

        self.line_phase_smooth, = self.ax_phase.semilogx(
            [],
            [],
            "r-",
            linewidth=1.8,
            marker="o",
            markersize=3,
            label="Fase suavizada"
        )

        # ==================================================
        # LINHAS NYQUIST
        # ==================================================

        self.line_nyquist_raw, = self.ax_nyquist.plot(
            [],
            [],
            color="lightgreen",
            linewidth=1.0,
            alpha=0.5,
            marker=".",
            label="Nyquist bruto"
        )

        self.line_nyquist_smooth, = self.ax_nyquist.plot(
            [],
            [],
            "g-",
            linewidth=2,
            marker="o",
            markersize=4,
            label="Nyquist suavizado"
        )

        # ==================================================
        # CONFIG EIXOS BODE
        # ==================================================

        self.ax_mag.set_ylabel("Impedância (Ohm)")
        self.ax_phase.set_ylabel("Fase (°)")
        self.ax_phase.set_xlabel("Frequência (Hz)")

        self.ax_mag.grid(True, which="both", ls="--", alpha=0.4)
        self.ax_phase.grid(True, which="both", ls="--", alpha=0.4)

        self.ax_mag.legend(loc="upper left")
        self.ax_phase.legend(loc="upper left")

        # ==================================================
        # CONFIG NYQUIST
        # ==================================================

        self.ax_nyquist.set_title("Diagrama de Nyquist")
        self.ax_nyquist.set_xlabel("Zreal (Ohm)")
        self.ax_nyquist.set_ylabel("-Zimag (Ohm)")

        # DESATIVA INDICAÇÕES DE OFFSET CONFUSAS NOS EIXOS DO NYQUIST
        self.ax_nyquist.get_xaxis().get_major_formatter().set_useOffset(False)
        self.ax_nyquist.get_yaxis().get_major_formatter().set_useOffset(False)

        self.ax_nyquist.grid(
            True,
            ls="--",
            alpha=0.4
        )

        self.ax_nyquist.legend(loc="upper right")
        self.ax_nyquist.axis("equal")

    # ======================================================
    # DETECTA ESP32
    # ======================================================

    def find_esp32(self):

        ports = serial.tools.list_ports.comports()
        print("\n📡 Portas encontradas:")

        for port in ports:
            print(f"{port.device} -> {port.description}")
            desc = (port.description or "").lower()

            if any(
                x in desc
                for x in [
                    "ch340",
                    "cp210",
                    "silicon",
                    "usb serial",
                    "uart"
                ]
            ):
                print(f"\n✅ ESP32 encontrado: {port.device}")
                return port.device

        return None

    # ======================================================
    # CONECTA SERIAL
    # ======================================================

    def connect(self):

        port = self.find_esp32()

        if not port:
            print("❌ ESP32 não encontrado")
            return False

        try:
            self.ser = serial.Serial(
                port,
                115200,
                timeout=0.05
            )
            print(f"\n✅ Conectado em {port}")
            return True

        except Exception as e:
            print("❌ Erro:", e)
            return False

    # ======================================================
    # SUAVIZAÇÃO
    # ======================================================

    def smooth_series(self, values, window=7):

        if len(values) < 3:
            return values[:]

        if len(values) < window:
            window = len(values)
            if window % 2 == 0:
                window -= 1

        if window < 3:
            return values[:]

        half = window // 2
        smooth = []

        for i in range(len(values)):
            start = max(0, i - half)
            end = min(len(values), i + half + 1)
            local = values[start:end]
            smooth.append(
                sum(local) / len(local)
            )

        return smooth

    # ======================================================
    # LEITURA SERIAL
    # ======================================================

    def read_serial(self):

        while self.ser.in_waiting > 0:
            try:
                line = (
                    self.ser.readline()
                    .decode("utf-8", errors="ignore")
                    .strip()
                )

                # ==========================================
                # NOVA VARREDURA
                # ==========================================

                if "Freq(Hz)" in line:
                    print("\n======================")
                    print("Nova varredura")
                    print("======================")
                    continue

                # ==========================================
                # IGNORA MENSAGENS E CALIBRAÇÕES
                # ==========================================

                if (
                    line == "" or
                    "CAL" in line or
                    "Calibração" in line or
                    "Nova" in line or
                    "===" in line or
                    "🚀" in line or
                    "🎯" in line or
                    "✅" in line or
                    "❌" in line
                ):
                    continue

                # ==========================================
                # CSV
                # ==========================================

                parts = line.split(",")
                if len(parts) != 3:
                    continue

                # Validação contra strings de texto residuais
                try:
                    freq = float(parts[0])
                except ValueError:
                    continue

                impedance = float(parts[1])
                phase_deg = float(parts[2])

                # ==========================================
                # ZREAL / ZIMAG
                # ==========================================

                phase_rad = np.radians(phase_deg)
                z_real = impedance * np.cos(phase_rad)
                z_imag = impedance * np.sin(phase_rad)

                # ==========================================
                # SUBSTITUI DADOS DA FREQUÊNCIA
                # ==========================================

                self.freq_data[freq] = {
                    "impedance": impedance,
                    "phase": phase_deg,
                    "z_real": z_real,
                    "z_imag": z_imag
                }

                print(
                    f"{freq:7.0f} Hz | "
                    f"|Z|={impedance:8.2f} Ω | "
                    f"φ={phase_deg:7.2f}° | "
                    f"Zr={z_real:8.2f} Ω | "
                    f"Zi={z_imag:8.2f} Ω"
                )

            except Exception as e:
                print("Erro na leitura serial:", e)

    # ======================================================
    # UPDATE PLOT
    # ======================================================

    def update_plot(self, frame):

        self.read_serial()

        if self.freq_data:

            freqs = sorted(self.freq_data.keys())

            imp_vals = [
                self.freq_data[f]["impedance"]
                for f in freqs
            ]

            phase_vals = [
                self.freq_data[f]["phase"]
                for f in freqs
            ]

            z_real_vals = [
                self.freq_data[f]["z_real"]
                for f in freqs
            ]

            # CORREÇÃO AQUI: Removeu-se o sinal negativo.
            # A inversão do eixo (-Zimag) se equilibra naturalmente com a fase do ESP32.
            z_imag_vals = [
                self.freq_data[f]["z_imag"]
                for f in freqs
            ]

            # ==============================================
            # SUAVIZAÇÃO
            # ==============================================

            imp_smooth = self.smooth_series(imp_vals, window=7)
            phase_smooth = self.smooth_series(phase_vals, window=7)
            z_real_smooth = self.smooth_series(z_real_vals, window=7)
            z_imag_smooth = self.smooth_series(z_imag_vals, window=7)

            # ==============================================
            # MAGNITUDE
            # ==============================================

            self.line_mag_raw.set_data(freqs, imp_vals)
            self.line_mag_smooth.set_data(freqs, imp_smooth)

            # ==============================================
            # FASE
            # ==============================================

            self.line_phase_raw.set_data(freqs, phase_vals)
            self.line_phase_smooth.set_data(freqs, phase_smooth)

            # ==============================================
            # NYQUIST
            # ==============================================

            self.line_nyquist_raw.set_data(z_real_vals, z_imag_vals)
            self.line_nyquist_smooth.set_data(z_real_smooth, z_imag_smooth)

            # ==============================================
            # AUTO SCALE
            # ==============================================

            self.ax_mag.relim()
            self.ax_mag.autoscale_view(scalex=False, scaley=True)

            self.ax_phase.relim()
            self.ax_phase.autoscale_view(scalex=False, scaley=True)

            self.ax_nyquist.relim()
            self.ax_nyquist.autoscale_view()

        return (
            self.line_mag_raw,
            self.line_mag_smooth,
            self.line_phase_raw,
            self.line_phase_smooth,
            self.line_nyquist_raw,
            self.line_nyquist_smooth
        )

    # ======================================================
    # START
    # ======================================================

    def start(self):

        if not self.connect():
            return

        self.running = True

        print("\n🚀 BODE + NYQUIST EM TEMPO REAL")
        print("-" * 60)

        ani = FuncAnimation(
            self.fig,
            self.update_plot,
            interval=100,
            blit=False,
            cache_frame_data=False
        )

        plt.tight_layout(
            rect=[0, 0, 1, 0.96]
        )

        plt.show()

# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":

    app = AD5933RealtimeBode()
    app.start()