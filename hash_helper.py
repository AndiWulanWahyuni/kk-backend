from blake3 import blake3
import json

def generate_hash(data_dict: dict) -> bytes:
    if not isinstance(data_dict, dict):
        raise ValueError("Data KK tidak valid untuk proses hashing.")

    normalized = {
        "nomor_kk": str(data_dict.get("nomor_kk", "")).lower().strip(),
        "kepala_keluarga": str(data_dict.get("kepala_keluarga", "")).lower().strip(),
        "alamat": str(data_dict.get("alamat", "")).lower().strip(),
        "rt_rw": str(data_dict.get("rt_rw", "")).lower().strip(),
        "kode_pos": str(data_dict.get("kode_pos", "")).lower().strip(),
        "desa_kelurahan": str(data_dict.get("desa_kelurahan", "")).lower().strip(),
        "kecamatan": str(data_dict.get("kecamatan", "")).lower().strip(),
        "kabupaten_kota": str(data_dict.get("kabupaten_kota", "")).lower().strip(),
        "provinsi": str(data_dict.get("provinsi", "")).lower().strip(),
        "tanggal_terbit": str(data_dict.get("tanggal_terbit", "")).lower().strip(),
    }

    anggota_list = data_dict.get("anggota_keluarga", [])
    normalized_anggota = []

    for anggota in anggota_list:
        normalized_anggota.append({
            "nama": str(anggota.get("nama", "")).lower().strip(),
            "nik": str(anggota.get("nik", "")).lower().strip(),
            "jenis_kelamin": str(anggota.get("jenis_kelamin", "")).lower().strip(),
            "tempat_lahir": str(anggota.get("tempat_lahir", "")).lower().strip(),
            "tanggal_lahir": str(anggota.get("tanggal_lahir", "")).lower().strip(),
            "agama": str(anggota.get("agama", "")).lower().strip(),
            "pendidikan": str(anggota.get("pendidikan", "")).lower().strip(),
            "pekerjaan": str(anggota.get("pekerjaan", "")).lower().strip(),
            "golongan_darah": str(anggota.get("golongan_darah", "")).lower().strip(),
            "status_perkawinan": str(anggota.get("status_perkawinan", "")).lower().strip(),
            "tanggal_perkawinan": str(anggota.get("tanggal_perkawinan", "")).lower().strip(),
            "status_dalam_keluarga": str(anggota.get("status_dalam_keluarga", "")).lower().strip(),
            "kewarganegaraan": str(anggota.get("kewarganegaraan", "")).lower().strip(),
            "ayah": str(anggota.get("ayah", "")).lower().strip(),
            "ibu": str(anggota.get("ibu", "")).lower().strip(),
        })

    normalized["anggota_keluarga"] = sorted(normalized_anggota, key=lambda x: x["nik"])

    data_str = json.dumps(normalized, ensure_ascii=False, sort_keys=True)

    return blake3(data_str.encode("utf-8")).digest()
