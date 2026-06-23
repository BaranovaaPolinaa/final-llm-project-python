from jose import ExpiredSignatureError, JWTError, jwt

from app.core.config import settings


def decode_and_validate(token: str) -> dict:
    """
    Validate JWT signature and expiration.
    Returns decoded payload on success.
    Raises ValueError with a descriptive message on failure.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALG],
        )
    except ExpiredSignatureError:
        raise ValueError("Token has expired")
    except JWTError as exc:
        raise ValueError(f"Invalid token: {exc}") from exc

    if "sub" not in payload:
        raise ValueError("Token is missing 'sub' claim")

    return payload
