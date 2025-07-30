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

st.set_page_config(
    page_title="Sistema de Controle de Acuracidade",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    .success-metric {
        border-left-color: #28a745;
    }
    .warning-metric {
        border-left-color: #ffc107;
    }
    .danger-metric {
        border-left-color: #dc3545;
    }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    .upload-section {
        background-color: #e8f4fd;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 2px dashed #1f77b4;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

class SistemaControleEstoque:
    def __init__(self):
        if 'estoque_sistema' not in st.session_state:
            st.session_state.estoque_sistema = {}
        if 'estoque_fisico' not in st.session_state:
            st.session_state.estoque_fisico = {}
        if 'movimentacoes' not in st.session_state:
            st.session_state.movimentacoes = []
        if 'divergencias' not in st.session_state:
            st.session_state.divergencias = []
        if 'contagens_ciclicas' not in st.session_state:
            st.session_state.contagens_ciclicas = []
        if 'dados_carregados' not in st.session_state:
            st.session_state.dados_carregados = False

    def carregar_planilha_sistema(self, arquivo_excel):
        """Carrega dados do estoque do sistema a partir de planilha Excel"""
        try:
            df = pd.read_excel(arquivo_excel)
            
            # Validar colunas obrigatórias
            colunas_obrigatorias = ['codigo', 'nome', 'categoria', 'quantidade', 'valor_unitario']
            colunas_faltantes = [col for col in colunas_obrigatorias if col not in df.columns]
            
            if colunas_faltantes:
                st.error(f"Colunas obrigatórias faltando: {', '.join(colunas_faltantes)}")
                st.info("Colunas obrigatórias: codigo, nome, categoria, quantidade, valor_unitario")
                return False
            
            # Limpar dados existentes
            st.session_state.estoque_sistema = {}
            
            # Carregar dados
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

    def carregar_planilha_fisico(self, arquivo_excel):
        """Carrega dados do estoque físico a partir de planilha Excel"""
        try:
            df = pd.read_excel(arquivo_excel)
            
            # Validar colunas obrigatórias
            colunas_obrigatorias = ['codigo', 'quantidade_fisica']
            colunas_faltantes = [col for col in colunas_obrigatorias if col not in df.columns]
            
            if colunas_faltantes:
                st.error(f"Colunas obrigatórias faltando: {', '.join(colunas_faltantes)}")
                st.info("Colunas obrigatórias: codigo, quantidade_fisica")
                return False
            
            # Limpar dados existentes
            st.session_state.estoque_fisico = {}
            
            # Carregar dados
            for _, row in df.iterrows():
                codigo = str(row['codigo']).strip()
                if codigo in st.session_state.estoque_sistema:
                    st.session_state.estoque_fisico[codigo] = int(row['quantidade_fisica'])
                else:
                    st.warning(f"Produto {codigo} não encontrado no estoque do sistema")
            
            st.success(f"✅ Dados físicos carregados: {len(st.session_state.estoque_fisico)} produtos")
            return True
            
        except Exception as e:
            st.error(f"Erro ao carregar planilha física: {str(e)}")
            return False

    def gerar_modelo_excel(self):
        """Gera modelos de planilhas Excel para download"""
        # Modelo para estoque do sistema
        modelo_sistema = pd.DataFrame({
            'codigo': ['A001', 'A002', 'A003', 'A004', 'A005'],
            'nome': ['Smartphone Galaxy', 'Notebook Dell', 'Tênis Nike', 'Camisa Polo', 'Perfume Importado'],
            'categoria': ['Eletrônicos', 'Informática', 'Calçados', 'Roupas', 'Cosméticos'],
            'quantidade': [150, 75, 200, 300, 80],
            'valor_unitario': [1200.00, 2500.00, 350.00, 89.90, 180.00]
        })
        
        # Modelo para estoque físico
        modelo_fisico = pd.DataFrame({
            'codigo': ['A001', 'A002', 'A003', 'A004', 'A005'],
            'quantidade_fisica': [145, 75, 195, 302, 78]
        })
        
        return modelo_sistema, modelo_fisico

    def realizar_contagem_ciclica(self, codigo: str) -> Dict:
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

    def gerar_dados_simulacao(self, dias: int = 30):
        resultados = []
        acuracidade_inicial = 78.0
        
        for dia in range(dias + 1):
            if dia <= 10:  
                acuracidade = acuracidade_inicial + (dia * 1.2)
            elif dia <= 20:  
                acuracidade = acuracidade_inicial + 12 + ((dia - 10) * 0.8)
            else:  
                acuracidade = min(96.5, acuracidade_inicial + 20 + ((dia - 20) * 0.3))
            
            acuracidade += random.uniform(-0.8, 0.8)
            acuracidade = max(75, min(98, acuracidade))
            
            fase = 'Implementação' if dia <= 10 else 'Estabilização' if dia <= 20 else 'Otimização'
            
            resultados.append({
                'dia': dia,
                'acuracidade': acuracidade,
                'fase': fase
            })
        
        return pd.DataFrame(resultados)

def criar_grafico_evolucao():
    sistema = SistemaControleEstoque()
    dados = sistema.gerar_dados_simulacao(30)
    
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
    
    fig.add_hline(y=95, line_dash="dash", line_color="red", 
                  annotation_text="Meta: 95%")
    
    fig.add_hline(y=78.3, line_dash="dot", line_color="gray", 
                  annotation_text="Situação Atual: 78.3%")
    
    fig.update_layout(
        title="Evolução da Acuracidade (30 dias)",
        xaxis_title="Dias",
        yaxis_title="Acuracidade (%)",
        height=500,
        showlegend=True
    )
    
    return fig

def criar_grafico_comparativo():
    metricas = ['Acuracidade (%)', 'Tempo Recontagem (h)', 'Perdas (R$ mil)', 'Produtividade (%)']
    antes = [78.3, 120, 45.2, 60]
    depois = [95.8, 30, 8.5, 90]
    
    fig = go.Figure(data=[
        go.Bar(name='Antes', x=metricas, y=antes, marker_color='#ff7f7f'),
        go.Bar(name='Depois', x=metricas, y=depois, marker_color='#7fbf7f')
    ])
    
    fig.update_layout(
        title="Comparativo: Antes vs Depois",
        barmode='group',
        height=500
    )
    
    return fig

def criar_grafico_roi():
    meses = list(range(0, 13))
    investimento_inicial = -50000
    economia_mensal = 36700
    
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
    
    payback_mes = next(i for i, v in enumerate(fluxo_caixa) if v >= 0)
    fig.add_trace(go.Scatter(
        x=[payback_mes],
        y=[fluxo_caixa[payback_mes]],
        mode='markers',
        name=f'Payback: {payback_mes} meses',
        marker=dict(color='gold', size=15, symbol='star')
    ))
    
    fig.update_layout(
        title="Análise de ROI e Payback",
        xaxis_title="Meses",
        yaxis_title="Fluxo de Caixa (R$)",
        height=500
    )
    
    return fig

def criar_grafico_divergencias():
    """Cria gráfico de divergências por categoria baseado nos dados carregados"""
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

def main():
    """Função principal do dashboard"""
    
    st.markdown('<h1 class="main-header">Sistema de Controle de Acuracidade de Estoque</h1>', 
                unsafe_allow_html=True)
    
    sistema = SistemaControleEstoque()
    
    # Seção de Upload de Planilhas
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    st.subheader("📁 Carregamento de Dados")
    
    col1, col2 = st.columns(2)
    
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
    
    # Verificar se os dados foram carregados
    if not st.session_state.estoque_sistema:
        st.warning("⚠️ Por favor, carregue primeiro a planilha do estoque do sistema para continuar.")
        return
    
    if not st.session_state.estoque_fisico:
        st.warning("⚠️ Por favor, carregue a planilha do estoque físico para realizar as contagens.")
        return
    
    # Sidebar com controles
    st.sidebar.header("🔧 Controles do Sistema")
    
    st.sidebar.subheader("Realizar Contagens")
    
    produtos_disponiveis = list(set(st.session_state.estoque_sistema.keys()) & 
                               set(st.session_state.estoque_fisico.keys()))
    
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
    
    # Exibir informações dos dados carregados
    st.sidebar.subheader("📊 Dados Carregados")
    st.sidebar.write(f"Produtos sistema: {len(st.session_state.estoque_sistema)}")
    st.sidebar.write(f"Produtos físico: {len(st.session_state.estoque_fisico)}")
    st.sidebar.write(f"Produtos válidos: {len(produtos_disponiveis)}")
    
    # KPIs Principais
    metricas = sistema.calcular_acuracidade()
    
    if 'erro' not in metricas:
        st.subheader("📈 KPIs Principais")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            acuracidade = metricas['acuracidade_percentual']
            cor = "success" if acuracidade >= 95 else "warning" if acuracidade >= 85 else "danger"
            st.markdown(f'<div class="metric-card {cor}-metric">', unsafe_allow_html=True)
            st.metric("Acuracidade", f"{acuracidade:.1f}%", 
                     delta=f"{acuracidade - 78.3:+.1f}% vs baseline")
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
    
    # Tabs com análises
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Evolução", "Comparativo", "ROI", "Categorias", "Dados"
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
            st.write("• Acuracidade: +17.5 pontos percentuais")
            st.write("• Redução tempo recontagem: -75%")
            st.write("• Redução de perdas: -81%")
            st.write("• Aumento produtividade: +30%")
        
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
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Investimento Total", "R$ 50.000")
        with col2:
            st.metric("Payback", "3 meses")
        with col3:
            st.metric("ROI (12 meses)", "180%")
    
    with tab4:
        st.subheader("Distribuição das Divergências por Categoria")
        fig_divergencias = criar_grafico_divergencias()
        st.plotly_chart(fig_divergencias, use_container_width=True)
        
        if st.session_state.divergencias:
            st.info("Análise baseada nos dados carregados e contagens realizadas.")
        else:
            st.warning("Realize algumas contagens para ver a análise real das divergências.")
    
    with tab5:
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