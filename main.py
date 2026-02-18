from datetime import datetime, timezone
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from firebase_init import (
    db,
    save_kk_record,
    get_all_versions,
    get_kk_by_version,
)
from extract_data import extract_kk_data
from hash_helper import generate_hash
from signature_helper import sign_document, verify_document
from qr_helper import generate_qr_response

import os
FRONTEND_URL = os.getenv("FRONTEND_URL")

app = FastAPI(
    title="API Verifikasi KK (BLAKE3 + ML-DSA-65)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "status": "Ok",
        "message": "API Verifikasi KK (BLAKE3 + ML-DSA-65) aktif"
    }

@app.post("/upload")
async def upload_kk(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "File harus PDF")

    pdf_bytes = await file.read()
    data = extract_kk_data(pdf_bytes)

    nomor_kk = data.get("nomor_kk")
    if not nomor_kk:
        raise HTTPException(400, "Nomor KK tidak ditemukan")

    version = 1

    hash_bytes = generate_hash(data)
    sig = sign_document(hash_bytes)

    save_kk_record(
        doc_id=nomor_kk,
        version=version,
        data_kk=data,
        data_hash=hash_bytes.hex(),
        signature=sig["signature"],
        public_key=sig["public_key"],
        algorithm=sig["algorithm"],
        signer_name="YATI (KEPALA DINAS KEPENDUDUKAN DAN PENCATATAN SIPIL KOTA PALU)",
        status="Aktif"
    )

    verify_url = f"{FRONTEND_URL}/?doc_id={nomor_kk}&v={version}"

    return {
        "message": "Data KK Berhasil Disimpan dan ditandatangani",
        "verify_url": verify_url
    }

@app.post("/verify/pdf")
async def verify_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "File harus PDF")

    pdf_bytes = await file.read()
    data = extract_kk_data(pdf_bytes)

    doc_id = data.get("nomor_kk")
    if not doc_id:
        raise HTTPException(400, "Nomor KK tidak ditemukan")

    records = get_all_versions(doc_id)

    timestamp = datetime.now(timezone.utc).astimezone().strftime(
        "%d-%m-%Y %H:%M:%S"
    )

    # 1️⃣ DATA TIDAK TERDAFTAR
    if not records:
        return {
            "valid": False,
            "status": "Data KK Tidak Ada Di Sistem",
            "integritas_data": "-",
            "digital_signature": "-",
            "signer_name": "-",
            "nomor_kk": doc_id,
            "verified_at": timestamp
        }

    # 2️⃣ CEK HASH
    recalculated_hash = generate_hash(data)
    matched_record = None

    for record in records:
        stored_hash = bytes.fromhex(record["data_hash"])
        if recalculated_hash == stored_hash:
            matched_record = record
            break

    if not matched_record:
        return {
            "valid": False,
            "status": "Data Telah Dimodifikasi",
            "integritas_data": "TIDAK TERJAGA",
            "digital_signature": "TIDAK VALID",
            "signer_name": "-",
            "nomor_kk": doc_id,
            "verified_at": timestamp
        }

    # 3️⃣ CEK SIGNATURE (WAJIB)
    valid_signature = verify_document(
        hash_bytes=recalculated_hash,
        signature_b64=matched_record["signature"],
        public_key_b64=matched_record["public_key"]
    )

    if not valid_signature:
        return {
            "valid": False,
            "status": "Signature Tidak Valid",
            "integritas_data": "-",
            "digital_signature": "TIDAK VALID",
            "signer_name": matched_record["signer_name"],
            "nomor_kk": doc_id,
            "verified_at": timestamp
        }

    # 4️⃣ CEK STATUS DOKUMEN
    if matched_record["status"] != "Aktif":
        return {
            "valid": False,
            "status": "Dokumen Tidak Aktif",
            "integritas_data": "TERJAGA",
            "digital_signature": "VALID",
            "signer_name": matched_record["signer_name"],
            "nomor_kk": doc_id,
            "verified_at": timestamp
        }

    # 5️⃣ SEMUA VALID
    return {
        "valid": True,
        "status": "Aktif",
        "integritas_data": "TERJAGA",
        "digital_signature": "VALID",
        "signer_name": matched_record["signer_name"],
        "nomor_kk": doc_id,
        "verified_at": timestamp
    }

@app.get("/verify/qr")
def verify_qr(doc_id: str, v: int):
    record = get_kk_by_version(doc_id, v)

    timestamp = datetime.now(timezone.utc).astimezone().strftime(
        "%d-%m-%Y %H:%M:%S"
    )

    # 1️⃣ DATA TIDAK TERDAFTAR
    if not record:
        return {
            "valid": False,
            "status": "Data KK Tidak Ada Di Sistem",
            "integritas_data": "-",
            "digital_signature": "-",
            "data_kk": None,
            "signer_name": "-",
            "nomor_kk": doc_id,
            "verified_at": timestamp
        }

    # 2️⃣ CEK HASH
    recalculated_hash = generate_hash(record["data_kk"])
    stored_hash = bytes.fromhex(record["data_hash"])

    if recalculated_hash != stored_hash:
        return {
            "valid": False,
            "status": "Data Telah Dimodifikasi",
            "integritas_data": "TIDAK TERJAGA",
            "digital_signature": "TIDAK VALID",
            "data_kk": None,
            "signer_name": "-",
            "nomor_kk": doc_id,
            "verified_at": timestamp
        }

    # 3️⃣ CEK SIGNATURE (WAJIB SEBELUM STATUS)
    valid_signature = verify_document(
        hash_bytes=recalculated_hash,
        signature_b64=record["signature"],
        public_key_b64=record["public_key"]
    )

    if not valid_signature:
        return {
            "valid": False,
            "status": "Signature Tidak Valid",
            "integritas_data": "TERJAGA",
            "digital_signature": "TIDAK VALID",
            "data_kk": None,
            "signer_name": record["signer_name"],
            "nomor_kk": doc_id,
            "verified_at": timestamp
        }

    # 4️⃣ STATUS DOKUMEN
    if record["status"] != "Aktif":
        return {
            "valid": False,
            "status": "Dokumen Tidak Aktif",
            "integritas_data": "TERJAGA",
            "digital_signature": "VALID",
            "data_kk": None,
            "signer_name": record["signer_name"],
            "nomor_kk": doc_id,
            "verified_at": timestamp
        }

    # 5️⃣ SEMUA VALID
    return {
        "valid": True,
        "status": "Aktif",
        "integritas_data": "TERJAGA",
        "digital_signature": "VALID",
        "data_kk": record["data_kk"],
        "signer_name": record["signer_name"],
        "nomor_kk": doc_id,
        "verified_at": timestamp
    }

@app.put("/update/{nomor_kk}")
async def update_kk(nomor_kk: str, file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "File harus PDF")

    pdf_bytes = await file.read()
    data = extract_kk_data(pdf_bytes)

    if not data.get("nomor_kk"):
        raise HTTPException(400, "Nomor KK tidak ditemukan pada PDF")

    if data["nomor_kk"] != nomor_kk:
        raise HTTPException(400, "Nomor KK pada PDF tidak sesuai")

    docs = (
        db.collection("kartu_keluarga")
        .where("doc_id", "==", nomor_kk)
        .stream()
    )

    old_docs = list(docs)
    if not old_docs:
        raise HTTPException(404, "Data KK Tidak Ada Di Sistem")

    versions = []

    for doc in old_docs:
        doc_data = doc.to_dict()
        versions.append(doc_data.get("version", 1))

        if doc_data.get("status") == "Aktif":
            doc.reference.update({
                "status": "Tidak Aktif",
                "is_active": False,
                "deactivated_at": datetime.now(timezone.utc)
                .astimezone()
                .strftime("%d-%m-%Y %H:%M:%S")
            })

    new_version = max(versions) + 1

    hash_bytes = generate_hash(data)
    sig = sign_document(hash_bytes)

    timestamp = datetime.now(timezone.utc).astimezone().strftime(
        "%d-%m-%Y %H:%M:%S"
    )

    save_kk_record(
        doc_id=nomor_kk,
        version=new_version,
        data_kk=data,
        data_hash=hash_bytes.hex(),
        signature=sig["signature"],
        public_key=sig["public_key"],
        algorithm=sig["algorithm"],
        signer_name="YATI (KEPALA DINAS KEPENDUDUKAN DAN PENCATATAN SIPIL KOTA PALU)",
        status="Aktif"
    )

    verify_url = (
        f"{FRONTEND_URL}/?doc_id={nomor_kk}&v={new_version}"
    )

    return {
        "message": "Data KK berhasil diperbarui",
        "doc_id": nomor_kk,
        "version": new_version,
        "verify_url": verify_url,
        "updated_at": timestamp
    }

@app.get("/qr")
def get_qr_code(doc_id: str, v: int):
    verify_url = (
        f"{FRONTEND_URL}/?doc_id={doc_id}&v={v}"
    )
    return generate_qr_response(verify_url)

@app.get("/data")
def get_all():
    docs = db.collection("kartu_keluarga").stream()
    return {
        "status": "success",
        "data": [d.to_dict() for d in docs]
    }
