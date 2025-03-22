import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import tabulate
import re
import base64
import scipy


# Carregando a base de dados
base = pd.read_csv('base_final.csv', sep = ',', encoding = 'utf-8')


# Título e seleção das variáveis a serem analisadas
st.title('Análise de dados do profissional da área de dados no Brasil em 2023')

variavel = st.selectbox('Escolha a variável para análise', ['Cargo',  'Carreira', 'Genero', 'Raça', 'Experiencia'])

# Função para aparecer imagem no streamlit

def ajustar_caminho_imagem(texto_markdown):
    # Expressão regular pra encontrar imagens no markdown
    padrao = r"!\[.*?\]\((.*?)\)"
    
    # Função auxiliar pra converter imagem pra base64
    def converter_para_base64(match):
        caminho_imagem = match.group(1)
        try:
            with open(caminho_imagem, "rb") as img_file:
                encoded_string = base64.b64encode(img_file.read()).decode("utf-8")
            return f'![Imagem](data:image/png;base64,{encoded_string})'
        except Exception as e:
            return f"Erro ao carregar imagem: {str(e)}"

    # Substitui os caminhos de imagem pelo formato base64
    texto_corrigido = re.sub(padrao, converter_para_base64, texto_markdown)
    return texto_corrigido

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
    texto_markdown = f'''### 📊 Sumário descritivo
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


# Função para executar o teste de hipóteses

def teste_normhip(variavel, categoria1, categoria2):
        texto_final = ''
        grupo1 = base[base[variavel] == categoria1]['Faixa salarial'].dropna().to_list()
        grupo2 = base[base[variavel] == categoria2]['Faixa salarial'].dropna().to_list()

        # Teste Shapiro para normalidade
        norm1 = scipy.stats.shapiro(grupo1)
        norm2 = scipy.stats.shapiro(grupo2)

        if norm1[1] < 0.05 or norm2[1] < 0.05:
            texto_final += '''Os dados das categorias não seguem uma distribuição normal. Serão aplicadas transformações para realizar o teste de hipóteses.
            '''
            if np.mean(grupo1) > np.median(grupo1) and np.mean(grupo2) > np.median(grupo2):
                texto_final += '''Como os grupos são assimétricos à direita, para se aproximar de uma normal, utilizaremos transformação logarítmica.
                '''
                grupo1 = np.log(grupo1)
                grupo2 = np.log(grupo2)
            else:
                texto_final += '''Os dados são assimétricos. Será aplicada a transformação Box-Cox.
                '''
                grupo1 = scipy.stats.boxcox(grupo1)[0]
                grupo2 = scipy.stats.boxcox(grupo2)[0]
        else:
            texto_final = '''Os dados seguem uma distribuição normal.
            '''
    
    # Teste de Bartllet para verificar a variância
        teste_bartlett = scipy.stats.bartlett(grupo1, grupo2)[1]

        if teste_bartlett > 0.05:
            p_value = scipy.stats.ttest_ind(grupo1, grupo2)[1]
        else:
            p_value = scipy.stats.ttest_ind(grupo1, grupo2, equal_var=False)[1]
    
        if p_value < 0.05:
            resultado = ['menor', 'diferentes']
        else:
            resultado = ['maior', 'iguais']

        texto_final += f'''
- H<sub>0</sub>: μ<sub>{categoria1}</sub>   =   μ<sub>{categoria2}</sub>

- H<sub>1</sub>: μ<sub>{categoria1}</sub>   ≠   μ<sub>{categoria2}</sub>

Como p-value ({round(p_value, 6)}) é {resultado[0]} que 0.05, há evidências estatísticas suficientes para afirmar que as médias das categorias são {resultado[1]}.'''
    
        return texto_final

texto = analisar_salario(variavel, base)
texto_final = ajustar_caminho_imagem(texto)

st.markdown(texto_final, unsafe_allow_html=True)

# Teste de Hipóteses ----------------------------------------------------

st.markdown('---')
st.markdown('''### 🔍 Teste de Hipóteses para a média''')

lista = pd.Series(base[variavel].unique()).dropna()
categoria1 = st.selectbox('Escolha a primeira categoria da variável', lista)
lista2 = lista.loc[lista != categoria1]
categoria2 = st.selectbox('Escolha a segunda categoria da variável', lista2)

texto_hipoteses = teste_normhip(variavel, categoria1, categoria2)
st.markdown(texto_hipoteses, unsafe_allow_html = True)
