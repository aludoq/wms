import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Optional, Tuple
import os # Importe o módulo os

FILE_PATH = 'WMS.xlsm'

@st.cache_data
def load_data(file_path: str) -> Optional[pd.DataFrame]:
    """Carrega dados do arquivo Excel especificado."""
    
    # Adiciona a data de modificação do arquivo como um parâmetro para quebrar o cache
    try:
        mod_time = os.path.getmtime(file_path)
    except FileNotFoundError:
        st.error(f"Arquivo '{file_path}' não encontrado. Verifique se o nome está correto.")
        return None

    try:
        # Troque 'NomeDaSuaAbaAqui' para o nome da aba correta
        return pd.read_excel(file_path, sheet_name='NomeDaSuaAbaAqui')
    except Exception as e:
        st.error(f"Ocorreu um erro ao ler o arquivo: {e}")
        return None

def preprocess_data(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """Pré-processa o DataFrame limpando colunas e manipulando datas."""
    df = df.copy()
    df.dropna(axis=1, how='all', inplace=True)

    colunas_para_remover = ['Lote', 'Almoxarifado']
    df.drop(columns=[col for col in colunas_para_remover if col in df.columns], inplace=True)

    if 'datasalva' not in df.columns:
        st.error("Coluna 'datasalva' não encontrada na planilha. Verifique o nome da coluna.")
        return None

    df['datasalva'] = pd.to_datetime(df['datasalva'], errors='coerce')
    df.dropna(subset=['datasalva'], inplace=True) # Remove linhas onde a conversão falhou
    df['datasalva_formatada'] = df['datasalva'].dt.date
    return df

def search_item(df: pd.DataFrame, item_code: str) -> Tuple[pd.DataFrame, Optional[str]]:
    """Procura um item pelo seu código no DataFrame."""
    if 'codigo' not in df.columns:
        error_message = "Coluna 'codigo' não encontrada."
        st.error(error_message)
        return pd.DataFrame(), error_message
    try:
        code_to_search = int(item_code)
        resultados = df[df['codigo'] == code_to_search]
        return resultados, None
    except ValueError:
        error_message = "Por favor, digite um código de item válido (números inteiros)."
        st.error(error_message)
        return pd.DataFrame(), error_message

def main():
    """Função principal para rodar o aplicativo Streamlit."""
    st.set_page_config(page_title="Consulta de Estoque WMS")
    st.title("Consulta de Itens por Código")

    df_raw = load_data(FILE_PATH)
    if df_raw is None:
        st.stop()

    df_processed = preprocess_data(df_raw)
    if df_processed is None:
        st.stop()

    hoje = datetime.now().date()
    df_hoje = df_processed[df_processed['datasalva_formatada'] == hoje]

    if df_hoje.empty:
        st.warning(f"Não há informações para a data de hoje ({hoje.strftime('%d/%m/%Y')}).")
        st.info("Por favor, selecione uma data para pesquisar.")
        data_pesquisa = st.date_input("Escolha a data da pesquisa:", value=hoje)
        df_filtrado = df_processed[df_processed['datasalva_formatada'] == data_pesquisa]
    else:
        df_filtrado = df_hoje

    st.markdown("Use o campo abaixo para pesquisar um item pelo seu código.")
    if not df_filtrado.empty:
        st.write(f"Dados exibidos para a data: **{df_filtrado['datasalva_formatada'].iloc[0].strftime('%d/%m/%Y')}**")

    codigo_busca = st.text_input("Digite o código do item com 7 digitos:")

    if codigo_busca:
        resultados, _ = search_item(df_filtrado, codigo_busca)
        if not resultados.empty:
            st.write("### Resultado da Busca")
            total_quantidade = resultados['Qtd'].sum()
            st.metric(label="Total de Quantidade", value=f"{total_quantidade:,.0f}")
            enderecos_encontrados = resultados['Endereço'].unique()
            st.write("### Endereços")
            for endereco in enderecos_encontrados:
                st.write(f"- {endereco}")
            st.write("---")
            st.dataframe(resultados)
        else:
            if not df_filtrado.empty:
                st.warning(f"Nenhum item encontrado com o código '{codigo_busca}' para esta data.")
    elif not df_filtrado.empty:
        st.write("### Planilha do dia")
        st.dataframe(df_filtrado)
    else:
        st.info("Nenhum dado encontrado para a data selecionada.")

if __name__ == "__main__":
    main()