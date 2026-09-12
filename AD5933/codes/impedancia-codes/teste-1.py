import csv
import math
import os
import time
import serial

# ======================================================
# CONFIGURAÇÕES DA PORTA SERIAL
# ======================================================
# Substitua pela porta correta do seu ESP32 (ex: 'COM3' no Windows ou '/dev/ttyUSB0' no Linux/Mac)
PORTA_SERIAL = "COM3"
BAUD_RATE = 115200
ARQUIVO_CSV = "dados_impedancia.csv"

# ======================================================
# INICIALIZAÇÃO DO ARQUIVO CSV
# ======================================================
# Cria o arquivo com o cabeçalho caso ele não exista
if not os.path.exists(ARQUIVO_CSV):
    with open(ARQUIVO_CSV, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "Timestamp",
                "Frequencia (Hz)",
                "Impedancia (Ohm)",
                "Fase (Graus)",
                "Z_real",
                "Z_imag",
            ]
        )

# ======================================================
# LEITURA EM TEMPO REAL
# ======================================================
try:
    print(f"Conectando à porta {PORTA_SERIAL}...")
    esp32 = serial.Serial(PORTA_SERIAL, BAUD_RATE, timeout=1)
    # Dá um pequeno tempo para resetar a comunicação
    time.sleep(2)
    print(f"Conectado com sucesso! Gravando dados em '{ARQUIVO_CSV}'...")
    print("Aguardando varredura iniciar (pressione Ctrl+C para parar)...")

    while True:
        if esp32.in_waiting > 0:
            # Lê a linha vinda da serial e decodifica para string
            linha = esp32.readline().decode("utf-8", errors="ignore").strip()

            # Pula linhas de texto explicativo ou vazias
            if (
                not linha
                or "Varredura" in linha
                or "Hz" in linha
                or "CAL" in linha
                or "==" in linha
            ):
                if linha:
                    print(f"[ESP32]: {linha}")  # Mostra avisos do ESP32 na tela
                continue

            try:
                # O ESP32 envia: freqAtual, impedance, correctedPhase
                valores = linha.split(",")

                if len(valores) == 3:
                    freq = int(valores[0])
                    impedancia = float(valores[1])
                    fase = float(valores[2])

                    # Conversão de fase de Graus para Radianos para as funções matemáticas
                    fase_rad = math.radians(fase)

                    # Cálculo dos componentes Real e Imaginário
                    # Z = |Z| * (cos(th) + j*sin(th))
                    z_real = impedancia * math.cos(fase_rad)
                    z_imag = impedancia * math.sin(fase_rad)

                    # Captura o horário exato da medição
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

                    # Salva no arquivo CSV imediatamente (tempo real)
                    with open(
                        ARQUIVO_CSV, mode="a", newline="", encoding="utf-8"
                    ) as file:
                        writer = csv.writer(file)
                        writer.writerow(
                            [
                                timestamp,
                                freq,
                                impedancia,
                                fase,
                                f"{z_real:.2f}",
                                f"{z_imag:.2f}",
                            ]
                        )

                    # Mostra no terminal o dado processado
                    print(
                        f"👉 Freq: {freq} Hz | Z_real: {z_real:.2f} Ω | Z_imag: {z_imag:.2f} Ω | Fase: {fase}°"
                    )

            except ValueError:
                # Ignora linhas que não possuem dados numéricos válidos (ex: logs de inicialização)
                pass

except serial.SerialException:
    print(
        f"❌ Erro: Não foi possível abrir a porta {PORTA_SERIAL}. Verifique o seu ESP32."
    )
except KeyboardInterrupt:
    print("\n⏹️ Captura finalizada pelo usuário.")