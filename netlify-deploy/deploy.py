"""
Netlify Deploy Tool - deployt de boumax-automatiseringen/deploy map naar
boumax.nl via Netlify's API (Zip-based deploy), zonder Netlify CLI.

Gebruik:
    python deploy.py

Leest het token uit een lokaal .env-bestand (nooit in de chat of in dit
bestand). Toont of logt het token nooit.
"""

from __future__ import annotations

import io
import json
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
ENV_PATH = PROJECT_DIR / ".env"
DEPLOY_DIR = PROJECT_DIR.parent / "deploy"

SITE_ID = "d37dcd8a-30ab-498e-a29d-f021c5999ac5"  # boumax.nl
API_URL = f"https://api.netlify.com/api/v1/sites/{SITE_ID}/deploys"


def load_env(path: Path) -> dict:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def build_zip(source_dir: Path) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in source_dir.rglob("*"):
            if path.is_file():
                zf.write(path, path.relative_to(source_dir))
    return buffer.getvalue()


def main() -> int:
    if not DEPLOY_DIR.exists():
        print(f"Deploy-map niet gevonden: {DEPLOY_DIR}", file=sys.stderr)
        return 1

    env = load_env(ENV_PATH)
    token = env.get("NETLIFY_AUTH_TOKEN")
    if not token:
        print(
            "NETLIFY_AUTH_TOKEN ontbreekt in .env. Kopieer .env.example naar "
            ".env en vul het token in.",
            file=sys.stderr,
        )
        return 1

    print(f"Zip bouwen van {DEPLOY_DIR} ...")
    zip_bytes = build_zip(DEPLOY_DIR)
    print(f"Zip-grootte: {len(zip_bytes) / 1024:.1f} KB")

    print("Uploaden naar Netlify ...")
    req = urllib.request.Request(
        API_URL,
        data=zip_bytes,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/zip",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        print(f"Deploy mislukt (HTTP {exc.code}). Controleer het token.", file=sys.stderr)
        return 1

    state = body.get("state", "onbekend")
    deploy_url = body.get("deploy_ssl_url") or body.get("deploy_url")
    print(f"Status: {state}")
    if deploy_url:
        print(f"Preview: {deploy_url}")
    print("Live op: https://boumax.nl (kan een paar seconden duren om te verwerken)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
