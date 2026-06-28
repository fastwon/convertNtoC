"""API-key validation and masking.

Never include the raw key in return messages, logs, or exceptions.
"""
from __future__ import annotations

import anthropic


def mask_secret(secret: str | None) -> str | None:
    """Display-safe form: only the last 4 chars are ever shown."""
    if not secret:
        return None
    if len(secret) <= 4:
        return "••••"
    return "••••" + secret[-4:]


def validate_anthropic_key(key: str) -> tuple[bool, str]:
    """Validate by making one cheap, real call (models.list). No retries."""
    if not key or not key.strip():
        return False, "키가 비어 있습니다"
    try:
        client = anthropic.Anthropic(api_key=key.strip(), max_retries=0, timeout=10.0)
        client.models.list()  # raises on an invalid/unauthorized key
        return True, "유효한 Anthropic 키입니다"
    except anthropic.AuthenticationError:
        return False, "인증 실패: 키가 올바르지 않습니다"
    except anthropic.PermissionDeniedError:
        return False, "권한 없음: 이 키로는 접근할 수 없습니다"
    except anthropic.APIConnectionError:
        return False, "네트워크 오류: 인터넷 연결을 확인하세요"
    except anthropic.APIStatusError as e:
        return False, f"검증 실패 (HTTP {e.status_code})"
    except Exception:
        return False, "알 수 없는 오류로 검증에 실패했습니다"


def validate_image_key(key: str) -> tuple[bool, str]:
    """Image provider is undecided (P6); for now accept a non-empty key and store it.

    Real validation (provider ping) lands once the provider is chosen.
    """
    if not key or not key.strip():
        return False, "키가 비어 있습니다"
    return True, "저장됨 (실제 검증은 이미지 공급자 확정 후 P6에서 추가)"
