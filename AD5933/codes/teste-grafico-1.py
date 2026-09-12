import os
import sys
import csv

# FORÇA O MATPLOTLIB A USAR O PYSIDE6 ANTES DE QUALQUER IMPORTAÇÃO
os.environ["QT_API"] = "pyside6"

import serial
import serial.tools.list_ports
import threading
import numpy as np

# IMPORTAÇÃO CORRETA E ISOLADA DO MATPLOTLIB PARA PYSIDE6
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

# IMPORTAÇÃO DOS COMPONENTES DO PYSIDE6
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QPushButton, QComboBox, QLabel, QTextEdit
)
from PySide6.QtCore import Signal as pyqtSignal, QObject

# ======================================================
# GERENCIADOR DE SINAIS PARA THREAD DA SERIAL
# ======================================================
class SerialSignals(QObject):
    data_received = pyqtSignal()

# ======================================================
# CLASSE PRINCIPAL DA INTERFACE
# ======================================================
class ImpedanceAnalyzer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Analisador de Impedância AD5933 + ESP32")
        self.setGeometry(100, 100, 1200, 700)

        # Dicionário de armazenamento e nome do arquivo de saída
        self.freq_data = {}
        self.csv_filename = "dados_impedancia.csv"
        
        self.signals = SerialSignals()
        self.signals.data_received.connect(self.update_plots)

        self.ser = None
        self.is_reading = False
        self.thread = None

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # --------------------------------------------------
        # PAINEL LATERAL ESQUERDO (CONTROLES)
        # --------------------------------------------------
        left_panel = QVBoxLayout()
        
        left_panel.addWidget(QLabel("<b>Porta COM:</b>"))
        self.combo_ports = QComboBox()
        self.refresh_ports()
        left_panel.addWidget(self.combo_ports)

        self.btn_connect = QPushButton("Conectar ESP32")
        self.btn_connect.clicked.connect(self.toggle_connection)
        left_panel.addWidget(self.btn_connect)

        self.btn_clear = QPushButton("Limpar Gráficos")
        self.btn_clear.clicked.connect(self.clear_data)
        left_panel.addWidget(self.btn_clear)

        left_panel.addWidget(QLabel("<br><b>Monitor Serial (Log):</b>"))
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        left_panel.addWidget(self.log_text)

        main_layout.addLayout(left_panel, stretch=1)

        # --------------------------------------------------
        # PAINEL DIREITO (MATPLOTLIB NATIVO NO PYSIDE6)
        # --------------------------------------------------
        self.figure = Figure(figsize=(15, 5))
        
        self.canvas = FigureCanvas(self.figure)
        main_layout.addWidget(self.canvas, stretch=3)

        self.ax_mag = self.figure.add_subplot(1, 3, 1)
        self.ax_phase = self.figure.add_subplot(1, 3, 2)
        self.ax_nyquist = self.figure.add_subplot(1, 3, 3)

        self.setup_plots()

    def setup_plots(self):
        """Configura a estética inicial dos eixos e labels."""
        self.figure.patch.set_facecolor('#f0f0f0')

        self.ax_mag.set_title("Bode - Magnitude")
        self.ax_mag.set_xlabel("Frequência (Hz)")
        self.ax_mag.set_ylabel("Impedância (|Z| [Ω])")
        self.ax_mag.grid(True, which="both", ls="--")
        self.ax_mag.set_xscale('log')
        self.ax_mag.set_xlim(1000, 100000)

        self.ax_phase.set_title("Bode - Fase")
        self.ax_phase.set_xlabel("Frequência (Hz)")
        self.ax_phase.set_ylabel("Fase (φ [°])")
        self.ax_phase.grid(True, which="both", ls="--")
        self.ax_phase.set_xscale('log')
        self.ax_phase.set_xlim(1000, 100000)

        self.ax_nyquist.set_title("Diagrama de Nyquist")
        self.ax_nyquist.set_xlabel("Z' (Real [Ω])")
        self.ax_nyquist.set_ylabel("-Z'' (Imaginário [Ω])")
        self.ax_nyquist.grid(True, which="both", ls="--")

        self.figure.tight_layout()
        self.canvas.draw()

    def refresh_ports(self):
        self.combo_ports.clear()
        ports = serial.tools.list_ports.comports()
        for p in ports:
            self.combo_ports.addItem(p.device)

    def toggle_connection(self):
        if self.ser is None or not self.ser.is_open:
            port = self.combo_ports.currentText()
            if not port:
                self.log_text.append("❌ Nenhuma porta selecionada.")
                return
            try:
                # Inicializa o arquivo CSV com cabeçalho limpo se ele não existir
                if not os.path.exists(self.csv_filename):
                    with open(self.csv_filename, mode='w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow(["Frequencia_Hz", "Impedancia_Ohm", "Fase_Graus", "Z_Real", "Z_Imaginario"])

                self.ser = serial.Serial(port, 115200, timeout=1)
                self.is_reading = True
                self.thread = threading.Thread(target=self.read_serial, daemon=True)
                self.thread.start()
                self.btn_connect.setText("Desconectar")
                self.log_text.append(f"✅ Conectado na porta {port}")
                self.log_text.append(f"💾 Arquivo de saída: {self.csv_filename}")
            except Exception as e:
                self.log_text.append(f"❌ Erro ao conectar: {e}")
        else:
            self.is_reading = False
            if self.ser:
                self.ser.close()
            self.btn_connect.setText("Conectar ESP32")
            self.log_text.append("🔌 Desconectado.")

    # ======================================================
    # LEITURA DA SERIAL DIRETA E PROCESSAMENTO DE SINAIS
    # ======================================================
    def read_serial(self):
        while self.is_reading:
            if self.ser and self.ser.in_waiting > 0:
                try:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if not line:
                        continue
                    # Ignora strings de controle ou logs vindos da firmware
                    if "Freq" in line or "CAL" in line or "🚀" in line or "✅" in line or "==" in line:
                        continue

                    parts = line.split(',')
                    if len(parts) != 3:
                        continue

                    freq = float(parts[0])
                    impedance = float(parts[1])
                    phase_deg = float(parts[2])

                    # Tratamento cíclico dos limites da fase do sinal elétrico
                    if phase_deg < -180: phase_deg += 360
                    if phase_deg > 180:  phase_deg -= 360

                    # Conversão direta para o plano complexo
                    phase_rad = np.radians(phase_deg)
                    z_real = impedance * np.cos(phase_rad)
                    z_imag = -(impedance * np.sin(phase_rad))

                    self.freq_data[freq] = {
                        "impedance": impedance,
                        "phase": phase_deg,
                        "z_real": z_real,
                        "z_imag": z_imag
                    }

                    # Gravação instantânea no CSV em tempo real
                    with open(self.csv_filename, mode='a', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow([freq, impedance, phase_deg, z_real, z_imag])

                    self.signals.data_received.emit()

                except Exception as e:
                    pass

    # ======================================================
    # ATUALIZAÇÃO DOS GRÁFICOS (PLOT EM TEMPO REAL)
    # ======================================================
    def update_plots(self):
        if not self.freq_data:
            return

        sorted_freqs = sorted(self.freq_data.keys())
        
        freqs = np.array(sorted_freqs)
        magnitudes = np.array([self.freq_data[f]["impedance"] for f in sorted_freqs])
        phases = np.array([self.freq_data[f]["phase"] for f in sorted_freqs])
        reals = np.array([self.freq_data[f]["z_real"] for f in sorted_freqs])
        imags = np.array([self.freq_data[f]["z_imag"] for f in sorted_freqs])

        self.ax_mag.clear()
        self.ax_phase.clear()
        self.ax_nyquist.clear()

        # Renderização dinâmica do painel Bode Magnitude
        self.ax_mag.grid(True, which="both", ls="--")
        self.ax_mag.set_xscale('log')
        self.ax_mag.set_title("Bode - Magnitude")
        self.ax_mag.set_xlabel("Frequência (Hz)")
        self.ax_mag.set_ylabel("Impedância (|Z| [Ω])")
        self.ax_mag.set_xlim(1000, 100000)

        # Renderização dinâmica do painel Bode Fase
        self.ax_phase.grid(True, which="both", ls="--")
        self.ax_phase.set_xscale('log')
        self.ax_phase.set_title("Bode - Fase")
        self.ax_phase.set_xlabel("Frequência (Hz)")
        self.ax_phase.set_ylabel("Fase (φ [°])")
        self.ax_phase.set_xlim(1000, 100000)
        
        # Ajustado limite de visualização para acomodar as variações resistivas/capacitivas reais
        self.ax_phase.set_ylim(-110, 20)

        # Renderização dinâmica do Diagrama de Nyquist
        self.ax_nyquist.grid(True, which="both", ls="--")
        self.ax_nyquist.set_title("Diagrama de Nyquist")
        self.ax_nyquist.set_xlabel("Z' (Real [Ω])")
        self.ax_nyquist.set_ylabel("-Z'' (Imaginário [Ω])")

        # Plot das linhas de tendência de dados
        self.ax_mag.plot(freqs, magnitudes, color='#1f77b4', marker='o', markersize=3, linewidth=2)
        self.ax_phase.plot(freqs, phases, color='#ff7f0e', marker='o', markersize=3, linewidth=2)
        self.ax_nyquist.plot(reals, imags, color='#9467bd', marker='o', markersize=4, linewidth=2)
        
        # Ajuste adaptável para manter aspect ratio 1:1 correto do semicírculo (Python 3.14/Matplotlib moderno)
        self.ax_nyquist.set_aspect('equal', adjustable='datalim')
        self.canvas.draw()

    def clear_data(self):
        self.freq_data.clear()
        self.ax_mag.clear()
        self.ax_phase.clear()
        self.ax_nyquist.clear()
        self.setup_plots()
        self.log_text.clear()
        self.log_text.append("🧹 Gráficos limpos na tela. Histórico resetado.")

    def closeEvent(self, event):
        self.is_reading = False
        if self.ser and self.ser.is_open:
            self.ser.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    analyzer = ImpedanceAnalyzer()
    analyzer.show()
    sys.exit(app.exec())