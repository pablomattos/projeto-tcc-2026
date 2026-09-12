import serial
import time
import numpy as np
import matplotlib.pyplot as plt
import skrf as rf

# ==============================================================================
# CONFIGURAÇÕES DA PORTA SERIAL (Ajuste conforme o seu sistema)
# ==============================================================================
# No Windows geralmente é 'COM3', 'COM4', etc. No Linux/Mac algo como '/dev/ttyUSB0'
PORTA_SERIAL = 'COM3'
BAUD_RATE = 115200
Z0_SISTEMA = 50.0  # Impedância de referência para normalização do Mapa de Smith

# ==============================================================================
# INICIALIZAÇÃO DO GRÁFICO (MAPA DE SMITH)
# ==============================================================================
plt.ion()  # Ativa o modo interativo do Matplotlib para atualizações em tempo real
fig, ax = plt.subplots(figsize=(8, 8))


def atualizar_mapa_smith(impedancias_complexas):
    """Limpa o gráfico anterior e plota os novos pontos no Mapa de Smith"""
    ax.clear()

    # Desenha as linhas e círculos característicos do Mapa de Smith usando o scikit-rf
    rf.plotting.plot_smith(ax=ax, chart_type='z', draw_labels=True)

    # Converte as impedâncias puras em Coeficientes de Reflexão (Gamma)
    # Fórmula: Gamma = (Z - Z0) / (Z + Z0)
    Z = np.array(impedancias_complexas)
    gamma = (Z - Z0_SISTEMA) / (Z + Z0_SISTEMA)

    # Plota os pontos medidos no mapa (linhas e marcadores)
    ax.plot(np.real(gamma), np.imag(gamma), 'r-o', linewidth=2, markersize=4, label='Varredura Sensor')
    ax.legend(loc='upper left')
    ax.set_title("Mapa de Smith em Tempo Real (AD5933 + ESP32)", fontsize=14, pad=20)

    # Atualiza a janela do gráfico
    fig.canvas.draw()
    fig.canvas.flush_events()


# ==============================================================================
# CONEXÃO SERIAL E LOOP PRINCIPAL
# ==============================================================================
print(f"Tentando conectar na porta {PORTA_SERIAL}...")
try:
    ser = serial.Serial(PORTA_SERIAL, BAUD_RATE, timeout=1)
    time.sleep(2)  # Aguarda o ESP32 resetar após a abertura da conexão
    print("Conectado com sucesso! Aguardando dados...")
except Exception as e:
    print(f"❌ Erro ao abrir a porta serial: {e}")
    exit()

pontos_varredura = []

try:
    while True:
        if ser.in_waiting > 0:
            linha = ser.readline().decode('utf-8', errors='ignore').strip()

            # Detecta o início de uma nova varredura ou mensagens de controle
            if "Freq(Hz)" in linha or "========================" in linha:
                if pontos_varredura:
                    # Se já tínhamos pontos acumulados da varredura anterior, plota no mapa
                    atualizar_mapa_smith(pontos_varredura)
                    pontos_varredura = []  # Limpa o array para a nova varredura
                continue

            if "❌" in linha or "🎯" in linha or "✅" in linha or "CAL" in linha:
                print(f"[ESP32]: {linha}")  # Mostra logs de calibração ou erros no terminal
                continue

            # Processa os dados do CSV: Freq(Hz),Impedancia(Ohm),Fase(°)
            try:
                partes = linha.split(',')
                if len(partes) == 3:
                    freq = float(partes[0])
                    impedance = float(partes[1])
                    phase_deg = float(partes[2])

                    # Converte Magnitude (Impedância) e Fase (Graus) para um Número Complexo Z = R + jX
                    phase_rad = np.radians(phase_deg)
                    r = impedance * np.cos(phase_rad)
                    x = impedance * np.sin(phase_rad)
                    z_complexo = complex(r, x)

                    pontos_varredura.append(z_complexo)

            except ValueError:
                # Ignora linhas de texto aleatórias que não sejam o CSV de dados
                pass

except KeyboardInterrupt:
    print("\nEncerrando o programa...")
finally:
    ser.close()
    plt.ioff()
    plt.show()