"""
Netlify Deploy Tool - deployt boumax.nl via Netlify's API (Zip-based deploy),
zonder Netlify CLI.

Gebruik:
    python deploy.py

Leest het token uit een lokaal .env-bestand (nooit in de chat of in dit
bestand). Toont of logt het token nooit.

Sinds de A+ sync (17-08-2026): dit script deployt NOOIT meer rechtstreeks de
lokale deploy/-map. Het roept eerst sync_with_github.sync() aan, die lokale
wijzigingen en GitHub (waar de dagelijkse cloud-routine ook uit put)
tweerichtings samenvoegt en pusht. Alleen bij een succesvolle push wordt de
zojuist gepushte GitHub-snapshot gedeployd - nooit de ruwe lokale map. Lukt
de sync niet, dan gebeurt er geen deploy. Zie sync_with_github.py voor de
volledige uitleg en het padbeleid.
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
ROOT_DIR = PROJECT_DIR.parent
ENV_PATH = PROJECT_DIR / ".env"

sys.path.insert(0, str(ROOT_DIR))
import sync_with_github  # noqa: E402

REPO_URL = "https://github.com/johanbouma/boumax-cloud-routine.git"
SITE_ID = "d37dcd8a-30ab-498e-a29d-f021c5999ac5"  # boumax.nl
API_URL = f"https://api.netlify.com/api/v1/sites/{SITE_ID}/deploys"
UPLOAD_TIMEOUT_S = 90
STATUS_POLL_TIMEOUT_S = 60
STATUS_POLL_INTERVAL_S = 3


def verify_still_latest(expected_sha: str) -> bool:
    """Race-check vlak voor de upload: is origin/main nog steeds de commit
    die we net gepusht hebben? Zo niet, heeft iets anders (bijv. de
    cloud-routine) tussentijds gepusht - dan niet deployen."""
    result = subprocess.run(
        ["git", "ls-remote", REPO_URL, "main"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if result.returncode != 0:
        print(f"Waarschuwing: kon origin/main niet verifieren ({result.stderr.strip()}).", file=sys.stderr)
        return False
    remote_sha = result.stdout.split()[0] if result.stdout.strip() else ""
    return remote_sha == expected_sha


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


def poll_deploy_status(deploy_id: str, token: str) -> dict:
    """Vraagt kort (begrensd, max STATUS_POLL_TIMEOUT_S) de deploy-status op
    totdat Netlify 'ready' of 'error' meldt, i.p.v. te vertrouwen dat een
    geslaagde upload ook een geslaagde publicatie betekent."""
    status_url = f"https://api.netlify.com/api/v1/deploys/{deploy_id}"
    deadline = time.monotonic() + STATUS_POLL_TIMEOUT_S
    last_body: dict = {}
    while time.monotonic() < deadline:
        req = urllib.request.Request(status_url, headers={"Authorization": f"Bearer {token}"})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                last_body = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError):
            time.sleep(STATUS_POLL_INTERVAL_S)
            continue
        if last_body.get("state") in ("ready", "error"):
            return last_body
        time.sleep(STATUS_POLL_INTERVAL_S)
    return last_body


def main() -> int:
    print("Stap 1/3: synchroniseren met GitHub voordat er gedeployd wordt ...")
    try:
        deploy_dir, sha = sync_with_github.sync()
    except sync_with_github.SyncError as exc:
        print(f"\nSync mislukt, GEEN deploy uitgevoerd:\n{exc}", file=sys.stderr)
        return 1

    if not deploy_dir.exists():
        print(f"Deploy-map niet gevonden: {deploy_dir}", file=sys.stderr)
        return 1

    print("\nStap 2/3: publiceren naar Netlify ...")
    env = load_env(ENV_PATH)
    token = env.get("NETLIFY_AUTH_TOKEN")
    if not token:
        print(
            "NETLIFY_AUTH_TOKEN ontbreekt in .env. Kopieer .env.example naar "
            ".env en vul het token in.",
            file=sys.stderr,
        )
        return 1

    if not verify_still_latest(sha):
        print(
            "Afgebroken: origin/main is sinds de sync alweer veranderd (waarschijnlijk "
            "heeft iets anders net gepusht). Draai het script opnieuw.",
            file=sys.stderr,
        )
        return 1

    print(f"Zip bouwen van {deploy_dir} (gepushte GitHub-snapshot {sha[:8]}) ...")
    zip_bytes = build_zip(deploy_dir)
    print(f"Zip-grootte: {len(zip_bytes) / 1024:.1f} KB")

    print("Stap 3/3: uploaden naar Netlify ...")
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
        with urllib.request.urlopen(req, timeout=UPLOAD_TIMEOUT_S) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        print(f"Deploy mislukt (HTTP {exc.code}). Controleer het token.", file=sys.stderr)
        return 1
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"Deploy mislukt: kon Netlify niet bereiken ({exc}).", file=sys.stderr)
        return 1

    deploy_id = body.get("id")
    deploy_url = body.get("deploy_ssl_url") or body.get("deploy_url")
    print(f"Geupload, status: {body.get('state', 'onbekend')}")
    if deploy_url:
        print(f"Preview: {deploy_url}")

    if not deploy_id:
        print("Waarschuwing: geen deploy-ID ontvangen, kon einduitkomst niet verifieren.", file=sys.stderr)
        return 0

    print("Wachten op definitieve status van Netlify ...")
    final = poll_deploy_status(deploy_id, token)
    final_state = final.get("state", "onbekend")
    summary = final.get("summary") or {}

    if final_state == "ready":
        print("Bevestigd: deploy is 'ready' en live op https://boumax.nl")
        if summary.get("messages"):
            for m in summary["messages"]:
                title = m.get("title") or m.get("description")
                if title:
                    print(f"  - {title}")
    elif final_state == "error":
        print(
            f"Deploy is mislukt volgens Netlify (state=error): "
            f"{final.get('error_message', 'geen foutdetail beschikbaar')}",
            file=sys.stderr,
        )
        return 1
    else:
        print(
            f"Waarschuwing: status na {STATUS_POLL_TIMEOUT_S}s nog steeds "
            f"'{final_state}', niet bevestigd als 'ready'. Controleer handmatig op "
            "https://app.netlify.com.",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
