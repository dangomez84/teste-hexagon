import streamlit as st
import pandas as pd
import pyodbc
import plotly.express as px
import config
import datetime

# ---------- Conexão ----------
def get_connection():
    return pyodbc.connect(
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={config.SERVER};"
        f"DATABASE={config.DATABASE};"
        f"UID={config.USERNAME};"
        f"PWD={config.PASSWORD};"
        "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    )

# ---------- Carregar dados ----------
@st.cache_data
def load_data():
    query = """
    SELECT 
        soh.SalesOrderID,
        soh.OrderDate,
        soh.TotalDue,
        sp.Name AS Region,
        p.Name AS ProductName
    FROM Sales.SalesOrderHeader AS soh
    JOIN Sales.SalesOrderDetail AS sod
        ON soh.SalesOrderID = sod.SalesOrderID
    JOIN Production.Product AS p
        ON sod.ProductID = p.ProductID
    JOIN Person.Address AS a
        ON soh.ShipToAddressID = a.AddressID
    JOIN Person.StateProvince AS sp
        ON a.StateProvinceID = sp.StateProvinceID
    """
    conn = get_connection()
    df = pd.read_sql(query, conn)
    conn.close()
    df['OrderDate'] = pd.to_datetime(df['OrderDate'])
    return df

# ---------- App ----------
st.set_page_config(page_title="Painel de Vendas", layout="wide")
st.title("Teste Hexagon - Daniel Gomes")

df = load_data()

# Converter para datetime.date
min_date = df['OrderDate'].min().date()
max_date = df['OrderDate'].max().date()

# ----- Filtros -----
col1, col2, col3, col4 = st.columns([1,1,1,0.5])
# col1, col2, col3 = st.columns(3)

with col1:
    regions = st.multiselect("Selecione as Regiões", df['Region'].unique())

with col2:
    products = st.multiselect("Selecione os Produtos", df['ProductName'].unique())

with col3:
    date_range = st.date_input(
        "Período",
        # [df['OrderDate'].min(), df['OrderDate'].max()]
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )
    

# ----- Aplicar filtros -----
filtered_df = df.copy()

if regions:
    filtered_df = filtered_df[filtered_df['Region'].isin(regions)]
if products:
    filtered_df = filtered_df[filtered_df['ProductName'].isin(products)]
if date_range:
    filtered_df = filtered_df[
        (filtered_df['OrderDate'] >= pd.to_datetime(date_range[0])) &
        (filtered_df['OrderDate'] <= pd.to_datetime(date_range[1]))
    ]


# # KPI
# total_sales = filtered_df['TotalDue'].sum()
# st.metric("Total de Vendas no Período", f"${total_sales:,.2f}")

# ---------- KPIs ----------
col_kpi1, col_kpi2, col_kpi3 = st.columns(3)

# KPI 1: Total geral
total_sales = filtered_df['TotalDue'].sum()
col_kpi1.metric("Total de Vendas no Período", f"${total_sales:,.2f}")

# KPI 2: Vendas por região (somando todas as regiões filtradas)
sales_by_region = filtered_df.groupby('Region')['TotalDue'].sum().reset_index()
top_region = sales_by_region.loc[sales_by_region['TotalDue'].idxmax()]
col_kpi2.metric(f"Maior Região ({top_region['Region']})", f"${top_region['TotalDue']:,.2f}")

# KPI 3: Vendas por produto (somando todos os produtos filtrados)
sales_by_product = filtered_df.groupby('ProductName')['TotalDue'].sum().reset_index()
top_product = sales_by_product.loc[sales_by_product['TotalDue'].idxmax()]
col_kpi3.metric(f"Produto Mais Vendido ({top_product['ProductName']})", f"${top_product['TotalDue']:,.2f}")


# Vendas por produto
sales_by_product = filtered_df.groupby('ProductName')['TotalDue'].sum().reset_index()
fig_product = px.bar(
    sales_by_product,
    height=500,
    y='ProductName',
    x='TotalDue',
    title="Vendas por Produto",
    labels={'TotalDue': 'Total de Vendas', 'ProductName': 'Produto'}
)



# Vendas ao longo do tempo
sales_by_time = filtered_df.groupby(filtered_df['OrderDate'].dt.to_period('M'))['TotalDue'].sum().reset_index()
sales_by_time['OrderDate'] = sales_by_time['OrderDate'].astype(str)
fig_time = px.line(
    sales_by_time,
    x='OrderDate',
    y='TotalDue',
    title="Vendas ao Longo do Tempo",
    labels={'TotalDue': 'Total de Vendas', 'OrderDate': 'Ano-Mês'}
)

# Mostrar gráficos
st.plotly_chart(fig_product, use_container_width=True)
st.plotly_chart(fig_time, use_container_width=True)


