import os
import base64
from pqcrypto.sign import ml_dsa_65

PRIVATE_KEY_B64 = os.getenv("ML_DSA_PRIVATE_KEY_BASE64")
PUBLIC_KEY_B64 = os.getenv("ML_DSA_PUBLIC_KEY_BASE64")

if not PRIVATE_KEY_B64 or not PUBLIC_KEY_B64:
    raise ValueError("Private/Public key not found in environment variables.")

SECRET_KEY = base64.b64decode(PRIVATE_KEY_B64)
PUBLIC_KEY = base64.b64decode(PUBLIC_KEY_B64)

def sign_document(hash_bytes: bytes) -> dict:
    if not isinstance(hash_bytes, (bytes, bytearray)):
        raise TypeError("Hash must be bytes")

    signature = ml_dsa_65.sign(SECRET_KEY, hash_bytes)

    return {
        "signature": base64.b64encode(signature).decode(),
        "public_key": base64.b64encode(PUBLIC_KEY).decode(),
        "algorithm": "ML-DSA-65"
    }

def verify_document(
    hash_bytes: bytes,
    signature_b64: str,
    public_key_b64: str
) -> bool:
    try:
        signature = base64.b64decode(signature_b64)
        public_key = base64.b64decode(public_key_b64)
        ml_dsa_65.verify(public_key, hash_bytes, signature)
        return True
    except Exception:
        return False
