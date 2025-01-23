import streamlit as st
import requests
import pandas as pd
import io

# URL API utama
url_main = "https://satudata.jatengprov.go.id/v1/data"
headers = {
    "Authorization": "Bearer p0ekF-G7SFbmqgYz7__HZ-z4mnvs-wrD"
}

# Fungsi untuk mengambil data judul dengan pagination dan caching
@st.cache_resource
def get_data_judul():
    all_data = []
    current_page = 1
    total_pages = 1  # Inisialisasi awal

    try:
        while current_page <= total_pages:
            # Tambahkan parameter halaman pada URL
            response = requests.get(f"{url_main}?page={current_page}", headers=headers)
            response.raise_for_status()  # Memastikan respons sukses
            
            # Parse data JSON
            json_response = response.json()
            data = json_response.get('data', [])
            _meta = json_response.get('_meta', {})
            
            # Tambahkan data dari halaman saat ini ke dalam list
            all_data.extend(data)
            
            # Update informasi pagination
            total_pages = _meta.get('pageCount', 1)
            current_page += 1

        return all_data
    except requests.exceptions.RequestException:
        # Cegah menampilkan error ke Streamlit
        return []

# Fungsi untuk mengambil data detail berdasarkan ID dengan caching
@st.cache_resource
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
            # Mengembalikan data kosong jika tidak ada data tanpa mencetak error
            return []
    except requests.exceptions.RequestException:
        # Jangan tampilkan pesan error di Streamlit
        return []

# Tampilan utama
st.title('Alat Bantu Filter Tahun Data Portal Data')

# Form untuk memilih rentang tahun
tahun_mulai = st.selectbox('Pilih Tahun Mulai', [i for i in range(2019, 2025)])
tahun_akhir = st.selectbox('Pilih Tahun Akhir', [i for i in range(tahun_mulai, 2025)])

with st.spinner("Sedang memuat data..."):
    # Ambil data judul
    data_judul = get_data_judul()

    # Menyimpan judul yang terisi untuk rentang tahun yang dipilih
    judul_terisi_data = []

    # Daftar tahun yang harus ada dalam rentang yang dipilih
    tahun_range_diharapkan = set(range(tahun_mulai, tahun_akhir + 1))

    # Iterasi setiap judul data dan periksa tahun yang terisi
    for entry in data_judul:
        id_data = entry['id']
        judul_data = entry['judul']
        
        # Ambil data detail untuk setiap judul
        detail_data = get_data_detail(id_data)

        # Menyimpan tahun yang terisi
        tahun_terisi = set()

        # Filter berdasarkan rentang tahun yang dipilih
        for item in detail_data:
            tahun_data = item.get('tahun_data', None)
            
            # Pastikan tahun_data adalah integer dan berada dalam rentang yang dipilih
            if tahun_data is not None:
                try:
                    tahun_data = int(tahun_data)  # Mengonversi ke integer jika perlu
                    if tahun_mulai <= tahun_data <= tahun_akhir:
                        tahun_terisi.add(tahun_data)
                except ValueError:
                    st.warning(f"Tahun data tidak valid: {tahun_data} untuk ID: {id_data}")

        # Cek jika seluruh tahun yang diperlukan ada dalam tahun_terisi
        if tahun_range_diharapkan.issubset(tahun_terisi):
            # Menyusun rentang tahun yang sesuai (misal, 2019-2021)
            tahun_range = f"{min(tahun_terisi)}-{max(tahun_terisi)}" if len(tahun_terisi) > 1 else str(next(iter(tahun_terisi)))
            judul_terisi_data.append({
                'Judul Data': judul_data,
                'Tahun Data': tahun_range,
                'ID': id_data  # Menyimpan ID data untuk referensi
            })

# Hitung jumlah total judul data yang diambil dari API
total_judul_data = len(data_judul)

# Hitung jumlah judul data yang sudah terisi datanya
jumlah_terisi = len(judul_terisi_data)

# Tampilan jumlah data dengan Markdown
st.markdown(f"""
<div style="text-align: center; margin-bottom: 20px;">
    <h2 style="color: #2c3e50;">Jumlah Judul Data: <span style="color: #2980b9;">{total_judul_data}</span></h2>
    <h2 style="color: #2c3e50;">Judul Data Terisi: <span style="color: #27ae60;">{jumlah_terisi}</span></h2>
</div>
""", unsafe_allow_html=True)

# Menampilkan hasil dalam tabel
if judul_terisi_data:
    st.subheader(f"Judul Data yang sudah terisi data tahun {tahun_mulai} - {tahun_akhir} :")
    df = pd.DataFrame(judul_terisi_data)  # Mengubah list ke DataFrame
    st.dataframe(df)  # Menampilkan tabel dengan Streamlit

    # Menambahkan tombol untuk melihat data per judul
    for index, row in df.iterrows():
        id_data = row['ID']
        judul_data = row['Judul Data']
        
        # Tombol "Lihat Data" untuk setiap judul
        if st.button(f"Lihat Data {judul_data}", key=f"lihat_{id_data}"):
            # Ambil dan tampilkan data detail untuk judul yang diklik
            detail_data = get_data_detail(id_data)
            st.write(f"Detail Data untuk {judul_data}")
            st.dataframe(detail_data)  # Menampilkan data dalam bentuk tabel

    # Menambahkan tombol untuk mengunduh file Excel
    @st.cache_resource
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
