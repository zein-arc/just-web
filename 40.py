import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import bcrypt
from io import BytesIO
import plotly.express as px
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Konfigurasi Streamlit
st.set_page_config(page_title="Sistem Manajemen Peserta", page_icon=":tada:", layout="wide")

DB = 'participant.db'
DEFAULT_PASSWORD = '123'

# Data bidang
bidang_data = [
    "Networking", "Technical Support", "Computer Engineering", "Programming", "Multimedia", "Database", "System Analyst",
    "Graphic Design", "Office Tools", "Animasi", "Artificial Intelligence", "IT Governance", "Public Relation", "Public Speaking",
    "Ketrampilan dalam bidang perhotelan", "Manajemen hotel", "Pelayanan pelanggan",
    "Teknik Ukir Logam", "Teknik Ukir Kayu", "Merenda", "Menyulam", "Menenun", "Sablon", "Anyaman", "Teknik Batik Tulis dan Cap",
    "Penyamakan Kulit", "Finishing Kulit", "Pembuatan Produk dari Kulit", "Menjahit (Knitting, Woven)", "Teknik Bordir",
    "Fashion Design dan Technology", "Kecantikan Kulit dan Rambut",
    "Pelatihan Sekretaris", "Administrasi Perkantoran", "ICT for Secretary", "Keuangan", "Tata Niaga/Penjualan", "Bahasa Asing",
    "Promosi Produktivitas", "Bimbingan Konsultansi", "Pengukuran dan Manajemen Peningkatan Produktivitas", "Kewirausahaan",
    "Mesin Produksi", "Instalasi Pipa", "Kerja Pelat", "Pengecoran Logam", "CNC", "Las Industri", "Fabrikasi", "Teknik Kendaraan Ringan",
    "Teknik Sepeda Motor", "Teknik Alat Berat", "Instalasi Penerangan dan Tenaga", "Otomasi Industri", "Mekatronika", "Telekomunikasi",
    "Instrumentasi dan Kontrol", "Audio Video", "Refrigerasi Domestik", "Konstruksi (Batu, Kayu, Baja Ringan, Gipsum)",
    "Pengurus Rumah Tangga", "Penjaga Lanjut Usia", "Pengasuh Bayi/Balita", "Juru Masak",
    "Mekanisasi Pertanian", "Budidaya Tanaman dan Ikan", "Pengolahan Hasil Pertanian dan Perikanan",
    "Metodologi Pelatihan Kerja", "Kesehatan dan Keselamatan Kerja (K3)", "Pelatihan Motivasi", "Pengembangan Diri dan Karir",
    "Neuro Language Programming"
]

# Data Kecamatan
district_data = {
    "35.17.01": "Kecamatan Perak",
    "35.17.02": "Kecamatan Gudo",
    "35.17.03": "Kecamatan Ngoro",
    "35.17.04": "Kecamatan Bareng",
    "35.17.05": "Kecamatan Wonosalam",
    "35.17.06": "Kecamatan Mojoagung",
    "35.17.07": "Kecamatan Mojowarno",
    "35.17.08": "Kecamatan Diwek",
    "35.17.09": "Kecamatan Jombang",
    "35.17.10": "Kecamatan Peterongan",
    "35.17.11": "Kecamatan Sumobito",
    "35.17.12": "Kecamatan Kesamben",
    "35.17.13": "Kecamatan Tembelang",
    "35.17.14": "Kecamatan Ploso",
    "35.17.15": "Kecamatan Plandaan",
    "35.17.16": "Kecamatan Kabuh",
    "35.17.17": "Kecamatan Kudu",
    "35.17.18": "Kecamatan Bandarkedungmulyo",
    "35.17.19": "Kecamatan Jogoroto",
    "35.17.20": "Kecamatan Megaluh",
    "35.17.21": "Kecamatan Ngusikan",
    "35.17.15": "Kecamatan Mojowarno"
}

# Fungsi untuk mengirim email notifikasi
def send_email(subject, body, to_email):
    from_email = "youremail@example.com"  # Ganti dengan email Anda
    from_password = "yourpassword"  # Ganti dengan password email Anda

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(from_email, from_password)
    text = msg.as_string()
    server.sendmail(from_email, to_email, text)
    server.quit()

# Fungsi Hashing
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

# Verifikasi Password
def verify_password(password, hashed_password):
    return bcrypt.checkpw(password.encode(), hashed_password.encode())

# Buat Tabel (jika belum ada)
def init_db():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS peserta (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nik TEXT UNIQUE,
                    nama TEXT,
                    umur INTEGER,
                    jenis_kelamin TEXT,
                    bidang TEXT,
                    kecamatan TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password TEXT,
                    role TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS district (
                    code TEXT PRIMARY KEY,
                    name TEXT)''')
    
    for code, name in district_data.items():
        cursor.execute("INSERT OR IGNORE INTO district (code, name) VALUES (?, ?)", (code, name))
    
    cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)", ("admin", hash_password(DEFAULT_PASSWORD), "admin"))
    cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)", ("user", hash_password(DEFAULT_PASSWORD), "user"))
    conn.commit()
    conn.close()

# Fungsi untuk mengambil data dari database
def fetch_data(search_term=None, filter_term=None, sort_term=None):
    conn = sqlite3.connect(DB)
    query = "SELECT * FROM peserta"
    if search_term:
        query += " WHERE nik LIKE ? OR nama LIKE ?"
        df = pd.read_sql_query(query, conn, params=(f"%{search_term}%", f"%{search_term}%"))
    elif filter_term:
        query += " WHERE jenis_kelamin = ? OR bidang = ?"
        df = pd.read_sql_query(query, conn, params=(filter_term, filter_term))
    else:
        df = pd.read_sql_query(query, conn)
    if sort_term:
        df = df.sort_values(by=sort_term)
    conn.close()
    return df

# Fungsi untuk memasukkan data ke database
def insert_data(nik, nama, umur, jenis_kelamin, bidang, kecamatan):
    # Validasi input
    if len(nik) != 16:
        st.error("NIK harus 16 digit")
        return
    if not nik.isdigit():
        st.error("NIK harus berupa angka")
        return
    if not nama:
        st.error("Nama tidak boleh kosong")
        return
    if umur <= 0:
        st.error("Umur harus lebih dari 0")
        return
    if not jenis_kelamin:
        st.error("Jenis kelamin tidak boleh kosong")
        return
    if not bidang:
        st.error("Bidang tidak boleh kosong")
        return
    if not kecamatan:
        st.error("Kecamatan tidak boleh kosong")
        return

    try:
        conn = sqlite3.connect(DB)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO peserta (nik, nama, umur, jenis_kelamin, bidang, kecamatan) VALUES (?, ?, ?, ?, ?, ?)", 
                       (nik, nama, umur, jenis_kelamin, bidang, kecamatan))
        conn.commit()
        st.success("Peserta berhasil ditambahkan")
        send_email("Peserta Baru Ditambahkan", f"Peserta {nama} telah ditambahkan ke database.", "admin@example.com")
    except sqlite3.IntegrityError:
        st.error("NIK sudah ada")
    finally:
        conn.close()

# Fungsi untuk menghapus data dari database
def delete_data(id):
    try:
        conn = sqlite3.connect(DB)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM peserta WHERE id=?", (id,))
        conn.commit()
        conn.close()
        st.success("Peserta berhasil dihapus")
    except sqlite3.Error as e:
        st.error(f"Gagal menghapus peserta: {e}")

# Fungsi untuk memperbarui data
def update_data(id, nama, umur, jenis_kelamin, bidang, kecamatan):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("UPDATE peserta SET nama=?, umur=?, jenis_kelamin=?, bidang=?, kecamatan=? WHERE id= ?", 
                   (nama, umur, jenis_kelamin, bidang, kecamatan, id))
    conn.commit()
    conn.close()
    st.success("Peserta berhasil diperbarui")

# Fungsi untuk mengekspor data
def export_data():
    df = fetch_data()
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    st.download_button("Ekspor Data ke Excel", data=output, file_name="data_peserta.xlsx", mime="application/vnd.ms-excel")

# Fungsi untuk membuat PDF
def generate_pdf():
    df = fetch_data()
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.drawString(100, 750, "Laporan Data Peserta")
    y = 730
    for index, row in df.iterrows():
        pdf.drawString(100, y, f"NIK: {row['nik']} - Nama: {row['nama']} - Umur: {row['umur']} - Jenis Kelamin: {row['jenis_kelamin']} - Bidang: {row['bidang']} - Kecamatan: {row['kecamatan']}")
        y -= 20
        if y < 50:
            pdf.showPage()
            y = 750
    pdf.save()
    buffer.seek(0)
    st.download_button("Unduh Laporan PDF", data=buffer, file_name="Laporan_Peserta.pdf", mime="application/pdf")

# Fungsi untuk mempaginasikan data
def paginate(df, page_size, page_number):
    start = (page_number - 1) * page_size
    end = start + page_size
    return df.iloc[start:end]

# Fungsi untuk mengunggah data dari Excel
def upload_data_from_excel(file):
    df = pd.read_excel(file)
    for index, row in df.iterrows():
        insert_data(row['nik'], row['nama'], row['umur'], row['jenis_kelamin'], row['bidang'], row['kecamatan'])

# Fungsi untuk mengunggah data dari PDF
def upload_data_from_pdf(file):
    # Untuk membaca data dari PDF,  perlu menggunakan library seperti PyPDF2 atau pdfplumber
    # Namun, karena kompleksitasnya, saya tidak akan menambahkan fitur ini dalam contoh ini
    st.error("Fitur upload data dari PDF belum tersedia")

# Fungsi untuk mereset password
def reset_password(username, new_password):
    hashed_password = hash_password(new_password)
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET password=? WHERE username=?", (hashed_password, username))
    conn.commit()
    conn.close()
    st.success("Password berhasil direset")

# Halaman login
def login_page():
    st.title("Halaman Login")
    st.markdown(
        """
        <style>
        .login-form {
            background-color: #f0f2f6;
            padding: 2rem;
            border-radius: 10px;
        }
        .login-form input {
            margin-bottom: 1rem;
        }
        .login-form button {
            background-color: #4CAF50;
            color: white;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    with st.form("login_form", clear_on_submit=True):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        if submit:
            conn = sqlite3.connect(DB)
            cursor = conn.cursor()
            cursor.execute("SELECT password, role FROM users WHERE username=?", (username,))
            result = cursor.fetchone()
            conn.close()
            if result and verify_password(password, result[0]):
                st.session_state.logged_in = True
                st.session_state.role = result[1]
                st.success(f"Selamat datang {username}")
            else:
                st.error("Password salah")

# Halaman utama
def main_page():
    st.sidebar.title("Navigasi")
    menu = ["Home", "Tambahkan Peserta", "Lihat Data", "Hapus Data", "Ekspor Data", "Visualisasi", "Reset Password", "Logout"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Home":
        st.title("Selamat Datang di Sistem Manajemen Data Peserta")
        st.info("Navigasikan menggunakan sidebar")
    elif choice == "Tambahkan Peserta":
        st.header("Tambahkan Peserta Baru")
        with st.form("participant_form"):
            col1, col2 = st.columns(2)
            with col1:
                nik = st.text_input("NIK")
                nama = st.text_input("Nama")
                umur = st.number_input("Umur", min_value=1, max_value=100)
            with col2:
                jenis_kelamin = st.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"])
                bidang_input = st.text_input("Bidang", value="")
                bidang = st.selectbox("Bidang", options=bidang_data, index=bidang_data.index(bidang_input) if bidang_input in bidang_data else 0)
                kecamatan = st.selectbox("Kecamatan", options=[f"{code} - {name}" for code, name in district_data.items()])
            submit = st.form_submit_button("Tambahkan Peserta")
            if submit:
                insert_data(nik, nama, umur, jenis_kelamin, bidang, kecamatan)
    elif choice == "Lihat Data":
        st.title("Daftar Peserta")
        search_term = st.text_input("Cari berdasarkan NIK atau Nama")
        filter_term = st.selectbox("Filter berdasarkan", ["", "Laki-laki", "Perempuan", "Bidang"])
        sort_term = st.selectbox("Urutkan berdasarkan", ["", "nama", "umur"])
        page_size = st.number_input("Ukuran halaman", min_value=1, max_value=100)
        page_number = st.number_input("Nomor halaman", min_value=1, max_value=100)
        df = fetch_data(search_term, filter_term, sort_term)
        df = paginate(df, page_size, page_number)
        st.dataframe(df)
        
        # Tambahkan tombol edit
        id_to_edit = st.selectbox("Pilih peserta yang ingin diedit", df['id'])
        if not df[df['id'] == id_to_edit].empty:
            with st.form("edit_participant_form"):
                col1, col2 = st.columns(2)
                with col1:
                    nik = st.text_input("NIK", value=df.loc[df['id'] == id_to_edit, 'nik'].values[0])
                    nama = st.text_input("Nama", value=df.loc[df['id'] == id_to_edit, 'nama'].values[0])
                    umur = st.number_input("Umur", min_value=1, max_value=100, value=df.loc[df['id'] == id_to_edit, 'umur'].values[0])
                with col2:
                    jenis_kelamin = st.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"], index=["Laki-laki", "Perempuan"].index(df.loc[df['id'] == id_to_edit, 'jenis_kelamin'].values[0]))
                    bidang_input = st.text_input("Bidang", value="")
                    bidang = st.selectbox("Bidang", options=bidang_data, index=bidang_data.index(bidang_input) if bidang_input in bidang_data else 0)
                    kecamatan = st.selectbox("Kecamatan", options=[f"{code} - {name}" for code, name in district_data.items()], index=[f"{code} - {name}" for code, name in district_data.items()].index(df.loc[df['id'] == id_to_edit, 'kecamatan'].values[0]))
                submit = st.form_submit_button("Simpan Perubahan")
                if submit:
                    update_data(id_to_edit, nama, umur, jenis_kelamin, bidang, kecamatan)
                    
                    # Fetch updated data after editing
                    df = fetch_data(search_term, filter_term, sort_term)  # Re-fetch the data
                    st.dataframe(df)  # Re-render the table with updated data
                    st.success("Data peserta berhasil diperbarui")
        else:
            st.error("Peserta tidak ditemukan")
    elif choice == "Hapus Data":
        st.title("Hapus Peserta")
        df = fetch_data()
        st.dataframe(df)
        id_to_delete = st.selectbox("Pilih peserta yang ingin dihapus", df['id'])
        if st.button("Hapus"):
            delete_data(id_to_delete)
    elif choice == "Ekspor Data":
        st.title("Ekspor Data")
        export_data()
        generate_pdf()
    elif choice == "Visualisasi":
        st.title("Visualisasi Data")
        df = fetch_data()
        fig = px.bar(df, x='kecamatan', color='jenis_kelamin')
        st.plotly_chart(fig)
    elif choice == "Reset Password":
        st.title("Reset Password")
        with st.form("reset_password_form"):
            username = st.text_input("Username")
            new_password = st.text_input("Password Baru", type="password")
            submit = st.form_submit_button("Reset Password")
            if submit:
                reset_password(username, new_password)
    elif choice == "Logout":
        st.session_state.logged_in = False
        st.session_state.role = None
        st.success("Anda telah logout")
        st.stop()
    else:
        st.error("Anda tidak memiliki akses ke halaman ini")

# Eksekusi utama
init_db()

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    login_page()
else:
    main_page()