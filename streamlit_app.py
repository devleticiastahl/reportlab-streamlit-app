"""
Report Lab - Plataforma de Análise de Dados e Geração de Relatórios Profissionais

Este aplicativo Streamlit permite:
1. Carregar datasets em CSV ou Excel
2. Visualizar análises exploratórias numéricas e categóricas
3. Gerar relatórios PDF profissionais com estatísticas e visualizações
4. Personalizar relatórios com logo da empresa

Desenvolvido com as bibliotecas:
- Streamlit para interface web
- Pandas para manipulação de dados
- Matplotlib/Seaborn para visualizações
- FPDF para geração de relatórios PDF

Autor: Letícia Stahl
Versão: 1.1
Data: 30/03/2025
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
from fpdf import FPDF
import base64
from tempfile import NamedTemporaryFile
import os
import matplotlib
import traceback
from io import BytesIO

# =============================================================================
# CONFIGURAÇÃO INICIAL
# =============================================================================

# Configurar backend para evitar problemas de threading
matplotlib.use('Agg')

# Configurar página do Streamlit
st.set_page_config(
    page_title="Report Lab",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configurar estilo de gráficos
plt.style.use('default')
sns.set_theme(style="whitegrid")
sns.set_palette(["#1a3a8f", "#1e4ed8", "#2563eb", "#3b82f6", "#93c5fd"])

# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def cleanup_temp_files(*file_paths):
    """Remove temporary files safely"""
    for path in file_paths:
        if path and os.path.exists(path):
            try:
                os.unlink(path)
            except Exception as e:
                print(f"Warning: Could not delete temp file {path}: {str(e)}")

@st.cache_data
def load_data(uploaded_file):
    """
    Carrega dados de arquivos CSV ou Excel.
    
    Parâmetros:
        uploaded_file (UploadedFile): Arquivo carregado via Streamlit
    
    Retorna:
        DataFrame: Dados carregados ou None em caso de erro
    """
    try:
        if uploaded_file.name.endswith('.csv'):
            return pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(('.xlsx', '.xls')):
            return pd.read_excel(uploaded_file, engine='openpyxl')
    except Exception as e:
        st.error(f"Erro ao ler arquivo: {str(e)}")
        return None

def create_pdf_report(df, logo_path, num_images=[], cat_images=[]):
    """
    Gera relatório PDF profissional com análise de dados.
    
    Parâmetros:
        df (DataFrame): Conjunto de dados a ser analisado
        logo_path (str): Caminho para o arquivo de logo
        num_images (list): Lista de caminhos para imagens de análises numéricas
        cat_images (list): Lista de caminhos para imagens de análises categóricas
    
    Retorna:
        bytes: Conteúdo do PDF em bytes
    """
    # Configurar PDF em formato paisagem (landscape)
    pdf = FPDF(orientation='L')
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=10)
    
    # Adicionar logo se existir
    if logo_path and os.path.exists(logo_path):
        pdf.image(logo_path, x=10, y=8, w=25)
    
    # Título do relatório
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 15, "Relatório de Análise de Dados", ln=1, align='C')
    pdf.ln(5)
    
    # Informações básicas do dataset
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, f"Data do relatório: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=1)
    pdf.cell(0, 8, f"Total de registros: {len(df)}", ln=1)
    pdf.cell(0, 8, f"Total de colunas: {len(df.columns)}", ln=1)
    pdf.cell(0, 8, f"Total de valores faltantes: {df.isnull().sum().sum()}", ln=1)
    pdf.ln(10)
    
    # Seção de resumo estatístico
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Resumo Estatístico", ln=1)
    pdf.set_font("Arial", '', 8)
    
    # Preparar dados estatísticos
    desc_stats = df.describe().T.reset_index()
    desc_stats.columns = ['Coluna', 'Contagem', 'Média', 'Desvio Padrão', 'Mínimo', '25%', '50%', '75%', 'Máximo']
    
    # Configurar layout da tabela
    page_width = 280
    col_widths = [
        page_width * 0.15, page_width * 0.10, page_width * 0.10,
        page_width * 0.12, page_width * 0.10, page_width * 0.10,
        page_width * 0.10, page_width * 0.10, page_width * 0.10
    ]
    
    # Cabeçalho da tabela
    headers = desc_stats.columns.tolist()
    pdf.set_fill_color(200, 220, 255)
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 8, header, border=1, fill=True, align='C')
    pdf.ln()
    
    # Dados da tabela
    pdf.set_fill_color(255, 255, 255)
    for _, row in desc_stats.iterrows():
        for i, col in enumerate(headers):
            value = row[col]
            if isinstance(value, float):
                value = f"{value:.2f}"
            pdf.cell(col_widths[i], 8, str(value), border=1, align='C')
        pdf.ln()
    
    pdf.ln(10)
    
    # Adicionar visualizações gráficas
    if num_images or cat_images:
        pdf.add_page(orientation='L')
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Visualizações Gráficas", ln=1)
        pdf.ln(8)
        
        # Gráficos numéricos
        if num_images:
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 8, "Análise Numérica", ln=1)
            pdf.ln(5)
            for img_path in num_images:
                if os.path.exists(img_path):
                    img_width = 260
                    x_position = (pdf.w - img_width) / 2
                    pdf.image(img_path, x=x_position, w=img_width)
                    pdf.ln(5)
        
        # Gráficos categóricos
        if cat_images:
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 8, "Análise Categórica", ln=1)
            pdf.ln(5)
            for img_path in cat_images:
                if os.path.exists(img_path):
                    img_width = 260
                    x_position = (pdf.w - img_width) / 2
                    pdf.image(img_path, x=x_position, w=img_width)
                    pdf.ln(5)
    
    # Retornar PDF como bytes
    return pdf.output(dest='S').encode('latin-1')

def save_plot(fig):
    """Salva figura matplotlib em arquivo temporário"""
    with NamedTemporaryFile(delete=False, suffix='.png') as tmpfile:
        fig.savefig(tmpfile.name, bbox_inches='tight', dpi=150)
        return tmpfile.name

# =============================================================================
# PÁGINA INICIAL (mantida igual)
# =============================================================================

def show_homepage():
    """Exibe a página inicial com apresentação do sistema"""
    # ... (código da homepage mantido igual) ...

# =============================================================================
# BARRA LATERAL (mantida igual)
# =============================================================================

with st.sidebar:
    # ... (código da sidebar mantido igual) ...

# =============================================================================
# PÁGINA PRINCIPAL DE ANÁLISE
# =============================================================================

# Exibir página inicial se nenhum arquivo foi carregado
if not uploaded_file:
    show_homepage()
    st.stop()

# Processamento de dados
df = load_data(uploaded_file)
if df is None:
    st.error("❌ Não foi possível carregar o arquivo. Verifique o formato e tente novamente.")
    st.stop()

st.session_state['df'] = df
st.success(f"✅ Arquivo '{uploaded_file.name}' carregado com sucesso!")

# Processamento de logo
logo_path = None
if logo_file:
    with NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
        tmp_file.write(logo_file.getvalue())
        logo_path = tmp_file.name
    st.success(f"✅ Logo carregada com sucesso!")

# =============================================================================
# SEÇÃO DE VISÃO GERAL (mantida igual)
# =============================================================================

st.header("Visão Geral dos Dados")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total de Registros", len(df))
with col2:
    st.metric("Total de Colunas", len(df.columns))
with col3:
    st.metric("Valores Faltantes", df.isnull().sum().sum())

st.subheader("Amostra dos Dados")
st.dataframe(df.head(), height=250, use_container_width=True)

# Inicializar listas para armazenar gráficos
num_figs, cat_figs = [], []
num_image_paths, cat_image_paths = [], []

# =============================================================================
# ANÁLISE NUMÉRICA (mantida igual)
# =============================================================================

numerical_cols = df.select_dtypes(include=np.number).columns.tolist()
if numerical_cols:
    st.header("📈 Análise Numérica")
    
    # ... (código de análise numérica mantido igual) ...

# =============================================================================
# ANÁLISE CATEGÓRICA (mantida igual)
# =============================================================================

categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
if categorical_cols:
    st.header("📊 Análise Categórica")
    
    # ... (código de análise categórica mantido igual) ...

# =============================================================================
# GERAÇÃO DE RELATÓRIOS (ATUALIZADA)
# =============================================================================

st.markdown("---")
st.header("📤 Exportar Relatório")

if st.button("Gerar Relatório em PDF", use_container_width=True, type="primary"):
    if not num_figs and not cat_figs:
        st.warning("⚠️ Selecione pelo menos uma coluna para análise antes de gerar o relatório!")
    else:
        with st.spinner("Criando relatório profissional..."):
            try:
                # Salvar gráficos temporariamente
                num_image_paths = [save_plot(fig) for fig in num_figs] if num_figs else []
                cat_image_paths = [save_plot(fig) for fig in cat_figs] if cat_figs else []
                
                # Gerar PDF diretamente em memória
                pdf_bytes = create_pdf_report(
                    df, 
                    logo_path, 
                    num_image_paths, 
                    cat_image_paths
                )
                
                # Criar botão de download
                st.success("✅ Relatório gerado com sucesso!")
                
                # Método 1: Download button nativo do Streamlit (funciona na maioria dos navegadores)
                st.download_button(
                    label="⬇️ Baixar Relatório PDF",
                    data=pdf_bytes,
                    file_name="relatorio_analise.pdf",
                    mime="application/pdf"
                )
                
                # Método 2: Link alternativo para navegadores problemáticos
                st.markdown(
                    f'<a href="data:application/pdf;base64,{base64.b64encode(pdf_bytes).decode()}" download="relatorio_analise.pdf">'
                    '📥 Alternativa: Clique aqui para baixar o relatório</a>',
                    unsafe_allow_html=True
                )
                
            except Exception as e:
                st.error(f"Erro ao gerar relatório: {str(e)}")
                st.text(traceback.format_exc())  # Mostrar traceback completo para debug
            finally:
                # Limpeza de arquivos temporários
                all_temp_files = []
                if logo_path:
                    all_temp_files.append(logo_path)
                all_temp_files.extend(num_image_paths)
                all_temp_files.extend(cat_image_paths)
                cleanup_temp_files(*all_temp_files)
