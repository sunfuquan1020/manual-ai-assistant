"""Shared prompt + JSON parsing for photo-based device identification."""
from __future__ import annotations

import json

from .base import DeviceIdentification

VISION_SYSTEM = (
    "You identify home appliances/electronic devices from a photo. "
    "Read any visible brand logos, model numbers, and labels."
)

VISION_INSTRUCTION = (
    "识别照片中的设备。只返回一个 JSON 对象，不要其它文字，字段如下：\n"
    '{"brand": 品牌或null, "model_number": 型号或null, '
    '"category": 大类(如"空调"/"洗衣机")或null, '
    '"device_type": 具体类型或null, '
    '"keywords": [用于搜索说明书的中英文关键词数组]}'
)


def parse_identification(text: str) -> DeviceIdentification:
    """Best-effort extraction of the first JSON object from model output."""
    raw = text.strip()
    obj: dict = {}
    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        try:
            obj = json.loads(raw[start : end + 1])
        except json.JSONDecodeError:
            obj = {}

    keywords = obj.get("keywords") or []
    if not isinstance(keywords, list):
        keywords = [str(keywords)]
    keywords = [str(k) for k in keywords if k]

    return DeviceIdentification(
        brand=_clean(obj.get("brand")),
        model_number=_clean(obj.get("model_number")),
        category=_clean(obj.get("category")),
        device_type=_clean(obj.get("device_type")),
        keywords=keywords,
        raw=raw,
    )


def _clean(value: object) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    return s or None
