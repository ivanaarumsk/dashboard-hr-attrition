import pandas as pd
import plotly.express as px
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Dashboard HR Attrition", page_icon="📊", layout="wide")


@st.cache_data
def load_data():
    path = Path(__file__).parent / "Data_Clean.xlsx"
    if not path.exists():
        st.error(f"File data tidak ditemukan. Taruh Data_Clean.xlsx di folder ini: {path.parent}")
        st.stop()
    return pd.read_excel(path, sheet_name="Data Clean")
df = load_data()

# ----------------Judul----------------
st.title("📊 Dashboard Analisis Attrition Karyawan")
st.write(
    "Dashboard ini menampilkan analisis tingkat resign (attrition) karyawan berdasarkan "
    "dataset **IBM HR Analytics Employee Attrition** dari Kaggle (1.470 karyawan). "
    "Filter di sidebar digunakan untuk melihat data berdasarkan departemen, gender, dan kelompok usia."
)

# ----------------Filter interaktif----------------
st.sidebar.header("Filter Data")
dept = st.sidebar.multiselect(
    "Department", sorted(df["Department"].unique()), default=sorted(df["Department"].unique())
)
gender = st.sidebar.multiselect(
    "Gender", sorted(df["Gender"].unique()), default=sorted(df["Gender"].unique())
)
age_order = ["18-25", "26-35", "36-45", "46-55", "56-60"]
age_group = st.sidebar.multiselect("Kelompok Usia", age_order, default=age_order)

data = df[
    df["Department"].isin(dept) & df["Gender"].isin(gender) & df["Age_Group"].isin(age_group)
]

if data.empty:
    st.warning("Tidak ada data yang sesuai dengan filter. Silakan ubah pilihan filter.")
    st.stop()

# ---------------- KPI ----------------
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Karyawan", f"{len(data):,}")
k2.metric("Karyawan Resign", f"{int(data['Resign'].sum()):,}")
k3.metric("Attrition Rate", f"{data['Resign'].mean() * 100:.1f}%")
k4.metric("Rata-rata Gaji Bulanan", f"${data['MonthlyIncome'].mean():,.0f}")

st.divider()

# --------------- Visualisasi ----------------
col1, col2 = st.columns(2)

# Bar chart
with col1:
    st.subheader("Attrition Rate per Job Role")
    role = data.groupby("JobRole")["Resign"].mean().mul(100).reset_index()
    role = role.sort_values("Resign")
    fig = px.bar(role, x="Resign", y="JobRole", orientation="h",
                 labels={"Resign": "Attrition Rate (%)", "JobRole": "Job Role"})
    st.plotly_chart(fig, width="stretch")

# Pie chart
with col2:
    st.subheader("Proporsi Karyawan Resign vs Bertahan")
    pie = data["Attrition"].map({"Yes": "Resign", "No": "Bertahan"}).value_counts().reset_index()
    pie.columns = ["Status", "Jumlah"]
    fig = px.pie(pie, names="Status", values="Jumlah", hole=0.4)
    st.plotly_chart(fig, width="stretch")

col3, col4 = st.columns(2)

# Line chart
with col3:
    st.subheader("Attrition Rate berdasarkan Lama Bekerja di Perusahaan")
    line = data.groupby("YearsAtCompany")["Resign"].mean().mul(100).reset_index()
    fig = px.line(line, x="YearsAtCompany", y="Resign", markers=True,
                  labels={"YearsAtCompany": "Tahun di Perusahaan", "Resign": "Attrition Rate (%)"})
    st.plotly_chart(fig, width="stretch")

# Histogram
with col4:
    st.subheader("Distribusi Gaji Bulanan")
    fig = px.histogram(data, x="MonthlyIncome", color="Attrition", nbins=30, barmode="overlay",
                       opacity=0.7, color_discrete_map={"Yes": "#d62728", "No": "#1f77b4"},
                       labels={"MonthlyIncome": "Gaji Bulanan"})
    st.plotly_chart(fig, width="stretch")

# Heatmap
st.subheader("Heatmap Attrition Rate: Kepuasan Kerja vs Work-Life Balance")
level = {1: "1 - Low", 2: "2 - Medium", 3: "3 - High", 4: "4 - Very High"}
heat = data.pivot_table(index="WorkLifeBalance", columns="JobSatisfaction",
                        values="Resign", aggfunc="mean") * 100
heat = heat.rename(index=level, columns=level)
fig = px.imshow(heat, text_auto=".1f", color_continuous_scale="Reds", aspect="auto",
                labels={"x": "Job Satisfaction", "y": "Work-Life Balance", "color": "Attrition (%)"})
st.plotly_chart(fig, width="stretch")
st.caption("Semakin merah, semakin tinggi persentase karyawan yang resign pada kombinasi tersebut.")

# ---------------- Insight singkat ----------------
st.subheader("💡 Insight Singkat")
top_role = role.iloc[-1]
ot = data.groupby("OverTime")["Resign"].mean() * 100
insight = f"- Job role dengan attrition rate tertinggi: **{top_role['JobRole']}** ({top_role['Resign']:.1f}%)."
if {"Yes", "No"} <= set(ot.index):
    insight += (f"\n- Karyawan yang lembur punya attrition rate **{ot['Yes']:.1f}%**, "
                f"sedangkan yang tidak lembur **{ot['No']:.1f}%**.")
st.markdown(insight)

with st.expander("Lihat data"):
    st.dataframe(data, width="stretch")
