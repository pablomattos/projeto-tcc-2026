import csv
import math
from pathlib import Path
import signal
import time
from datetime import datetime

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import serial
import serial.tools.list_ports


class AD5933BodeRealtime:

  def __init__(self):
    script_dir = Path(__file__).parent.absolute()
    self.csv_file = (
        script_dir
        / f"AD5933_Bode_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    )

    print(f"📁 Direitório de execução: {script_dir}")
    print(f"💾 Arquivo CSV de saída: {self.csv_file}")

    self.buffer = []
    self.last_save = time.time()
    self.save_interval = 15  # Salva o buffer no CSV a cada 15 segundos
    self.running = False
    self.ser = None

    self.freq_data = {}
    self.last_freq_received = None
    self.last_mean_impedance = None
    self.sweep_id = 1

    signal.signal(signal.SIGINT, self.signal_handler)

    # Configuração dos Gráficos Matplotlib
    self.fig, (self.ax_mag, self.ax_phase) = plt.subplots(
        2, 1, figsize=(12, 8), sharex=True
    )
    self.fig.suptitle("AD5933 + ESP32 - Diagrama de Bode em Tempo Real")

    (self.line_mag_raw,) = self.ax_mag.semilogx(
        [],
        [],
        color="lightsteelblue",
        linewidth=1.0,
        alpha=0.6,
        label="|Z| bruto",
    )
    (self.line_mag_smooth,) = self.ax_mag.semilogx(
        [],
        [],
        "b-",
        linewidth=1.8,
        marker="o",
        markersize=2.5,
        label="|Z| médio",
    )

    (self.line_phase_raw,) = self.ax_phase.semilogx(
        [],
        [],
        color="mistyrose",
        linewidth=1.0,
        alpha=0.6,
        label="Fase bruta",
    )
    (self.line_phase_smooth,) = self.ax_phase.semilogx(
        [],
        [],
        "r-",
        linewidth=1.8,
        marker="o",
        markersize=2.5,
        label="Fase média",
    )

    self.ax_mag.set_ylabel("Impedância (Ω)")
    self.ax_phase.set_ylabel("Fase (°)")
    self.ax_phase.set_xlabel("Frequência (Hz)")

    self.ax_mag.grid(True, which="both", ls="--", alpha=0.4)
    self.ax_phase.grid(True, which="both", ls="--", alpha=0.4)

    self.ax_mag.legend(loc="upper left")
    self.ax_phase.legend(loc="upper left")

    self.status_text = self.fig.text(
        0.01, 0.985, "Aguardando conexão com ESP32...", fontsize=10, va="top"
    )

  def signal_handler(self, sig, frame):
    print("\n⏹️ Parando execução...")
    self.running = False

  def find_esp32(self):
    """Busca automaticamente a porta COM associada ao ESP32."""
    ports = serial.tools.list_ports.comports()
    print("\n📡 Analisando portas seriais disponíveis:")

    for port in ports:
      print(f"  ➜ {port.device}: {port.description}")
      desc = (port.description or "").lower()
      if any(
          x in desc
          for x in [
              "ch340",
              "cp210",
              "silicon",
              "usb serial",
              "uart",
              "esp32",
              "ftdi",
          ]
      ):
        print(f"✅ Dispositivo ESP32 identificado em: {port.device}")
        return port.device

    # Se não encontrar por palavra-chave, mas houver apenas 1 porta conectada
    if len(ports) == 1:
      print(f"⚠️ Nenhuma correspondência exata, selecionando {ports[0].device}")
      return ports[0].device

    return None

  def connect(self):
    port = self.find_esp32()
    if not port:
      print("❌ ESP32 não encontrado! Verifique a conexão USB.")
      return False

    try:
      self.ser = serial.Serial(port, 115200, timeout=0.05)
      print(f"✅ Conectado com sucesso na porta {port} (115200 baud)")
      time.sleep(2)  # Aguarda estabilização do DTR/RTS do ESP32
      self.ser.reset_input_buffer()
      return True
    except Exception as e:
      print(f"❌ Erro ao abrir a porta serial: {e}")
      return False

  def smooth_series(self, values, window=5):
    """Aplica média móvel aos dados para suavização visual."""
    if len(values) < 3:
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
    """Processa cada linha vinda da serial do ESP32."""
    line = line.strip()

    if not line:
      return None, None

    # Detecta eventos de reinício/início de varredura
    if any(
        kw in line.upper()
        for kw in ["INICIANDO VARREDURA", "NOVA VARREDURA", "SWEEP_START"]
    ):
      return "new_sweep", None

    # Detecta mensagens de média de impedância enviadas pelo microcontrolador
    if "MEDIA_IMPEDANCIA" in line or "IMPEDANCIA MEDIA" in line.upper():
      try:
        parts = line.split(":") if ":" in line else line.split(",")
        val_str = parts[1].replace("Ohm", "").strip().split()[0]
        return "mean", float(val_str)
      except (IndexError, ValueError):
        return "mean", None

    # Descarta cabeçalhos e textos informativos gerais
    if any(
        kw in line
        for kw in ["Freq(Hz)", "Gain", "CALIBRA", "PRONTO", "TIMEOUT", "=="]
    ):
      return None, None

    if "," not in line:
      return None, None

    parts = line.split(",")

    # Formato simplificado enviado por muitos sketches ESP32: Freq, Impedancia, Fase
    if len(parts) == 3:
      try:
        freq = int(float(parts[0]))
        imp = float(parts[1])
        phase = float(parts[2])

        # Calcula as componentes real/imaginária a partir do módulo e fase
        rad = math.radians(phase)
        real = imp * math.cos(rad)
        imag = imp * math.sin(rad)

        data = {
            "freq": freq,
            "imp_avg": imp,
            "phase_avg": phase,
            "real_avg": real,
            "imag_avg": imag,
            "mag_avg": imp,
        }
        return "data", data
      except ValueError:
        return None, None

    # Formato estendido de 6 parâmetros
    if len(parts) >= 6:
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
            "Sweep_ID",
            "Freq(Hz)",
            "Imp_AVG(Ohm)",
            "Fase_AVG(°)",
            "Real_AVG(Ohm)",
            "Imag_AVG(Ohm)",
            "Mag_AVG",
        ])

      for row in self.buffer:
        writer.writerow(row)

    print(f"💾 {len(self.buffer)} novos registros salvos em → {self.csv_file.name}")
    self.buffer.clear()

  def read_serial_non_blocking(self):
    if not self.ser or not self.ser.is_open:
      return

    while self.ser.in_waiting > 0:
      try:
        line = self.ser.readline().decode("utf-8", errors="ignore").rstrip()
        line_type, payload = self.parse_line(line)

        if line_type == "new_sweep":
          self.sweep_id += 1
          self.freq_data.clear()  # Limpa a tela para a nova varredura
          print(f"\n🔄 Iniciando Varredura #{self.sweep_id}")

        elif line_type == "mean":
          self.last_mean_impedance = payload
          if payload is not None:
            print(f"📈 Impedância Média da Varredura: {payload:.2f} Ω")

        elif line_type == "data":
          data = payload
          now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

          self.freq_data[data["freq"]] = data
          self.last_freq_received = data["freq"]

          self.buffer.append([
              now,
              self.sweep_id,
              data["freq"],
              data["imp_avg"],
              data["phase_avg"],
              data["real_avg"],
              data["imag_avg"],
              data["mag_avg"],
          ])

          print(
              f"📡 [{self.sweep_id}] {data['freq']:6d} Hz | "
              f"|Z|={data['imp_avg']:8.2f} Ω | "
              f"φ={data['phase_avg']:7.2f}°"
          )

      except Exception as e:
        print(f"⚠️ Erro de leitura serial: {e}")
        break

  def update_plot(self, frame):
    if not self.running:
      return (
          self.line_mag_raw,
          self.line_mag_smooth,
          self.line_phase_raw,
          self.line_phase_smooth,
      )

    self.read_serial_non_blocking()

    if self.freq_data:
      freqs = sorted(self.freq_data.keys())
      imp_vals = [self.freq_data[f]["imp_avg"] for f in freqs]
      phase_vals = [self.freq_data[f]["phase_avg"] for f in freqs]

      imp_smooth = self.smooth_series(imp_vals, window=5)
      phase_smooth = self.smooth_series(phase_vals, window=5)

      self.line_mag_raw.set_data(freqs, imp_vals)
      self.line_mag_smooth.set_data(freqs, imp_smooth)

      self.line_phase_raw.set_data(freqs, phase_vals)
      self.line_phase_smooth.set_data(freqs, phase_smooth)

      self.ax_mag.relim()
      self.ax_mag.autoscale_view()

      self.ax_phase.relim()
      self.ax_phase.autoscale_view()

      if len(freqs) >= 2:
        self.ax_mag.set_xlim(min(freqs), max(freqs))

      mean_txt = (
          f" | Média Imp.: {self.last_mean_impedance:.2f} Ω"
          if self.last_mean_impedance is not None
          else ""
      )

      self.status_text.set_text(
          f"Varredura: #{self.sweep_id} | Freq: {self.last_freq_received} Hz | "
          f"Pontos: {len(freqs)}{mean_txt} | "
          f"Atualizado: {datetime.now().strftime('%H:%M:%S')}"
      )

    # Persiste dados periodicamente no CSV
    if time.time() - self.last_save >= self.save_interval:
      self.save_csv()
      self.last_save = time.time()

    return (
        self.line_mag_raw,
        self.line_mag_smooth,
        self.line_phase_raw,
        self.line_phase_smooth,
    )

  def start(self):
    if not self.connect():
      return

    self.running = True
    self.last_save = time.time()

    print("\n🚀 LEITURA EM TEMPO REAL INICIADA")
    print("📊 Exibindo Bode (Magnitude e Fase) | Pressione Ctrl+C para encerrar")
    print("-" * 70)

    _ani = FuncAnimation(
        self.fig,
        self.update_plot,
        interval=100,
        blit=False,
        cache_frame_data=False,
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

      print(f"\n✅ Concluído. Dados gravados em: {self.csv_file}")


if __name__ == "__main__":
  app = AD5933BodeRealtime()
  app.start()