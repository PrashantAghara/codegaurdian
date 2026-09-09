import hashlib
import hmac

from fastapi import HTTPException, Request

from app.core.config import settings


async def verify_github_signature(request: Request) -> bytes:
    """Verify the X-Hub-Signature-256 header against GITHUB_WEBHOOK_SECRET. Returns the raw body if valid."""
    body = await request.body()
    signature_header = request.headers.get("X-Hub-Signature-256")

    if not signature_header:
        raise HTTPException(status_code=401, detail="Missing signature header")

    expected = (
        "sha256="
        + hmac.new(
            settings.github_webhook_secret.encode(), body, hashlib.sha256
        ).hexdigest()
    )

    if not hmac.compare_digest(expected, signature_header):
        raise HTTPException(status_code=401, detail="Invalid signature")

    return body
