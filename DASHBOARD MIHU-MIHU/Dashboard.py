import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ------------------ CONFIG DASHBOARD ------------------
st.title("Dashboard Keaktifan Mahasiswa dalam Kegiatan Kampus sebagai Motivasi Kualitas Penyelesaian Tugas Mata Kuliah")
st.set_page_config(
    page_title="Dashboard Keaktifan Mahasiswa dalam Kegiatan Kampus sebagai Motivasi Kualitas Penyelesaian Tugas Mata Kuliah",
    page_icon="📊",
    layout="wide"
)

# ---------- PALETTE PASTEL ----------
PALETTE_PASTEL = [
    "#A8E6CF",  # mint
    "#FFD3B6",  # peach
    "#AEC6CF",  # blue-gray pastel
    "#FFF5BA",  # yellow soft
    "#FFB6B9",  # pink pastel
    "#C7CEEA",  # lavender
]

# ---------- UTIL: INTERPRETATION HELPERS ----------
def pct_str(x, total):
    return f"{(x/total*100):.1f}%"

def interpret_top_category(series, top_n=1):
    """
    Mengembalikan interpretasi singkat untuk series kategori:
    - Nama kategori terbanyak
    - Persentase
    - Kalimat interpretasi singkat
    """
    if series is None or series.empty:
        return None
    counts = series.value_counts(dropna=True)
    total = counts.sum()
    if total == 0:
        return None
    top = counts.iloc[0]
    top_label = counts.index[0]
    return f"💬 Sebagian besar responden berada pada kategori **'{top_label}'** ({top} responden, {pct_str(top, total)}) dari total {total} responden."

def interpret_mean_numeric(series, label=None, dec=2):
    if series is None or series.dropna().empty:
        return None
    mean_val = series.mean()
    label_txt = f" {label}" if label else ""
    return f"💬 Rata-rata{label_txt} adalah **{mean_val:.{dec}f}**."

# ------------------ BACA DATA ------------------
@st.cache_data
def load_data(path="data_bersih6.xlsx"):
    try:
        df = pd.read_excel(path)
    except Exception as e:
        # jika file tidak ada/korup, kembali DF kosong (silent)
        df = pd.DataFrame()
    return df

df = load_data()

# jika df kosong, tampilkan pesan ramah dan stop
if df.empty:
    st.title("📚 Dashboard Interaktif — Data Mahasiswa")
    st.info("Belum ada dataset yang valid. Pastikan file 'data_bersih6.xlsx' ada di folder yang sama.")
    st.stop()

# ------------------ FUNGSI MASKING ------------------
def mask_name(name):
    if pd.isna(name):
        return name
    parts = str(name).split()
    masked_parts = [p[0] + "*" * (len(p) - 1) for p in parts]
    return " ".join(masked_parts)

def mask_npm(npm):
    s = str(npm)
    if len(s) <= 3:
        return "*" * len(s)
    return s[:3] + "*****"

def mask_phone(phone):
    s = str(phone)
    digits = "".join(c for c in s if c.isdigit())
    if len(digits) <= 3:
        return "*" * len(digits)
    return digits[:3] + "*" * (len(digits) - 3)

# ------------------ SAMARKAN DATA (jika kolom ada) ------------------
if "Nama Lengkap" in df.columns:
    df["Nama Lengkap"] = df["Nama Lengkap"].apply(mask_name)

if "NPM" in df.columns:
    df["NPM"] = df["NPM"].apply(mask_npm)

if "Nomor Whatsapp" in df.columns:
    df["Nomor Whatsapp"] = df["Nomor Whatsapp"].apply(mask_phone)
elif "Nomor Telepon" in df.columns:
    df["Nomor Telepon"] = df["Nomor Telepon"].apply(mask_phone)

# ------------------ SIDEBAR FILTER ------------------
st.sidebar.header("🔍 Filter Data")

# Helpful: if column missing, provide empty list / fallback
fakultas_options = sorted(df["Fakultas"].dropna().unique()) if "Fakultas" in df.columns else []
semester_options = sorted(df["Semester"].dropna().unique()) if "Semester" in df.columns else []

fakultas = st.sidebar.multiselect(
    "Fakultas",
    options=fakultas_options,
    default=fakultas_options
)

semester = st.sidebar.multiselect(
    "Semester",
    options=semester_options,
    default=semester_options
)

# IPK slider fallback if IPK exists
if "IPK" in df.columns:
    ipk_min_val = float(df["IPK"].min())
    ipk_max_val = float(df["IPK"].max())
    ipk_min, ipk_max = st.sidebar.slider(
        "Rentang IPK",
        ipk_min_val,
        ipk_max_val,
        (ipk_min_val, ipk_max_val)
    )
else:
    ipk_min, ipk_max = None, None

# ------------------ FILTERKAN DATA (silent jika kolom hilang) ------------------
df_filtered = df.copy()
if fakultas_options:
    df_filtered = df_filtered[df_filtered["Fakultas"].isin(fakultas)]
if semester_options:
    df_filtered = df_filtered[df_filtered["Semester"].isin(semester)]
if ipk_min is not None:
    df_filtered = df_filtered[(df_filtered["IPK"] >= ipk_min) & (df_filtered["IPK"] <= ipk_max)]

# ------------------ TAMPILKAN TABEL ------------------
show_table = st.sidebar.checkbox("Tampilkan tabel data (disamarkan)", value=True)

st.title("📚 Dashboard Interaktif — Data Mahasiswa")
st.markdown("Data ini diambil melalui Kuesioner dengan responden seluruh fakultas UPN Veteran Jawa Timur")

if show_table:
    st.subheader("📄 Tabel Data (Disamarkan)")
    st.dataframe(df_filtered.reset_index(drop=True))

# ------------------ EKSPOR CSV ------------------
st.sidebar.download_button(
    label="💾 Ekspor CSV hasil filter",
    data=df_filtered.to_csv(index=False).encode("utf-8"),
    file_name="data_mahasiswa_filtered.csv",
    mime="text/csv"
)

# ------------------ RINGKASAN METRIK ------------------
st.write("---")
col1, col2, col3 = st.columns(3)

# safe metrics
num_respondents = len(df_filtered)
mean_ipk = round(df_filtered["IPK"].mean(), 2) if "IPK" in df_filtered.columns and not df_filtered["IPK"].dropna().empty else "N/A"
num_fakultas = int(df_filtered["Fakultas"].nunique()) if "Fakultas" in df_filtered.columns else "N/A"

col1.metric("Jumlah Responden", num_respondents)
col2.metric("Rata-rata IPK", mean_ipk)
col3.metric("Jumlah Fakultas", num_fakultas)

# additional metrics row
col4, col5, col6 = st.columns(3)
ipk_max = round(df_filtered["IPK"].max(), 2) if "IPK" in df_filtered.columns and not df_filtered["IPK"].dropna().empty else "N/A"
ipk_min = round(df_filtered["IPK"].min(), 2) if "IPK" in df_filtered.columns and not df_filtered["IPK"].dropna().empty else "N/A"
aktif_count = df_filtered[df_filtered.get("Mengikuti kegiatan", pd.Series()).fillna("").str.lower() == "ya"].shape[0] if "Mengikuti kegiatan" in df_filtered.columns else "N/A"

col4.metric("IPK Tertinggi", ipk_max)
col5.metric("IPK Terendah", ipk_min)
col6.metric("Mahasiswa Aktif mengikuti Kegiatan", aktif_count)

# ------------------ GRAFIK: Jumlah Mahasiswa per Semester ------------------
if "Semester" in df_filtered.columns:
    st.subheader("🎓 Jumlah Mahasiswa per Semester")
    semester_count = df_filtered["Semester"].value_counts().reset_index()
    semester_count.columns = ["Semester", "Jumlah Mahasiswa"]
    fig_sem = px.bar(
        semester_count.sort_values("Semester"),
        x="Semester",
        y="Jumlah Mahasiswa",
        color="Jumlah Mahasiswa",
        color_continuous_scale=[PALETTE_PASTEL[0], PALETTE_PASTEL[1]],
        labels={"Jumlah Mahasiswa":"Jumlah"}
    )
    st.plotly_chart(fig_sem, use_container_width=True)

    interp = interpret_top_category(df_filtered["Semester"])
    if interp:
        st.markdown(interp)

# ------------------ GRAFIK: Proporsi Keikutsertaan Kegiatan ------------------
if "Mengikuti kegiatan" in df_filtered.columns:
    st.subheader("💬 Proporsi Keikutsertaan Mahasiswa dalam Kegiatan")
    aktif_count = df_filtered["Mengikuti kegiatan"].value_counts().reset_index()
    aktif_count.columns = ["Status", "Jumlah"]
    fig_aktif = px.pie(
        aktif_count,
        values="Jumlah",
        names="Status",
        hole=0.4,
        color_discrete_sequence=PALETTE_PASTEL
    )
    st.plotly_chart(fig_aktif, use_container_width=True)

    interp = interpret_top_category(df_filtered["Mengikuti kegiatan"])
    if interp:
        st.markdown(interp)

# ------------------ GRAFIK: Distribusi IPK Mahasiswa yang Mengikuti Kegiatan (Violin) ------------------
if {"Mengikuti kegiatan", "IPK"}.issubset(df_filtered.columns):
    st.subheader("🎓 Distribusi IPK Mahasiswa yang Mengikuti Kegiatan")
    df_ikut = df_filtered[df_filtered["Mengikuti kegiatan"].str.lower().str.strip() == "ya"]
    if not df_ikut.empty:
        fig_violin = px.violin(
            df_ikut,
            y="IPK",
            box=True,
            points="all",
            color_discrete_sequence=[PALETTE_PASTEL[0]]
        )
        fig_violin.update_layout(title="Distribusi IPK Mahasiswa yang Mengikuti Kegiatan", showlegend=False)
        st.plotly_chart(fig_violin, use_container_width=True)

        mean_ipk_ikut = interpret_mean_numeric(df_ikut["IPK"], label="IPK mahasiswa yang mengikuti kegiatan")
        if mean_ipk_ikut:
            st.markdown(mean_ipk_ikut)

# ------------------ GRAFIK: Statistik Keaktifan Mahasiswa (kategori khusus) ------------------
if "Jumlah Mengikuti Kegiatan_category" in df_filtered.columns:
    st.subheader("📊 Statistik Keaktifan Mahasiswa dalam Kegiatan")
    count_kegiatan = df_filtered["Jumlah Mengikuti Kegiatan_category"].value_counts().reset_index()
    count_kegiatan.columns = ["Kategori Keaktifan", "Jumlah"]
    total = count_kegiatan["Jumlah"].sum()
    cols = st.columns(len(count_kegiatan))
    for col, row in zip(cols, count_kegiatan.itertuples(index=False)):
        col.metric(
            label=f"{row[0]}",
            value=f"{row[1]} Mahasiswa",
            delta=f"{(row[1]/total*100):.1f}% dari total"
        )
    # Interpretation
    interp = interpret_top_category(df_filtered["Jumlah Mengikuti Kegiatan_category"])
    if interp:
        st.markdown(interp)

# ------------------ GRAFIK: Kegiatan vs Gangguan Tugas (pie) ------------------
col_name_ganggu = "Apakah kegiatan menganggu aktivitas mengerjakan tugas mata kuliah"
if col_name_ganggu in df_filtered.columns:
    st.subheader("⚖️ Apakah Kegiatan Menganggu Aktivitas Mengerjakan Tugas Mata Kuliah")
    ganggu_count = df_filtered[col_name_ganggu].value_counts().reset_index()
    ganggu_count.columns = ["Respon", "Jumlah"]
    ganggu_count["Persentase"] = (ganggu_count["Jumlah"] / ganggu_count["Jumlah"].sum()) * 100

    fig_ganggu = px.pie(
        ganggu_count,
        values="Persentase",
        names="Respon",
        hole=0.4,
        color_discrete_sequence=PALETTE_PASTEL
    )
    fig_ganggu.update_traces(textposition="inside", textinfo="percent+label", insidetextorientation="radial")
    st.plotly_chart(fig_ganggu, use_container_width=True)

    interp = interpret_top_category(df_filtered[col_name_ganggu])
    if interp:
        st.markdown(interp)

# ------------------ GRAFIK: Ketepatan Mengerjakan Tugas (Hanya yg ikut) ------------------
col_tugas_cat = "Mengerjakan tugas kuliah sebelum deadline_category"
if {"Mengikuti kegiatan", col_tugas_cat}.issubset(df_filtered.columns):
    st.subheader("⏰ Ketepatan Mengerjakan Tugas (Hanya Mahasiswa yang Mengikuti Kegiatan)")
    df_ikut = df_filtered[df_filtered["Mengikuti kegiatan"].str.lower().str.strip() == "ya"]
    if not df_ikut.empty:
        distribusi_tugas = (
            df_ikut[col_tugas_cat]
            .value_counts(normalize=True)
            .mul(100)
            .reset_index()
        )
        distribusi_tugas.columns = ["Kategori Ketepatan Mengerjakan Tugas", "Persentase"]

        fig_tugas_ikut = px.bar(
            distribusi_tugas,
            x="Kategori Ketepatan Mengerjakan Tugas",
            y="Persentase",
            text=distribusi_tugas["Persentase"].apply(lambda x: f"{x:.1f}%"),
            color="Kategori Ketepatan Mengerjakan Tugas",
            color_discrete_sequence=PALETTE_PASTEL
        )
        fig_tugas_ikut.update_traces(textposition="outside")
        fig_tugas_ikut.update_layout(yaxis_title="Persentase (%)", showlegend=False)
        st.plotly_chart(fig_tugas_ikut, use_container_width=True)

        # interpretasi: kategori terbanyak
        if not distribusi_tugas.empty:
            top = distribusi_tugas.sort_values("Persentase", ascending=False).iloc[0]
            st.markdown(f"📊 Sebagian besar mahasiswa yang mengikuti kegiatan mengerjakan tugas secara **'{top['Kategori Ketepatan Mengerjakan Tugas']}'** (~{top['Persentase']:.1f}%)")

# ------------------ GRAFIK: Pengaruh Kegiatan pada Motivasi (Hanya yg ikut) ------------------
col_pengaruh = "Pengaruh kegiatan dalam meningkatkan motivasi mengerjakan tugas mata kuliah"
if {"Mengikuti kegiatan", col_pengaruh}.issubset(df_filtered.columns):
    st.subheader("💡 Pengaruh Kegiatan dalam Meningkatkan Motivasi Mengerjakan Tugas")
    df_ikut = df_filtered[df_filtered["Mengikuti kegiatan"].str.lower().str.strip() == "ya"]
    if not df_ikut.empty:
        pengaruh_count = df_ikut[col_pengaruh].value_counts(normalize=True).mul(100).reset_index()
        pengaruh_count.columns = ["Kategori Pengaruh", "Persentase"]

        fig_pengaruh = px.bar(
            pengaruh_count,
            x="Persentase",
            y="Kategori Pengaruh",
            orientation="h",
            text=pengaruh_count["Persentase"].apply(lambda x: f"{x:.1f}%"),
            color="Kategori Pengaruh",
            color_discrete_sequence=PALETTE_PASTEL
        )
        fig_pengaruh.update_traces(textposition="outside")
        fig_pengaruh.update_layout(xaxis_title="Persentase (%)", showlegend=False)
        st.plotly_chart(fig_pengaruh, use_container_width=True)

        if not pengaruh_count.empty:
            top = pengaruh_count.sort_values("Persentase", ascending=False).iloc[0]
            st.markdown(f"💬 Sebagian besar mahasiswa yang mengikuti kegiatan merasa **'{top['Kategori Pengaruh']}'** (≈{top['Persentase']:.1f}%).")

# ------------------ GRAFIK: Rata-rata Waktu Mengerjakan Tugas Berdasarkan Keikutsertaan ------------------
col_waktu = "Rata-rata waktu mengerjakan tugas"
if {"Mengikuti kegiatan", col_waktu}.issubset(df_filtered.columns):
    st.subheader("⏱️ Rata-rata Waktu Mengerjakan Tugas Berdasarkan Keikutsertaan Kegiatan")

    df_avg = df_filtered.groupby("Mengikuti kegiatan")[col_waktu].mean().reset_index()
    df_avg.columns = ["Mengikuti kegiatan", col_waktu]

    # Donut chart dengan tampilan jam (tanpa persen)
    fig_avg_donut = px.pie(
        df_avg,
        values=col_waktu,
        names="Mengikuti kegiatan",
        hole=0.4,
        color_discrete_sequence=PALETTE_PASTEL
    )

    # Menampilkan jam langsung sebagai label
    fig_avg_donut.update_traces(
        textposition="inside",
        textinfo="label+text",  # hanya label + jam
        text=df_avg[col_waktu].apply(lambda x: f"{x:.2f} jam")
    )

    fig_avg_donut.update_layout(
        title="Rata-rata Waktu Mengerjakan Tugas (Donut Chart)",
        showlegend=True
    )

    st.plotly_chart(fig_avg_donut, use_container_width=True)

    if not df_avg.empty:
        highest = df_avg.loc[df_avg[col_waktu].idxmax()]
        lowest = df_avg.loc[df_avg[col_waktu].idxmin()]
        st.markdown(
            f"💬 Mahasiswa yang **{highest['Mengikuti kegiatan']}** memiliki rata-rata waktu mengerjakan tugas lebih tinggi "
            f"(**{highest[col_waktu]:.2f} jam**) dibandingkan yang **{lowest['Mengikuti kegiatan']}** "
            f"(**{lowest[col_waktu]:.2f} jam**)."
        )

# ------------------ GRAFIK: Distribusi Menunda Tugas (Responden yang Mengikuti Kegiatan) ------------------
col_menunda = "Jumlah menunda mengerjakan tugas mata kuliah_category"
if {"Mengikuti kegiatan", col_menunda}.issubset(df.columns):
    df_ya = df[df["Mengikuti kegiatan"].str.lower().str.strip() == "ya"]
    if not df_ya.empty:
        st.subheader("⏳ Distribusi Kategori Menunda Tugas (Responden yang Mengikuti Kegiatan)")
        distribusi_tunda = df_ya[col_menunda].value_counts(normalize=True).mul(100).reset_index()
        distribusi_tunda.columns = ["Kategori", "Persentase"]

        fig_bar = px.bar(
            distribusi_tunda,
            x="Kategori",
            y="Persentase",
            text=distribusi_tunda["Persentase"].apply(lambda x: f"{x:.1f}%"),
            color="Kategori",
            color_discrete_sequence=PALETTE_PASTEL
        )
        fig_bar.update_traces(textposition="outside")
        fig_bar.update_layout(yaxis_title="Persentase (%)", showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

        top = distribusi_tunda.sort_values("Persentase", ascending=False).iloc[0]
        st.markdown(f"💬 Dari responden yang mengikuti kegiatan, kategori **'{top['Kategori']}'** memiliki proporsi tertinggi (~{top['Persentase']:.1f}%).")

# ------------------ GRAFIK: Tingkat Kesungguhan Mengerjakan Tugas (Responden yang Mengikuti Kegiatan) ------------------
col_sungguh = "Mengerjakan tugas mata kuliah dengan sungguh-sungguh"
if {"Mengikuti kegiatan", col_sungguh}.issubset(df.columns):
    df_ya = df[df["Mengikuti kegiatan"].str.lower().str.strip() == "ya"]
    if not df_ya.empty:
        st.subheader("📝 Tingkat Kesungguhan Mengerjakan Tugas (Responden yang Mengikuti Kegiatan)")
        distribusi_sungguh = df_ya[col_sungguh].value_counts(normalize=True).mul(100).reset_index()
        distribusi_sungguh.columns = ["Kategori", "Persentase"]

        fig_bar = px.bar(
            distribusi_sungguh,
            x="Kategori",
            y="Persentase",
            text=distribusi_sungguh["Persentase"].apply(lambda x: f"{x:.1f}%"),
            color="Kategori",
            color_discrete_sequence=PALETTE_PASTEL
        )
        fig_bar.update_traces(textposition="outside")
        fig_bar.update_layout(yaxis_title="Persentase (%)", showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

        top = distribusi_sungguh.sort_values("Persentase", ascending=False).iloc[0]
        st.markdown(f"💬 Dari responden yang mengikuti kegiatan, sebagian besar berada pada kategori **'{top['Kategori']}'** (~{top['Persentase']:.1f}%).")

# ------------------ GRAFIK: Dampak Mengikuti Kegiatan pada Kemampuan di Bawah Tekanan ------------------
col_dampak = "Dampak mengikuti kegiatan dalam kemampuan mengerjakan tugas mata kuliah  di bawah tekanan"
if {"Mengikuti kegiatan", col_dampak}.issubset(df.columns):
    df_ikut = df[df["Mengikuti kegiatan"].str.lower().str.strip() == "ya"]
    if not df_ikut.empty:
        st.subheader("💪 Dampak Mengikuti Kegiatan terhadap Kemampuan di Bawah Tekanan (Responden 'Ya')")
        distribusi_dampak = df_ikut[col_dampak].value_counts(normalize=True).mul(100).reset_index()
        distribusi_dampak.columns = ["Kategori Dampak", "Persentase"]

        fig_dampak = px.bar(
            distribusi_dampak,
            x="Persentase",
            y="Kategori Dampak",
            orientation="h",
            text=distribusi_dampak["Persentase"].apply(lambda x: f"{x:.1f}%"),
            color="Kategori Dampak",
            color_discrete_sequence=PALETTE_PASTEL
        )
        fig_dampak.update_traces(textposition="outside")
        fig_dampak.update_layout(xaxis_title="Persentase (%)", showlegend=False)
        st.plotly_chart(fig_dampak, use_container_width=True)

        top = distribusi_dampak.sort_values("Persentase", ascending=False).iloc[0]
        st.markdown(f"💬 Sebagian besar mahasiswa yang mengikuti kegiatan merasa **'{top['Kategori Dampak']}'** (≈{top['Persentase']:.1f}%).")
