import io
import re
import pdfplumber

def extract_kk_data(pdf_bytes: bytes) -> dict:
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            page = pdf.pages[0]
            raw_text = page.extract_text() or ""
            tables = page.extract_tables() or []
    except Exception as e:
        raise Exception(f"Gagal membaca PDF: {e}")

    if not tables or len(tables[0]) == 0:
        raise Exception("Tabel KK tidak ditemukan pada PDF!")

    table = tables[0]
    text = raw_text.replace("\r", "\n")

    def _find(text, pattern):
      m = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
      return m.group(1).strip() if m else None

    nomor_kk = _find(text, r"No\.\s*(\d{16})")
    kepala_keluarga = _find(text, r"Nama Kepala Keluarga\s*:\s*(.*?)(?=\s+Desa\/Kelurahan|\n|$)")
    desa_kelurahan = _find(text, r"Desa\/Kelurahan\s*:\s*(.*?)(?=\s+Alamat|\n|$)")
    alamat = _find(text, r"Alamat\s*:\s*(.*?)(?=\s+Kecamatan|\n|$)")
    kecamatan = _find(text, r"Kecamatan\s*:\s*(.*?)(?=\s+RT\/RW|\n|$)")
    rt_rw = _find(text, r"RT\/RW\s*:\s*([\d\/]+)")
    kabupaten_kota = _find(text, r"Kabupaten\/Kota\s*:\s*(.*?)(?=\s+Kode Pos|\n|$)")
    kode_pos = _find(text, r"Kode Pos\s*:\s*(\d{5})")
    provinsi = _find(text, r"Provinsi\s*:\s*(.*?)(?=\s+Jenis|\n|$)")
    tanggal_terbit = _find(text, r"Dikeluarkan Tanggal[: ]+(\d{2}-\d{2}-\d{4})")

    idx_status = None
    for i, row in enumerate(table):
        if len(row) > 1 and isinstance(row[1], str) and row[1].strip().startswith("Status"):
            idx_status = i
            break

    if idx_status is None:
        raise Exception("Tabel Status Keluarga tidak ditemukan!")

    data_pribadi = table[3:idx_status - 1]
    data_status = table[idx_status + 3:]

    status_map = {}
    for row in data_status:
        no = row[0]
        if no and str(no).isdigit():
            status_map[int(no)] = row

    anggota_list = []

    for row in data_pribadi:
        if not row[1] or row[1] == "-":
            continue

        no = int(row[0])
        s = status_map.get(no, [None] * len(data_status[0]))

        anggota_list.append({
            "nama": row[1],
            "nik": row[4],
            "jenis_kelamin": row[6],
            "tempat_lahir": row[8],
            "tanggal_lahir": row[10],
            "agama": row[12],
            "pendidikan": row[13],
            "pekerjaan": row[14],
            "golongan_darah": row[16],
            "status_perkawinan": s[1],
            "tanggal_perkawinan": s[2],
            "status_dalam_keluarga": s[3],
            "kewarganegaraan": s[5],
            "ayah": s[11],
            "ibu": s[15],
        })

    return {
        "nomor_kk": nomor_kk,
        "kepala_keluarga": kepala_keluarga,
        "alamat": alamat,
        "rt_rw": rt_rw,
        "kode_pos": kode_pos,
        "desa_kelurahan": desa_kelurahan,
        "kecamatan": kecamatan,
        "kabupaten_kota": kabupaten_kota,
        "provinsi": provinsi,
        "tanggal_terbit": tanggal_terbit,
        "anggota_keluarga": anggota_list
    }
