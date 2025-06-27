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
Versão: 1.0
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

def create_pdf_report(df, logo_path, num_images=[], cat_images=[], filename="relatorio.pdf"):
    """
    Gera relatório PDF profissional com análise de dados.
    
    Parâmetros:
        df (DataFrame): Conjunto de dados a ser analisado
        logo_path (str): Caminho para o arquivo de logo
        num_images (list): Lista de caminhos para imagens de análises numéricas
        cat_images (list): Lista de caminhos para imagens de análises categóricas
        filename (str): Nome do arquivo de saída
    
    Retorna:
        str: Caminho para o arquivo PDF gerado
    """
    # Configurar PDF em formato paisagem (landscape)
    pdf = FPDF(orientation='L')
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=10)
    
    # Adicionar logo se existir
    if logo_path:
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
                img_width = 260
                x_position = (pdf.w - img_width) / 2
                pdf.image(img_path, x=x_position, w=img_width)
                pdf.ln(5)
    
    # Salvar PDF
    pdf.output(filename)
    return filename

def get_binary_file_downloader_html(bin_file, file_label='File'):
    """Gera link HTML para download de arquivo"""
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        bin_str = base64.b64encode(data).decode()
        href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{os.path.basename(bin_file)}">Clique para baixar {file_label}</a>'
        return href
    except Exception as e:
        st.error(f"Erro ao gerar link de download: {str(e)}")
        return ""

def save_plot(fig):
    """Salva figura matplotlib em arquivo temporário"""
    with NamedTemporaryFile(delete=False, suffix='.png') as tmpfile:
        fig.savefig(tmpfile.name, bbox_inches='tight', dpi=150)
        return tmpfile.name

# =============================================================================
# PÁGINA INICIAL
# =============================================================================

def show_homepage():
    """Exibe a página inicial com apresentação do sistema"""
    # CSS personalizado moderno
    st.markdown("""
    <style>
        /* Estilos gerais */
        .stApp {
            background-color: #f8fafc;
        }
        
        /* Seção hero com gradiente moderno */
        .hero-section {
            background: linear-gradient(135deg, #1a3a8f 0%, #2563eb 100%);
            border-radius: 16px;
            padding: 4rem 2rem;
            margin: -1rem -1rem 3rem -1rem;
            text-align: center;
            color: white;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }
        
        .title-text {
            font-size: 3.5rem !important;
            font-weight: 800 !important;
            color: white !important;
            margin-bottom: 1rem;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        .subtitle-text {
            font-size: 1.5rem !important;
            color: rgba(255, 255, 255, 0.9) !important;
            margin-bottom: 2rem;
            font-weight: 400;
        }
        
        /* Cards de recursos modernos */
        .feature-card {
            border-radius: 12px;
            padding: 2rem 1.5rem;
            background-color: white;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
            transition: all 0.3s ease;
            height: 100%;
            border: 1px solid #e2e8f0;
        }
        
        .feature-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
            border-color: #93c5fd;
        }
        
        .feature-icon {
            font-size: 2.5rem;
            margin-bottom: 1.5rem;
            color: #1a3a8f;
            background: #e0f2fe;
            width: 70px;
            height: 70px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            margin-left: auto;
            margin-right: auto;
        }
        
        .feature-title {
            font-size: 1.3rem;
            font-weight: 700;
            margin-bottom: 1rem;
            color: #1e293b;
            text-align: center;
        }
        
        .feature-desc {
            color: #64748b;
            font-size: 1rem;
            text-align: center;
            line-height: 1.6;
        }
        
        /* Seção "Como Funciona" */
        .how-to-container {
            background-color: white;
            border-radius: 16px;
            padding: 3rem;
            margin-top: 3rem;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
            border: 1px solid #e2e8f0;
        }
        
        .how-to-title {
            font-size: 2rem;
            font-weight: 700;
            color: #1e293b;
            text-align: center;
            margin-bottom: 2rem;
            position: relative;
        }
        
        .how-to-title:after {
            content: '';
            display: block;
            width: 80px;
            height: 4px;
            background: #2563eb;
            margin: 0.5rem auto 0;
            border-radius: 2px;
        }
        
        .step-card {
            background-color: white;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            transition: all 0.3s ease;
        }
        
        .step-card:hover {
            transform: translateX(5px);
        }
        
        .step-number {
            font-size: 1.5rem;
            font-weight: 800;
            color: #2563eb;
            margin-bottom: 0.5rem;
            display: inline-block;
            background: #e0f2fe;
            width: 40px;
            height: 40px;
            text-align: center;
            line-height: 40px;
            border-radius: 50%;
        }
        
        .step-title {
            font-size: 1.2rem;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 0.5rem;
        }
        
        .step-desc {
            color: #475569;
            line-height: 1.6;
        }
        
        /* Botão CTA moderno */
        .cta-button {
            display: inline-block;
            padding: 1rem 2rem;
            font-size: 1.2rem;
            font-weight: 600;
            text-align: center;
            border-radius: 12px;
            background: linear-gradient(to right, #1a3a8f, #2563eb);
            color: white !important;
            margin: 2rem auto 0;
            text-decoration: none;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(26, 58, 143, 0.3);
            border: none;
            cursor: pointer;
        }
        
        .cta-button:hover {
            background: linear-gradient(to right, #2563eb, #1e40af);
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(26, 58, 143, 0.4);
            color: white;
        }
        
        /* Divisor estilizado */
        .styled-divider {
            border: none;
            height: 1px;
            background: linear-gradient(to right, transparent, #cbd5e1, transparent);
            margin: 3rem 0;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Seção Hero com gradiente
    st.markdown("""
    <div class="hero-section">
        <h1 class="title-text">Report Lab</h1>
        <p class="subtitle-text">Transforme dados complexos em relatórios profissionais com poucos cliques</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Seção de recursos
    st.markdown("""
    <div style="text-align: center; margin-bottom: 3rem;">
        <h2 style="font-size: 2rem; color: #1e293b; font-weight: 700;">Recursos Exclusivos</h2>
        <p style="color: #64748b; max-width: 700px; margin: 0 auto;">Uma plataforma completa para análise de dados e criação de relatórios automatizados</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Cards de recursos em 3 colunas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📊</div>
            <h3 class="feature-title">Análise Automatizada</h3>
            <p class="feature-desc">Visualizações inteligentes que revelam padrões, tendências e outliers em seus dados automaticamente.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📑</div>
            <h3 class="feature-title">Relatórios Profissionais</h3>
            <p class="feature-desc">PDFs prontos para impressão com layout otimizado e todas as análises organizadas.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">⚡</div>
            <h3 class="feature-title">Integração Simples</h3>
            <p class="feature-desc">Conecte-se a diversas fontes de dados e gere insights em minutos, não em horas.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Chamada para ação centralizada
    st.markdown("""
    <div style="text-align: center;">
        <a href="#como-usar" class="cta-button">
            Comece Agora &rarr;
        </a>
    </div>
    """, unsafe_allow_html=True)
    
    # Divisor estilizado
    st.markdown('<hr class="styled-divider">', unsafe_allow_html=True)
    
    # Seção "Como Funciona" em container destacado
    st.markdown("""
    <div class="how-to-container">
        <h2 class="how-to-title" id="como-usar">Como Funciona</h2>
        <div style="display: flex; flex-wrap: wrap; gap: 1.5rem;">
            <div style="flex: 1; min-width: 300px;">
                <div class="step-card">
                    <div class="step-number">1</div>
                    <h3 class="step-title">Carregue seus dados</h3>
                    <p class="step-desc">Importe arquivos CSV ou Excel diretamente pela interface intuitiva.</p>
                </div>
                <div class="step-card">
                    <div class="step-number">2</div>
                    <h3 class="step-title">Adicione sua marca</h3>
                    <p class="step-desc">Personalize os relatórios com o logo e cores da sua empresa.</p>
                </div>
            </div>
            <div style="flex: 1; min-width: 300px;">
                <div class="step-card">
                    <div class="step-number">3</div>
                    <h3 class="step-title">Selecione as análises</h3>
                    <p class="step-desc">Escolha quais métricas e visualizações incluir no relatório.</p>
                </div>
                <div class="step-card">
                    <div class="step-number">4</div>
                    <h3 class="step-title">Gere e compartilhe</h3>
                    <p class="step-desc">Exporte o PDF profissional ou compartilhe diretamente com sua equipe.</p>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# =============================================================================
# BARRA LATERAL (SIDEBAR)
# =============================================================================

with st.sidebar:
    # Estilos para sidebar
    st.markdown("""
    <style>
        .sidebar-header {
            color: #1a3a8f;
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
            text-align: center;
        }
        .sidebar-section {
            padding: 1rem;
            background-color: #f0f9ff;
            border-radius: 12px;
            margin-bottom: 1.5rem;
        }
        .sidebar-section-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: #1a3a8f;
            margin-bottom: 0.5rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Título da sidebar
    st.markdown('<div class="sidebar-header">Report Lab</div>', unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)
    
    # Seção de upload de dados
    with st.container():
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-section-title">1. Carregar Dados</div>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Selecione seu arquivo (CSV ou Excel)",
            type=["csv", "xlsx"],
            label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)  # Fechar a div da seção
    
    # Seção de logo
    with st.container():
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-section-title">2. Adicionar Logo</div>', unsafe_allow_html=True)
        logo_file = st.file_uploader(
            "Envie sua logo (opcional)",
            type=["png", "jpg", "jpeg"],
            label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)  # Fechar a div da seção

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
# SEÇÃO DE VISÃO GERAL
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
# ANÁLISE NUMÉRICA
# =============================================================================

numerical_cols = df.select_dtypes(include=np.number).columns.tolist()
if numerical_cols:
    st.header("📈 Análise Numérica")
    
    # Seleção de colunas
    selected_num_cols = st.multiselect(
        "Selecione colunas numéricas para análise", 
        numerical_cols,
        help="Selecione várias colunas para análise"
    )
    
    # Geração de gráficos
    for col in selected_num_cols:
        with st.expander(f"Análise da coluna: **{col}**", expanded=True):
            col1, col2 = st.columns(2)
            
            # Histograma
            with col1:
                st.subheader(f"Distribuição de {col}")
                fig1, ax1 = plt.subplots(figsize=(8, 4))
                sns.histplot(df[col], kde=True, color='#1a3a8f')
                st.pyplot(fig1)
                num_figs.append(fig1)
                plt.close(fig1)
            
            # Boxplot
            with col2:
                st.subheader(f"Boxplot de {col}")
                fig2, ax2 = plt.subplots(figsize=(8, 4))
                sns.boxplot(x=df[col], color='#1e4ed8')
                st.pyplot(fig2)
                num_figs.append(fig2)
                plt.close(fig2)

# =============================================================================
# ANÁLISE CATEGÓRICA
# =============================================================================

categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
if categorical_cols:
    st.header("📊 Análise Categórica")
    
    # Seleção de colunas
    selected_cat_cols = st.multiselect(
        "Selecione colunas categóricas para análise", 
        categorical_cols,
        help="Selecione várias colunas para análise"
    )
    
    # Configuração de top N
    top_n = st.slider("Mostrar top N valores", 5, 20, 10)
    
    # Geração de gráficos
    for col in selected_cat_cols:
        with st.expander(f"Análise da coluna: **{col}**", expanded=True):
            counts = df[col].value_counts().nlargest(top_n)
            
            fig, ax = plt.subplots(figsize=(10, 5))
            sns.barplot(x=counts.values, y=counts.index, ax=ax, palette='Blues_d')
            plt.title(f'Top {top_n} Valores em {col}')
            st.pyplot(fig)
            cat_figs.append(fig)
            plt.close(fig)

# =============================================================================
# GERAÇÃO DE RELATÓRIOS
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
                
                # Definir caminho absoluto para o relatório
                report_path = os.path.abspath("relatorio_analise.pdf")
                
                # Gerar PDF
                create_pdf_report(
                    df, 
                    logo_path, 
                    num_image_paths, 
                    cat_image_paths,
                    filename=report_path
                )
                
                # Verificar se o arquivo foi criado
                if os.path.exists(report_path):
                    st.success("✅ Relatório gerado com sucesso!")
                    
                    # Botão de download
                    with open(report_path, "rb") as f:
                        st.download_button(
                            "Baixar Relatório PDF",
                            f,
                            file_name="relatorio_analise.pdf",
                            mime="application/pdf"
                        )
                else:
                    st.error("Falha ao gerar o relatório PDF")
                
            except Exception as e:
                st.error(f"Erro ao gerar relatório: {str(e)}")
            finally:
                # Limpeza de arquivos temporários
                cleanup_temp_files(logo_path, *num_image_paths, *cat_image_paths)
