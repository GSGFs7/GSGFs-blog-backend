import json
from functools import lru_cache
from pathlib import Path

from django import template
from django.conf import settings
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()


@lru_cache(maxsize=1)
def _load_manifest(path: Path):
    return json.loads(path.read_text())


@lru_cache(maxsize=1)
def _manifest_path() -> Path:
    return Path(settings.BASE_DIR / "web/static/ssr/solid-islands.json")


@register.simple_tag
def solid_island(name: str, **props):
    item = _load_manifest(_manifest_path())["islands"][name]
    merged_props = {**item.get("props", {}), **props}
    return format_html(
        '<div data-solid-island="{}" data-solid-ssr data-props="{}">{}</div>',
        name,
        json.dumps(merged_props, separators=(",", ":")),
        mark_safe(item["html"]),
    )
