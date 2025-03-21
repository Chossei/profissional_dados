import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import tabulate


# Carregando a base de dados
base = pd.read_csv('base.csv', sep = ',', encoding = 'utf-8')


# Título e seleção das variáveis a serem analisadas
st.title('Análise de dados do profissional da área de dados no Brasil em 2023')

variavel = st.selectbox('Escolha a variável para análise', ['Cargo',  'Carreira', 'Genero', 'Raça', 'Experiencia'])

# Função para analisar a variável

def analisar_salario(variavel, data_new):
    # Calcular estatísticas descritivas estilo summary() do R -----------------
    descritivas = data_new.groupby(variavel)['Faixa salarial'].describe()

    # Criar DataFrame do intervalo de confiança --------------------------------
    stats = data_new.groupby(variavel)['Faixa salarial'].agg(['count', 'mean', 'std'])
    stats.rename(columns={'count': 'n', 'mean': 'Média', 'std': 'Desvio Padrão'}, inplace=True)

    stats['IC Inferior'] = stats['Média'] - 1.96 * (stats['Desvio Padrão'] / np.sqrt(stats['n']))
    stats['IC Superior'] = stats['Média'] + 1.96 * (stats['Desvio Padrão'] / np.sqrt(stats['n']))

    # Criando o boxplot --------------------------------------------------------
    plt.figure(figsize=(10, 6))
    plot = sns.boxplot(
        x=variavel, y='Faixa salarial', data=data_new, showmeans=True, palette="coolwarm",
        meanprops={'marker': 'D', 'markerfacecolor': 'red', 'markeredgecolor': 'black', 'markersize': 7}
    )

    # Ajustes visuais
    plot.set_xlabel(variavel, fontsize=10)
    plot.set_ylabel('R$', fontsize=10)
    plt.title(f'Salário por {variavel}', fontsize=12)
    plt.xticks(fontsize=8)
    plt.yticks(fontsize=8)

    # Adicionando linhas horizontais em intervalos de 5 mil
    for i in range(1, 9):
        plt.axhline(y=i * 5000, color='gray', linestyle='--', linewidth=1, alpha=0.5)

    # Salvando gráfico
    grafico_path = 'grafico.png'
    plt.savefig(grafico_path, dpi=300, bbox_inches='tight')
    plt.close()

    # Criar texto Markdown -----------------------------------------------------
    texto_markdown = f'''## Análise descritiva do Salário por {variavel} no mercado de dados no Brasil, 2023

### 📊 Sumário descritivo estilo R
{descritivas.to_markdown()}

---

### 📈 Visualização gráfica
![Salario por {variavel}]({grafico_path})

---

### 📏 Intervalo de confiança para a média (95% de confiança)
'''
    for index, row in stats.iterrows():
        texto_markdown += f'''- {index}:
  - **IC Inferior:** {row["IC Inferior"]:.2f}
  - **IC Superior:** {row["IC Superior"]:.2f}

'''

    return texto_markdown

texto = analisar_salario(variavel, base)

st.markdown(texto)
