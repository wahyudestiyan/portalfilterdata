import streamlit as st
import requests
import pandas as pd
import io

# URL API utama
url_main = "https://satudata.jatengprov.go.id/v1/data"
headers = {
    "Authorization": "Bearer p0ekF-G7SFbmqgYz7__HZ-z4mnvs-wrD"
}

# Fungsi untuk mengambil data judul dengan caching
@st.cache_data
def get_data_judul():
    try:
        response = requests.get(url_main, headers=headers)
        response.raise_for_status()  # Memastikan respons sukses
        return response.json().get('data', [])
    except requests.exceptions.RequestException as e:
        st.error(f"Terjadi kesalahan saat mengambil data judul: {e}")
        return []

# Fungsi untuk mengambil data detail berdasarkan ID dengan caching
@st.cache_data
def get_data_detail(id_data):
    url_detail = f"https://satudata.jatengprov.go.id/v1/data/{id_data}"
    try:
        detail_response = requests.get(url_detail, headers=headers)
        detail_response.raise_for_status()  # Memastikan respons sukses
        detail_data = detail_response.json()
        
        # Pastikan kunci 'data' ada dalam respons
        if 'data' in detail_data:
            return detail_data['data']
        else:
            st.warning(f"Warning: Tidak ada data ditemukan untuk ID: {id_data}")
            return []
    except requests.exceptions.RequestException as e:
        st.error(f"Terjadi kesalahan saat mengambil detail data ID {id_data}: {e}")
        return []

# Tampilan utama
st.title('Alat Bantu Filter Tahun Data Portal Data')

# Form untuk memilih rentang tahun
tahun_mulai = st.selectbox('Pilih Tahun Mulai', [i for i in range(2019, 2025)])
tahun_akhir = st.selectbox('Pilih Tahun Akhir', [i for i in range(tahun_mulai, 2025)])

# Tampilkan spinner saat memproses data
with st.spinner("Sedang memuat data..."):
    # Ambil data judul
    data_judul = get_data_judul()

    # Menyimpan judul yang terisi untuk rentang tahun yang dipilih
    judul_terisi_data = []

    # Iterasi setiap judul data dan periksa tahun yang terisi
    for entry in data_judul:
        id_data = entry['id']
        judul_data = entry['judul']
        
        # Ambil data detail untuk setiap judul
        detail_data = get_data_detail(id_data)

        # Menyimpan tahun yang terisi
        tahun_terisi = []

        # Filter berdasarkan rentang tahun yang dipilih
        for item in detail_data:
            tahun_data = item.get('tahun_data', None)
            
            # Pastikan tahun_data bukan None dan berada dalam rentang yang dipilih
            if tahun_data is not None and tahun_mulai <= tahun_data <= tahun_akhir:
                tahun_terisi.append(tahun_data)

        # Jika ada tahun yang terisi dalam rentang yang dipilih
        if tahun_terisi:
            # Menyusun rentang tahun yang sesuai (misal, 2019-2021)
            tahun_range = f"{min(tahun_terisi)}-{max(tahun_terisi)}" if len(tahun_terisi) > 1 else str(tahun_terisi[0])
            judul_terisi_data.append({
                'Judul Data': judul_data,
                'Tahun Data': tahun_range
            })

# Hitung jumlah total judul data yang diambil dari API
total_judul_data = len(data_judul)

# Hitung jumlah judul data yang sudah terisi datanya
jumlah_terisi = len(judul_terisi_data)

# Tampilan jumlah data dengan Markdown
st.markdown(f"""
<div style="text-align: center; margin-bottom: 20px;">
    <h2 style="color: #2c3e50;">Jumlah seluruh judul data yang diambil dari API: <span style="color: #2980b9;">{total_judul_data}</span></h2>
    <h2 style="color: #2c3e50;">Jumlah judul data yang sudah terisi datanya: <span style="color: #27ae60;">{jumlah_terisi}</span></h2>
</div>
""", unsafe_allow_html=True)

# Menampilkan hasil dalam tabel
if judul_terisi_data:
    st.subheader(f"Judul Data untuk Tahun {tahun_mulai} - {tahun_akhir}:")
    df = pd.DataFrame(judul_terisi_data)  # Mengubah list ke DataFrame
    st.dataframe(df)  # Menampilkan tabel dengan Streamlit

    # Menambahkan tombol untuk mengunduh file Excel
    @st.cache_data
    def to_excel(df):
        # Menyimpan DataFrame sebagai file Excel dalam format bytes
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Data")
        return output.getvalue()

    # Tombol unduh Excel
    excel_data = to_excel(df)
    st.download_button(
        label="Unduh Tabel sebagai Excel",
        data=excel_data,
        file_name="judul_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.write(f"Tidak ada data yang terisi untuk rentang tahun {tahun_mulai} - {tahun_akhir}.")
