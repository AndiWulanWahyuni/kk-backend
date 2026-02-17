import firebase_admin
from firebase_admin import credentials, firestore
import os

def init_firebase():
    if not firebase_admin._apps:
        required_env = [
            "FIREBASE_TYPE",
            "FIREBASE_PROJECT_ID",
            "FIREBASE_PRIVATE_KEY",
            "FIREBASE_CLIENT_EMAIL",
        ]

        for var in required_env:
            if not os.getenv(var):
                raise ValueError(f"Environment variable {var} belum di-set di Render")

        cred_dict = {
            "type": os.getenv("FIREBASE_TYPE"),
            "project_id": os.getenv("FIREBASE_PROJECT_ID"),
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
            "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace("\\n", "\n"),
            "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
            "client_id": os.getenv("FIREBASE_CLIENT_ID"),
            "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
            "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
            "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER"),
            "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT"),
        }

        cred = credentials.Certificate(cred_dict)
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
