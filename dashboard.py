import streamlit as st
import pandas as pd
import pymysql
import matplotlib.pyplot as plt

# 设置中文字体 (解决 Mac 上中文显示方块的问题)
plt.rcParams['font.sans-serif'] = ['PingFang SC', 'Arial Unicode MS'] 
plt.rcParams['axes.unicode_minus'] = False

st.set_page_config(page_title="销售数据看板", page_icon="📊")
st.title("📊 实时销售数据分析看板")

# 数据库配置
@st.cache_data(ttl=60)
def load_data():
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='123456',  # <--- 记得改成你的密码
            database='sales_db',
            charset='utf8mb4'
        )
        df = pd.read_sql("SELECT * FROM sales_data", con=conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"数据库连接失败: {e}")
        return pd.DataFrame()

df = load_data()
# 获取所有不重复的产品名称
all_products = df['product_name'].unique().tolist()
# 在最前面加一个“全部”选项
all_products.insert(0, "全部") 

if not df.empty:
    # 关键指标
    col1, col2, col3 = st.columns(3)
    # --- 筛选器开始 ---
# 1. 获取所有产品名称，并加上“全部”选项
all_products = ["全部"] + df['product_name'].unique().tolist()

# 2. 在侧边栏创建下拉菜单
selected_product = st.sidebar.selectbox("🔍 请选择产品类别", all_products)
# --- 复制下面这段代码 ---

# 1. 先处理时间筛选 (新增部分)
# 确保你的数据里有一列叫 'sale_date'，如果是字符串需要先转成时间格式
df['sale_date'] = pd.to_datetime(df['sale_date']) 

start_date = st.sidebar.date_input("📅 开始日期", df['sale_date'].min())
end_date = st.sidebar.date_input("📅 结束日期", df['sale_date'].max())

# 2. 再处理产品筛选
all_products = ["全部"] + df['product_name'].unique().tolist()
selected_product = st.sidebar.selectbox("🔍 请选择产品类别", all_products, key="product_selector")

# 3. 执行筛选逻辑 (注意这里的顺序：先筛时间，再筛产品)
filtered_df = df.copy() # 先复制一份总表

# A. 应用时间筛选
# --- 复制这段代码替换原来的日期筛选部分 ---

# 1. 强制将数据库的日期列转换为标准时间格式 (这一步最关键！)
# 注意：如果你的列名不叫 'sale_date'，请改成真实的列名
df['sale_date'] = pd.to_datetime(df['sale_date'], errors='coerce')

# 2. 执行筛选
# start_date 和 end_date 是 sidebar 选出来的日期对象
mask_time = (df['sale_date'] >= pd.to_datetime(start_date)) & \
            (df['sale_date'] <= pd.to_datetime(end_date) + pd.Timedelta(days=1)) 
            # 加一天是为了包含结束日期当天的所有数据

filtered_df = df[mask_time].copy()

# --- 替换结束 ---
filtered_df = filtered_df[mask_time]

# B. 应用产品筛选
if selected_product != "全部":
    filtered_df = filtered_df[filtered_df['product_name'] == selected_product]

# --- 替换结束 ---
    if selected_product == "全部":
        filtered_df = df
    else:
        filtered_df = df[df['product_name'] == selected_product]
    
    # 4. 展示指标 (使用 filtered_df)
    col1.metric("总销售额", f"¥{filtered_df['price'].sum():,.2f}")
    col2.metric("总销量", f"{filtered_df['quantity'].sum()} 件")
    col3.metric("平均单价", f"¥{filtered_df['price'].mean():.2f}")
    # --- 复制这段代码替换原来的画图和警告部分 ---

# 1. 先处理数据（确保列名正确）
filtered_df['sale_date'] = pd.to_datetime(filtered_df['sale_date'])
filtered_df['月份'] = filtered_df['sale_date'].dt.to_period('M').astype(str)

# 2. 聚合数据
monthly_sales = filtered_df.groupby('月份')['price'].sum().reset_index()
monthly_sales.columns = ['月份', '总销售额']

# 3. 统一的判断逻辑
if not monthly_sales.empty:
    # 如果有数据，就画图
    st.subheader("📈 月度销售趋势")
    st.line_chart(monthly_sales.set_index('月份'))
else:
    # 如果没数据，才显示警告
    st.warning("⚠️ 当前筛选条件下暂无销售数据。")

# 4. 显示表格（始终显示，或者你也可以加个判断）
st.subheader("📋 详细数据明细")
st.dataframe(filtered_df)

# --- 替换结束 ---
# -----------------------------
# --- 导出功能代码 ---
st.subheader("📥 数据导出")
csv = filtered_df.to_csv(index=False).encode('utf-8-sig') # 转换格式，防止中文乱码
st.download_button(
    label="下载当前筛选数据 (CSV)",
    data=csv,
    file_name=f'销售数据_{pd.Timestamp.now().strftime("%Y%m%d")}.csv',
    mime='text/csv',
)
# -------------------