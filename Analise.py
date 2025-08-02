import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import random
from typing import Dict, List
import time

# ==================== CONFIGURAÇÃO DA PÁGINA ====================
st.set_page_config(
    page_title="Sistema de Controle de Acuracidade",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== ESTILOS CSS ====================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #1f77b4;
    }
    .success-metric { border-left-color: #28a745; }
    .warning-metric { border-left-color: #ffc107; }
    .danger-metric { border-left-color: #dc3545; }
    .upload-section {
        background-color: #e8f4fd;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 2px dashed #1f77b4;
        margin-bottom: 2rem;
    }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

# ==================== CLASSE PRINCIPAL ====================
class SistemaControleEstoque:
    """Sistema de controle de acuracidade de estoque"""
    
    def __init__(self):
        """Inicializa o sistema e session states"""
        self._inicializar_session_states()

    def _inicializar_session_states(self):
        """Inicializa todas as variáveis de sessão"""
        session_vars = {
            'estoque_sistema': {},
            'estoque_fisico': {},
            'movimentacoes': [],
            'divergencias': [],
            'contagens_ciclicas': [],
            'dados_carregados': False
        }
        
        for var, default_value in session_vars.items():
            if var not in st.session_state:
                st.session_state[var] = default_value

    # ==================== MÉTODOS DE CARREGAMENTO ====================
    
    def carregar_planilha_sistema(self, arquivo_excel) -> bool:
        """
        Carrega dados do estoque do sistema
        
        Args:
            arquivo_excel: Arquivo Excel uploadado
            
        Returns:
            bool: True se carregado com sucesso
        """
        colunas_obrigatorias = ['codigo', 'nome', 'categoria', 'quantidade', 'valor_unitario']
        
        try:
            df = pd.read_excel(arquivo_excel)
            
            # Validar colunas
            if not self._validar_colunas(df, colunas_obrigatorias):
                return False
            
            # Limpar e carregar dados
            st.session_state.estoque_sistema = {}
            
            for _, row in df.iterrows():
                codigo = str(row['codigo']).strip()
                st.session_state.estoque_sistema[codigo] = {
                    'quantidade': int(row['quantidade']),
                    'nome': str(row['nome']).strip(),
                    'categoria': str(row['categoria']).strip(),
                    'valor_unitario': float(row['valor_unitario']),
                    'ultima_contagem': datetime.now() - timedelta(days=random.randint(1, 30))
                }
            
            st.success(f"✅ Dados do sistema carregados: {len(st.session_state.estoque_sistema)} produtos")
            return True
            
        except Exception as e:
            st.error(f"Erro ao carregar planilha do sistema: {str(e)}")
            return False

    def carregar_planilha_fisico(self, arquivo_excel) -> bool:
        """
        Carrega dados do estoque físico
        
        Args:
            arquivo_excel: Arquivo Excel uploadado
            
        Returns:
            bool: True se carregado com sucesso
        """
        colunas_obrigatorias = ['codigo', 'quantidade_fisica']
        
        try:
            df = pd.read_excel(arquivo_excel)
            
            # Validar colunas
            if not self._validar_colunas(df, colunas_obrigatorias):
                return False
            
            # Limpar e carregar dados
            st.session_state.estoque_fisico = {}
            produtos_nao_encontrados = []
            
            for _, row in df.iterrows():
                codigo = str(row['codigo']).strip()
                if codigo in st.session_state.estoque_sistema:
                    st.session_state.estoque_fisico[codigo] = int(row['quantidade_fisica'])
                else:
                    produtos_nao_encontrados.append(codigo)
            
            if produtos_nao_encontrados:
                st.warning(f"Produtos não encontrados no sistema: {', '.join(produtos_nao_encontrados[:5])}")
            
            st.success(f"✅ Dados físicos carregados: {len(st.session_state.estoque_fisico)} produtos")
            return True
            
        except Exception as e:
            st.error(f"Erro ao carregar planilha física: {str(e)}")
            return False

    def _validar_colunas(self, df: pd.DataFrame, colunas_obrigatorias: List[str]) -> bool:
        """Valida se todas as colunas obrigatórias estão presentes"""
        colunas_faltantes = [col for col in colunas_obrigatorias if col not in df.columns]
        
        if colunas_faltantes:
            st.error(f"Colunas obrigatórias faltando: {', '.join(colunas_faltantes)}")
            st.info(f"Colunas obrigatórias: {', '.join(colunas_obrigatorias)}")
            return False
        
        return True

    # ==================== MÉTODOS DE CÁLCULO ====================
    
    def calcular_acuracidade_inicial(self) -> float:
        """Calcula a acuracidade inicial baseada nos dados carregados"""
        if not st.session_state.estoque_sistema or not st.session_state.estoque_fisico:
            return 78.0
        
        produtos_comuns = self._obter_produtos_comuns()
        if not produtos_comuns:
            return 78.0
        
        produtos_ok = sum(1 for codigo in produtos_comuns 
                         if st.session_state.estoque_sistema[codigo]['quantidade'] == 
                            st.session_state.estoque_fisico[codigo])
        
        return (produtos_ok / len(produtos_comuns)) * 100

    def calcular_economia_projetada(self) -> float:
        """Calcula economia mensal baseada nas divergências encontradas"""
        if not st.session_state.estoque_sistema or not st.session_state.estoque_fisico:
            return 36700
        
        produtos_comuns = self._obter_produtos_comuns()
        valor_total_divergencias = 0
        
        for codigo in produtos_comuns:
            qtd_sistema = st.session_state.estoque_sistema[codigo]['quantidade']
            qtd_fisica = st.session_state.estoque_fisico[codigo]
            divergencia = abs(qtd_fisica - qtd_sistema)
            valor_unitario = st.session_state.estoque_sistema[codigo]['valor_unitario']
            valor_total_divergencias += divergencia * valor_unitario
        
        # Economia mensal = 80% das divergências encontradas
        economia_mensal = valor_total_divergencias * 0.8
        return max(economia_mensal, 5000)

    def obter_produtos_divergentes(self) -> List[Dict]:
        """Retorna lista detalhada de produtos com divergências"""
        if not st.session_state.estoque_sistema or not st.session_state.estoque_fisico:
            return []
        
        produtos_divergentes = []
        produtos_comuns = self._obter_produtos_comuns()
        
        for codigo in produtos_comuns:
            qtd_sistema = st.session_state.estoque_sistema[codigo]['quantidade']
            qtd_fisica = st.session_state.estoque_fisico[codigo]
            divergencia = qtd_fisica - qtd_sistema
            
            if divergencia != 0:
                produto_info = st.session_state.estoque_sistema[codigo]
                produtos_divergentes.append({
                    'codigo': codigo,
                    'nome': produto_info['nome'],
                    'categoria': produto_info['categoria'],
                    'qtd_sistema': qtd_sistema,
                    'qtd_fisica': qtd_fisica,
                    'divergencia_unidades': divergencia,
                    'divergencia_percentual': (divergencia / qtd_sistema * 100) if qtd_sistema > 0 else 0,
                    'valor_unitario': produto_info['valor_unitario'],
                    'valor_divergencia': abs(divergencia) * produto_info['valor_unitario'],
                    'tipo': 'Sobra' if divergencia > 0 else 'Falta'
                })
        
        return sorted(produtos_divergentes, key=lambda x: abs(x['valor_divergencia']), reverse=True)

    def _obter_produtos_comuns(self) -> set:
        """Retorna produtos presentes em ambos os estoques"""
        return set(st.session_state.estoque_sistema.keys()) & set(st.session_state.estoque_fisico.keys())

    # ==================== MÉTODOS DE CONTAGEM ====================
    
    def realizar_contagem_ciclica(self, codigo: str) -> Dict:
        """Realiza contagem cíclica de um produto específico"""
        if codigo not in st.session_state.estoque_sistema or codigo not in st.session_state.estoque_fisico:
            return {"erro": "Produto não encontrado em ambos os estoques"}
        
        timestamp = datetime.now()
        qtd_sistema = st.session_state.estoque_sistema[codigo]['quantidade']
        qtd_fisica = st.session_state.estoque_fisico[codigo]
        divergencia = qtd_fisica - qtd_sistema
        
        contagem = {
            'timestamp': timestamp,
            'codigo': codigo,
            'nome': st.session_state.estoque_sistema[codigo]['nome'],
            'categoria': st.session_state.estoque_sistema[codigo]['categoria'],
            'qtd_sistema': qtd_sistema,
            'qtd_fisica': qtd_fisica,
            'divergencia': divergencia,
            'valor_divergencia': abs(divergencia) * st.session_state.estoque_sistema[codigo]['valor_unitario'],
            'status': 'OK' if divergencia == 0 else 'DIVERGENTE'
        }
        
        st.session_state.contagens_ciclicas.append(contagem)
        
        if divergencia != 0:
            st.session_state.divergencias.append(contagem)
            
        return contagem

    def calcular_acuracidade(self) -> Dict:
        """Calcula métricas de acuracidade baseadas nas contagens realizadas"""
        if not st.session_state.contagens_ciclicas:
            return {"erro": "Nenhuma contagem realizada"}
        
        total_contagens = len(st.session_state.contagens_ciclicas)
        contagens_ok = len([c for c in st.session_state.contagens_ciclicas if c['status'] == 'OK'])
        acuracidade_percentual = (contagens_ok / total_contagens) * 100
        
        valor_total_divergencias = sum([d['valor_divergencia'] for d in st.session_state.divergencias])
        valor_total_estoque = sum([
            info['quantidade'] * info['valor_unitario'] 
            for info in st.session_state.estoque_sistema.values()
        ])
        
        impacto_financeiro_percent = (valor_total_divergencias / valor_total_estoque) * 100 if valor_total_estoque > 0 else 0
        
        return {
            'acuracidade_percentual': acuracidade_percentual,
            'total_contagens': total_contagens,
            'produtos_divergentes': len(st.session_state.divergencias),
            'valor_divergencias': valor_total_divergencias,
            'impacto_financeiro_percent': impacto_financeiro_percent,
            'valor_total_estoque': valor_total_estoque
        }

    # ==================== MÉTODOS DE SIMULAÇÃO ====================
    
    def gerar_dados_simulacao(self, dias: int = 30) -> pd.DataFrame:
        """Gera dados de simulação da evolução da acuracidade"""
        acuracidade_inicial = self.calcular_acuracidade_inicial()
        resultados = []
        
        # Definir meta final baseada na situação atual
        if acuracidade_inicial >= 90:
            meta_final = min(98, acuracidade_inicial + 5)
        elif acuracidade_inicial >= 80:
            meta_final = 95
        else:
            meta_final = 92
        
        for dia in range(dias + 1):
            if dia == 0:
                acuracidade = acuracidade_inicial
            elif dia <= 10:  # Implementação
                progresso = dia / 10
                melhoria = (meta_final - acuracidade_inicial) * 0.4 * progresso
                acuracidade = acuracidade_inicial + melhoria
            elif dia <= 20:  # Estabilização
                progresso = (dia - 10) / 10
                melhoria_base = (meta_final - acuracidade_inicial) * 0.4
                melhoria_adicional = (meta_final - acuracidade_inicial) * 0.4 * progresso
                acuracidade = acuracidade_inicial + melhoria_base + melhoria_adicional
            else:  # Otimização
                progresso = (dia - 20) / 10
                melhoria_base = (meta_final - acuracidade_inicial) * 0.8
                melhoria_final = (meta_final - acuracidade_inicial) * 0.2 * progresso
                acuracidade = acuracidade_inicial + melhoria_base + melhoria_final
            
            # Adicionar variação aleatória
            acuracidade += random.uniform(-0.5, 0.5)
            acuracidade = max(acuracidade_inicial - 2, min(meta_final + 1, acuracidade))
            
            fase = 'Implementação' if dia <= 10 else 'Estabilização' if dia <= 20 else 'Otimização'
            
            resultados.append({
                'dia': dia,
                'acuracidade': acuracidade,
                'fase': fase
            })
        
        return pd.DataFrame(resultados)

# ==================== FUNÇÕES DE GRÁFICOS ====================

def criar_grafico_evolucao() -> go.Figure:
    """Cria gráfico de evolução da acuracidade"""
    sistema = SistemaControleEstoque()
    dados = sistema.gerar_dados_simulacao(30)
    acuracidade_inicial = sistema.calcular_acuracidade_inicial()
    
    fig = go.Figure()
    cores_fases = {'Implementação': '#ff7f7f', 'Estabilização': '#ffbf7f', 'Otimização': '#7fbf7f'}
    
    for fase in dados['fase'].unique():
        dados_fase = dados[dados['fase'] == fase]
        fig.add_trace(go.Scatter(
            x=dados_fase['dia'],
            y=dados_fase['acuracidade'],
            mode='lines+markers',
            name=fase,
            line=dict(color=cores_fases[fase], width=3),
            marker=dict(size=6)
        ))
    
    fig.add_hline(y=95, line_dash="dash", line_color="red", annotation_text="Meta: 95%")
    fig.add_hline(y=acuracidade_inicial, line_dash="dot", line_color="gray", 
                  annotation_text=f"Situação Atual: {acuracidade_inicial:.1f}%")
    
    fig.update_layout(
        title="Evolução da Acuracidade (Projeção 30 dias)",
        xaxis_title="Dias",
        yaxis_title="Acuracidade (%)",
        height=500,
        showlegend=True
    )
    
    return fig

def criar_grafico_comparativo() -> go.Figure:
    """Cria gráfico comparativo antes vs depois"""
    sistema = SistemaControleEstoque()
    acuracidade_inicial = sistema.calcular_acuracidade_inicial()
    acuracidade_final = min(95.8, acuracidade_inicial + 15)
    
    # Calcular métricas baseadas nos dados reais
    produtos_divergentes = sistema.obter_produtos_divergentes()
    perdas_atuais = sum([p['valor_divergencia'] for p in produtos_divergentes]) / 1000
    perdas_futuras = perdas_atuais * 0.15
    
    tempo_atual = 120 if acuracidade_inicial < 80 else 90 if acuracidade_inicial < 90 else 60
    tempo_futuro = 30
    
    produtividade_atual = max(50, acuracidade_inicial * 0.8)
    produtividade_futura = min(95, produtividade_atual + 25)
    
    metricas = ['Acuracidade (%)', 'Tempo Recontagem (h)', 'Perdas (R$ mil)', 'Produtividade (%)']
    antes = [acuracidade_inicial, tempo_atual, perdas_atuais, produtividade_atual]
    depois = [acuracidade_final, tempo_futuro, perdas_futuras, produtividade_futura]
    
    fig = go.Figure(data=[
        go.Bar(name='Antes', x=metricas, y=antes, marker_color='#ff7f7f'),
        go.Bar(name='Depois', x=metricas, y=depois, marker_color='#7fbf7f')
    ])
    
    fig.update_layout(
        title="Comparativo: Antes vs Depois (Baseado nos seus dados)",
        barmode='group',
        height=500
    )
    
    return fig

def criar_grafico_roi() -> go.Figure:
    """Cria gráfico de ROI e payback"""
    sistema = SistemaControleEstoque()
    economia_mensal = sistema.calcular_economia_projetada()
    
    meses = list(range(0, 13))
    investimento_inicial = -50000
    
    fluxo_caixa = [investimento_inicial]
    for mes in range(1, 13):
        fluxo_caixa.append(fluxo_caixa[-1] + economia_mensal)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=meses,
        y=fluxo_caixa,
        mode='lines+markers',
        name='Fluxo de Caixa Acumulado',
        line=dict(color='#1f77b4', width=4),
        marker=dict(size=8)
    ))
    
    fig.add_hline(y=0, line_dash="dash", line_color="black")
    
    # Calcular payback
    payback_mes = next((i for i, v in enumerate(fluxo_caixa) if v >= 0), 12)
    if payback_mes < 12:
        fig.add_trace(go.Scatter(
            x=[payback_mes],
            y=[fluxo_caixa[payback_mes]],
            mode='markers',
            name=f'Payback: {payback_mes} meses',
            marker=dict(color='gold', size=15, symbol='star')
        ))
    
    fig.update_layout(
        title=f"Análise de ROI - Economia Mensal: R$ {economia_mensal:,.0f}",
        xaxis_title="Meses",
        yaxis_title="Fluxo de Caixa (R$)",
        height=500
    )
    
    return fig

def criar_grafico_divergencias() -> go.Figure:
    """Cria gráfico de divergências por categoria"""
    if not st.session_state.divergencias:
        # Dados de exemplo se não há divergências
        categorias = ['Eletrônicos', 'Informática', 'Eletrodomésticos', 'Roupas', 'Calçados', 'Cosméticos']
        valores = [18500, 12300, 8700, 4200, 3800, 2500]
    else:
        # Usar dados reais das divergências
        df_div = pd.DataFrame(st.session_state.divergencias)
        divergencias_categoria = df_div.groupby('categoria')['valor_divergencia'].sum()
        categorias = divergencias_categoria.index.tolist()
        valores = divergencias_categoria.values.tolist()
    
    fig = go.Figure(data=[go.Pie(
        labels=categorias, 
        values=valores,
        hole=0.3,
        textinfo='label+percent+value',
        texttemplate='%{label}<br>%{percent}<br>R$ %{value:,.0f}'
    )])
    
    fig.update_layout(
        title="Divergências por Categoria (R$)",
        height=500
    )
    
    return fig

# ==================== FUNÇÕES DE INTERFACE ====================

def exibir_upload_section():
    """Exibe seção de upload de planilhas"""
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    st.subheader("📁 Carregamento de Dados")
    
    col1, col2 = st.columns(2)
    sistema = SistemaControleEstoque()
    
    with col1:
        st.write("**1. Estoque do Sistema**")
        st.write("Colunas: codigo, nome, categoria, quantidade, valor_unitario")
        arquivo_sistema = st.file_uploader(
            "Carregar planilha do estoque do sistema",
            type=['xlsx', 'xls'],
            key="sistema"
        )
        
        if arquivo_sistema:
            if sistema.carregar_planilha_sistema(arquivo_sistema):
                st.session_state.dados_carregados = True
    
    with col2:
        st.write("**2. Estoque Físico (Contagem)**")
        st.write("Colunas: codigo, quantidade_fisica")
        arquivo_fisico = st.file_uploader(
            "Carregar planilha do estoque físico",
            type=['xlsx', 'xls'],
            key="fisico"
        )
        
        if arquivo_fisico and st.session_state.estoque_sistema:
            sistema.carregar_planilha_fisico(arquivo_fisico)
    
    st.markdown('</div>', unsafe_allow_html=True)

def exibir_sidebar_controles():
    """Exibe controles da sidebar"""
    sistema = SistemaControleEstoque()
    
    st.sidebar.header("🔧 Controles do Sistema")
    st.sidebar.subheader("Realizar Contagens")
    
    produtos_disponiveis = list(sistema._obter_produtos_comuns())
    
    if not produtos_disponiveis:
        st.sidebar.error("Nenhum produto comum encontrado entre as planilhas")
        return
    
    produto_selecionado = st.sidebar.selectbox(
        "Selecione um produto:",
        produtos_disponiveis,
        format_func=lambda x: f"{x} - {st.session_state.estoque_sistema[x]['nome']}"
    )
    
    if st.sidebar.button("Realizar Contagem"):
        with st.spinner("Realizando contagem..."):
            time.sleep(1)
            resultado = sistema.realizar_contagem_ciclica(produto_selecionado)
            
            if 'erro' in resultado:
                st.sidebar.error(resultado['erro'])
            elif resultado['status'] == 'OK':
                st.sidebar.success(f"Contagem OK: {resultado['nome']}")
            else:
                st.sidebar.error(f"Divergência: {resultado['nome']}")
                st.sidebar.write(f"Diferença: {resultado['divergencia']} unidades")
                st.sidebar.write(f"Impacto: R$ {resultado['valor_divergencia']:,.2f}")
    
    if st.sidebar.button("Simular Contagens Múltiplas"):
        with st.spinner("Realizando múltiplas contagens..."):
            progress_bar = st.sidebar.progress(0)
            for i, codigo in enumerate(produtos_disponiveis):
                resultado = sistema.realizar_contagem_ciclica(codigo)
                if 'erro' not in resultado:
                    progress_bar.progress((i + 1) / len(produtos_disponiveis))
                time.sleep(0.2)
            st.sidebar.success("Todas as contagens realizadas!")
    
    if st.sidebar.button("Reset Contagens"):
        st.session_state.movimentacoes = []
        st.session_state.divergencias = []
        st.session_state.contagens_ciclicas = []
        st.sidebar.success("Contagens resetadas!")
    
    # Informações dos dados carregados
    st.sidebar.subheader("📊 Dados Carregados")
    st.sidebar.write(f"Produtos sistema: {len(st.session_state.estoque_sistema)}")
    st.sidebar.write(f"Produtos físico: {len(st.session_state.estoque_fisico)}")
    st.sidebar.write(f"Produtos válidos: {len(produtos_disponiveis)}")

def exibir_kpis():
    """Exibe KPIs principais"""
    sistema = SistemaControleEstoque()
    metricas = sistema.calcular_acuracidade()
    acuracidade_inicial = sistema.calcular_acuracidade_inicial()
    
    if 'erro' not in metricas:
        st.subheader("📈 KPIs Principais")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            acuracidade = metricas['acuracidade_percentual']
            cor = "success" if acuracidade >= 95 else "warning" if acuracidade >= 85 else "danger"
            st.markdown(f'<div class="metric-card {cor}-metric">', unsafe_allow_html=True)
            st.metric("Acuracidade", f"{acuracidade:.1f}%", 
                     delta=f"{acuracidade - acuracidade_inicial:+.1f}% vs baseline")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="metric-card danger-metric">', unsafe_allow_html=True)
            st.metric("Divergências", metricas['produtos_divergentes'], 
                     delta=f"-{15 - metricas['produtos_divergentes']} vs meta")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="metric-card warning-metric">', unsafe_allow_html=True)
            st.metric("Perdas", f"R$ {metricas['valor_divergencias']:,.0f}", 
                     delta=f"-R$ {45000 - metricas['valor_divergencias']:,.0f} vs atual")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col4:
            produtividade = 90 if acuracidade > 90 else 70
            st.markdown('<div class="metric-card success-metric">', unsafe_allow_html=True)
            st.metric("Produtividade", f"{produtividade}%", 
                     delta=f"+{produtividade - 60}% vs atual")
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        # Mostrar métricas iniciais
        st.subheader("📈 Análise Inicial dos Dados")
        
        produtos_divergentes = sistema.obter_produtos_divergentes()
        total_produtos = len(sistema._obter_produtos_comuns())
        total_divergencias = len(produtos_divergentes)
        valor_total_divergencias = sum([p['valor_divergencia'] for p in produtos_divergentes])
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown('<div class="metric-card danger-metric">', unsafe_allow_html=True)
            st.metric("Acuracidade Inicial", f"{acuracidade_inicial:.1f}%")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="metric-card warning-metric">', unsafe_allow_html=True)
            st.metric("Produtos Divergentes", f"{total_divergencias}/{total_produtos}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="metric-card danger-metric">', unsafe_allow_html=True)
            st.metric("Valor das Divergências", f"R$ {valor_total_divergencias:,.0f}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col4:
            economia_projetada = sistema.calcular_economia_projetada()
            st.markdown('<div class="metric-card success-metric">', unsafe_allow_html=True)
            st.metric("Economia Potencial/Mês", f"R$ {economia_projetada:,.0f}")
            st.markdown('</div>', unsafe_allow_html=True)

def exibir_tab_divergencias():
    """Exibe tab de análise de divergências"""
    st.subheader("🚨 Produtos com Divergências")
    
    sistema = SistemaControleEstoque()
    produtos_divergentes = sistema.obter_produtos_divergentes()
    
    if produtos_divergentes:
        # Separar por tipo
        sobras = [p for p in produtos_divergentes if p['tipo'] == 'Sobra']
        faltas = [p for p in produtos_divergentes if p['tipo'] == 'Falta']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Sobras no Estoque")
            if sobras:
                df_sobras = pd.DataFrame(sobras)
                st.dataframe(
                    df_sobras[['codigo', 'nome', 'categoria', 'divergencia_unidades', 
                              'divergencia_percentual', 'valor_divergencia']].round(2),
                    use_container_width=True
                )
                total_sobras = sum([p['divergencia_unidades'] for p in sobras])
                valor_sobras = sum([p['valor_divergencia'] for p in sobras])
                st.info(f"Total de sobras: {total_sobras} unidades (R$ {valor_sobras:,.2f})")
            else:
                st.success("Nenhuma sobra encontrada!")
        
        with col2:
            st.subheader("📉 Faltas no Estoque")
            if faltas:
                df_faltas = pd.DataFrame(faltas)
                st.dataframe(
                    df_faltas[['codigo', 'nome', 'categoria', 'divergencia_unidades', 
                              'divergencia_percentual', 'valor_divergencia']].round(2),
                    use_container_width=True
                )
                total_faltas = abs(sum([p['divergencia_unidades'] for p in faltas]))
                valor_faltas = sum([p['valor_divergencia'] for p in faltas])
                st.error(f"Total de faltas: {total_faltas} unidades (R$ {valor_faltas:,.2f})")
            else:
                st.success("Nenhuma falta encontrada!")
        
        # Resumo geral
        st.subheader("📊 Resumo das Divergências")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Produtos Divergentes", len(produtos_divergentes))
        with col2:
            total_valor = sum([p['valor_divergencia'] for p in produtos_divergentes])
            st.metric("Valor Total das Divergências", f"R$ {total_valor:,.2f}")
        with col3:
            if produtos_divergentes:
                maior_divergencia = max(produtos_divergentes, key=lambda x: abs(x['divergencia_unidades']))
                st.metric("Maior Divergência", f"{maior_divergencia['divergencia_unidades']} un")
        with col4:
            if produtos_divergentes:
                maior_valor = max(produtos_divergentes, key=lambda x: x['valor_divergencia'])
                st.metric("Maior Impacto (R$)", f"R$ {maior_valor['valor_divergencia']:,.2f}")
        
        # Top 10 divergências por valor
        st.subheader("🔥 Top 10 Divergências por Impacto Financeiro")
        top_10 = produtos_divergentes[:10]
        df_top10 = pd.DataFrame(top_10)
        
        fig_top10 = go.Figure(data=[
            go.Bar(
                x=df_top10['nome'],
                y=df_top10['valor_divergencia'],
                marker_color=['red' if x['tipo'] == 'Falta' else 'orange' for x in top_10],
                text=[f"{x['divergencia_unidades']:+} un" for x in top_10],
                textposition='auto'
            )
        ])
        
        fig_top10.update_layout(
            title="Produtos com Maior Impacto Financeiro",
            xaxis_title="Produtos",
            yaxis_title="Valor da Divergência (R$)",
            height=400,
            xaxis_tickangle=-45
        )
        
        st.plotly_chart(fig_top10, use_container_width=True)
        
    else:
        st.info("⚠️ Carregue as planilhas para ver as divergências dos seus produtos.")
        st.write("O sistema analisará automaticamente:")
        st.write("• Produtos com sobras (quantidade física > sistema)")
        st.write("• Produtos com faltas (quantidade física < sistema)")
        st.write("• Impacto financeiro de cada divergência")
        st.write("• Ranking dos produtos com maiores divergências")

def exibir_tab_dados():
    """Exibe tab de dados detalhados"""
    st.subheader("Dados Detalhados")
    
    # Mostrar resumo dos dados carregados
    st.write("**Resumo dos Dados Carregados:**")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.session_state.estoque_sistema:
            df_sistema = pd.DataFrame.from_dict(st.session_state.estoque_sistema, orient='index')
            df_sistema.reset_index(inplace=True)
            df_sistema.rename(columns={'index': 'codigo'}, inplace=True)
            st.write("**Estoque do Sistema:**")
            st.dataframe(df_sistema[['codigo', 'nome', 'categoria', 'quantidade', 'valor_unitario']], use_container_width=True)
    
    with col2:
        if st.session_state.estoque_fisico:
            df_fisico = pd.DataFrame(list(st.session_state.estoque_fisico.items()), 
                                   columns=['codigo', 'quantidade_fisica'])
            st.write("**Estoque Físico:**")
            st.dataframe(df_fisico, use_container_width=True)
    
    # Mostrar contagens realizadas
    if st.session_state.contagens_ciclicas:
        df_contagens = pd.DataFrame(st.session_state.contagens_ciclicas)
        df_contagens['timestamp'] = pd.to_datetime(df_contagens['timestamp'])
        
        st.write("**Últimas Contagens Realizadas:**")
        st.dataframe(
            df_contagens[['timestamp', 'codigo', 'nome', 'categoria', 'qtd_sistema', 
                         'qtd_fisica', 'divergencia', 'valor_divergencia', 'status']],
            use_container_width=True
        )
        
        if st.session_state.divergencias:
            st.write("**Estatísticas por Categoria:**")
            df_div = pd.DataFrame(st.session_state.divergencias)
            stats_categoria = df_div.groupby('categoria').agg({
                'valor_divergencia': ['sum', 'count', 'mean']
            }).round(2)
            st.dataframe(stats_categoria, use_container_width=True)
    else:
        st.info("Realize algumas contagens para ver os dados detalhados.")

# ==================== FUNÇÃO PRINCIPAL ====================

def main():
    """Função principal do dashboard"""
    
    # Header
    st.markdown('<h1 class="main-header">Sistema de Controle de Acuracidade de Estoque</h1>', 
                unsafe_allow_html=True)
    
    # Upload de planilhas
    exibir_upload_section()
    
    # Verificar se os dados foram carregados
    if not st.session_state.estoque_sistema:
        st.warning("⚠️ Por favor, carregue primeiro a planilha do estoque do sistema para continuar.")
        return
    
    if not st.session_state.estoque_fisico:
        st.warning("⚠️ Por favor, carregue a planilha do estoque físico para realizar as contagens.")
        return
    
    # Sidebar com controles
    exibir_sidebar_controles()
    
    # KPIs Principais
    exibir_kpis()
    
    # Tabs com análises
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Evolução", "Comparativo", "ROI", "Categorias", "Divergências", "Dados"
    ])
    
    with tab1:
        st.subheader("Evolução da Acuracidade (Projeção 30 dias)")
        fig_evolucao = criar_grafico_evolucao()
        st.plotly_chart(fig_evolucao, use_container_width=True)
        
        st.info("Interpretação: O gráfico mostra a evolução esperada da acuracidade "
               "com a implementação do sistema em 3 fases: Implementação, Estabilização e Otimização.")
    
    with tab2:
        st.subheader("Comparativo: Antes vs Depois")
        fig_comparativo = criar_grafico_comparativo()
        st.plotly_chart(fig_comparativo, use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.success("Melhorias Esperadas:")
            sistema_temp = SistemaControleEstoque()
            acuracidade_inicial = sistema_temp.calcular_acuracidade_inicial()
            acuracidade_final = min(95.8, acuracidade_inicial + 15)
            st.write(f"• Acuracidade: +{acuracidade_final - acuracidade_inicial:.1f} pontos percentuais")
            st.write("• Redução tempo recontagem: -75%")
            st.write("• Redução de perdas: -85%")
            st.write("• Aumento produtividade: +25%")
        
        with col2:
            st.info("Benefícios Adicionais:")
            st.write("• Maior confiabilidade dos dados")
            st.write("• Redução de stress da equipe")
            st.write("• Decisões mais assertivas")
            st.write("• Melhoria no atendimento")
    
    with tab3:
        st.subheader("Análise de ROI e Payback")
        fig_roi = criar_grafico_roi()
        st.plotly_chart(fig_roi, use_container_width=True)
        
        sistema = SistemaControleEstoque()
        economia_mensal = sistema.calcular_economia_projetada()
        payback_meses = max(1, int(50000 / economia_mensal)) if economia_mensal > 0 else 12
        roi_12_meses = ((economia_mensal * 12 - 50000) / 50000) * 100 if economia_mensal > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Investimento Total", "R$ 50.000")
        with col2:
            st.metric("Payback", f"{payback_meses} meses")
        with col3:
            st.metric("ROI (12 meses)", f"{roi_12_meses:.0f}%")
    
    with tab4:
        st.subheader("Distribuição das Divergências por Categoria")
        fig_divergencias = criar_grafico_divergencias()
        st.plotly_chart(fig_divergencias, use_container_width=True)
        
        if st.session_state.divergencias:
            st.info("Análise baseada nos dados carregados e contagens realizadas.")
        else:
            st.warning("Realize algumas contagens para ver a análise real das divergências.")
    
    with tab5:
        exibir_tab_divergencias()
    
    with tab6:
        exibir_tab_dados()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p><strong>Sistema de Controle de Acuracidade de Estoque</strong></p>
        <p>Desenvolvido para demonstração - Case de Entrevista | Engenharia da Computação → Análise de Estoque</p>
        <p><em>Transformando dados em decisões inteligentes</em></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()