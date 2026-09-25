import os
import matplotlib.pyplot as plt
import pandas as pd

# Mapeamento dos arquivos CSV e seus respectivos rótulos para a legenda
arquivos = {
    'teste-01-branco.csv': 'Teste - Branco',
    'teste-01-005.csv': 'Teste - 0.05',
    'teste-01-025.csv': 'Teste - 0.25',
    'teste-01-500.csv': 'Teste - 5.00',
}

# Criando a figura com 2 subplots (Impedância no superior e Fase no inferior)
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

for caminho_arquivo, rotulo in arquivos.items():
    if os.path.exists(caminho_arquivo):
        # 1. Leitura do arquivo CSV
        df = pd.read_csv(caminho_arquivo)

        # 2. Limpeza dos nomes das colunas (removendo caracteres indesejados/ponto e vírgula)
        df.columns = [col.split(';')[0].strip() for col in df.columns]

        # 3. Localização dinâmica da coluna de Fase (independente da codificação do caractere '°')
        coluna_fase = [col for col in df.columns if 'Fase' in col][0]

        # 4. Conversão dos dados para tipos numéricos
        cols_numericas = ['Freq(Hz)', 'Imp_AVG(Ohm)', coluna_fase]
        for col in cols_numericas:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.split(';').str[0], errors='coerce'
            )

        # 5. Remoção de linhas nulas ou corrompidas
        df = df.dropna(subset=cols_numericas)

        # 6. Filtragem pela última varredura (Sweep_ID) do arquivo, caso existam varreduras repetidas
        if 'Sweep_ID' in df.columns:
            df['Sweep_ID'] = pd.to_numeric(
                df['Sweep_ID'].astype(str).str.split(';').str[0],
                errors='coerce',
            )
            ultimo_sweep = df['Sweep_ID'].max()
            df = df[df['Sweep_ID'] == ultimo_sweep]

        # 7. Ordenação por frequência
        df = df.sort_values(by='Freq(Hz)')

        # Frequência em kHz no eixo X
        freq_khz = df['Freq(Hz)'] / 1000

        # Plotagem da Impedância (Eixo Superior)
        ax1.plot(
            freq_khz,
            df['Imp_AVG(Ohm)'],
            marker='o',
            markersize=3,
            label=rotulo,
        )

        # Plotagem da Fase (Eixo Inferior)
        ax2.plot(
            freq_khz,
            df[coluna_fase],
            marker='s',
            markersize=3,
            linestyle='--',
            label=rotulo,
        )

# Configurações do gráfico de Impedância
ax1.set_ylabel('Impedância Média (Ω)', fontweight='bold')
ax1.set_title(
    'Comparação de Espectros de Impedância e Fase (10 kHz a 100 kHz)',
    fontweight='bold',
)
ax1.grid(True, linestyle='--', alpha=0.6)
ax1.legend(title='Amostras')

# Configurações do gráfico de Fase
ax2.set_xlabel('Frequência (kHz)', fontweight='bold')
ax2.set_ylabel('Fase Média (°)', fontweight='bold')
ax2.grid(True, linestyle='--', alpha=0.6)
ax2.legend(title='Amostras')

plt.tight_layout()
plt.show()