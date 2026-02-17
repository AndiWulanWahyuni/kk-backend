import firebase_admin
from firebase_admin import credentials, firestore
import os

def init_firebase():
    if not firebase_admin._apps:
        cred_path = os.path.join(os.path.dirname(__file__), "firebase_config.json")

        if not os.path.exists(cred_path):
            raise FileNotFoundError("File firebase_config.json tidak ditemukan di folder backend!")

        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)

    return firestore.client()

db = init_firebase()

def save_kk_record(
    doc_id: str,
    version: int,
    data_kk: dict,
    data_hash: str,
    signature: str,
    public_key: str,
    algorithm: str,
    signer_name: str,
    status: str = "Aktif"
):
    
    firestore_id = f"{doc_id}_v{version}"
    
    db.collection("kartu_keluarga").document(firestore_id).set({
        "doc_id": doc_id,
        "version": version,
        "data_kk": data_kk,
        "data_hash": data_hash,
        "signature": signature,
        "public_key": public_key,
        "algorithm": algorithm,
        "signer_name": signer_name,
        "status": status,
        "is_active": status == "Aktif",
        "created_at": firestore.SERVER_TIMESTAMP,
    })

def get_kk_by_version(doc_id: str, version: int):
    firestore_id = f"{doc_id}_v{version}"
    doc = db.collection("kartu_keluarga").document(firestore_id).get()
    return doc.to_dict() if doc.exists else None

def get_all_versions(doc_id: str):
    docs = (
        db.collection("kartu_keluarga")
        .where("doc_id", "==", doc_id)
        .stream()
    )
    return sorted(
        [d.to_dict() for d in docs],
        key=lambda x: x.get("version", 0)
    )
