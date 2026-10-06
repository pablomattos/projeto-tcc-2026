import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Mapeamento dos arquivos CSV e rótulos das amostras
arquivos = {
    'teste-01-branco.csv': 'Branco',
    'teste-01-005.csv': '0.05 molar',
    'teste-01-025.csv': '0.25 molar',
    'teste-01-500.csv': '0.5 molar',
}

# Criando a figura para o Diagrama de Bode
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

for caminho_arquivo, rotulo in arquivos.items():
    if os.path.exists(caminho_arquivo):
        # 1. Leitura e limpeza das colunas
        df = pd.read_csv(caminho_arquivo)
        df.columns = [col.split(';')[0].strip() for col in df.columns]

        # 2. Identificação dinâmica da coluna de Fase
        coluna_fase = [col for col in df.columns if 'Fase' in col][0]

        # 3. Conversão para tipo numérico
        cols_numericas = ['Freq(Hz)', 'Imp_AVG(Ohm)', coluna_fase]
        for col in cols_numericas:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.split(';').str[0], errors='coerce'
            )

        # 4. Remoção de NaNs/linhas corrompidas
        df = df.dropna(subset=cols_numericas)

        # 5. Filtragem do último Sweep_ID (evita efeito dente de serra no gráfico)
        if 'Sweep_ID' in df.columns:
            df['Sweep_ID'] = pd.to_numeric(
                df['Sweep_ID'].astype(str).str.split(';').str[0],
                errors='coerce',
            )
            ultimo_sweep = df['Sweep_ID'].max()
            df = df[df['Sweep_ID'] == ultimo_sweep]

        # 6. Ordenação por frequência
        df = df.sort_values(by='Freq(Hz)')

        freq_hz = df['Freq(Hz)']

        # Cálculo da Magnitude em Decibéis (dB)
        mag_db = 20 * np.log10(df['Imp_AVG(Ohm)'])

        # Plot 1: Bode Magnitude (Escala semilogarítmica)
        ax1.semilogx(
            freq_hz, mag_db, marker='o', markersize=3, label=rotulo
        )

        # Plot 2: Bode Fase (Escala semilogarítmica)
        ax2.semilogx(
            freq_hz,
            df[coluna_fase],
            marker='s',
            markersize=3,
            linestyle='--',
            label=rotulo,
        )

# Configurações do gráfico superior (Magnitude em dB)
ax1.set_ylabel('Magnitude (dB = 20 log10 |Z|)', fontweight='bold')
ax1.set_title(
    'Diagrama de Bode - Espectros de Impedância e Fase', fontweight='bold'
)
ax1.grid(True, which='both', linestyle='--', alpha=0.6)
ax1.legend(title='Concen. NaCl')

# Configurações do gráfico inferior (Fase em graus)
ax2.set_xlabel('Frequência (Hz)', fontweight='bold')
ax2.set_ylabel('Fase (°)', fontweight='bold')
ax2.grid(True, which='both', linestyle='--', alpha=0.6)
ax2.legend(title='Concen. NaCl')

plt.tight_layout()
plt.show()