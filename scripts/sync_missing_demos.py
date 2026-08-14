"""
Sync Missing Demos - haalt op welke demo-<naam>/ mappen live staan op
boumax.nl (via Netlify's API) en zet ontbrekende mappen (én ontbrekende
foto's daarbinnen) terug in deze repo.

Vervangt de git-push-stap die de Claude-cloud-routine zelf niet kan
uitvoeren (bekende Anthropic-bug, GitHub-connector geeft geen
schrijfrechten - zie github.com/anthropics/claude-code/issues/80874 en
#79393). Draait als GitHub Action met het ingebouwde GITHUB_TOKEN, dus
volledig onafhankelijk van die kapotte koppeling.

Gebruikt alleen Python-stdlib (geen dependencies nodig in de Action).
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

SITE_ID = "d37dcd8a-30ab-498e-a29d-f021c5999ac5"  # boumax.nl
REPO_ROOT = Path(__file__).resolve().parent.parent
DEPLOY_DIR = REPO_ROOT / "deploy"
TEMPLATE_IMAGES_DIR = REPO_ROOT / "website-demo-schilders" / "images"

_DEMO_SLUG_RE = re.compile(r"^/(demo-[a-z0-9-]+)/index\.html$")


def netlify_get(path: str, token: str) -> dict:
    req = urllib.request.Request(
        f"https://api.netlify.com/api/v1{path}",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_live_demo_slugs(token: str) -> set[str]:
    site = netlify_get(f"/sites/{SITE_ID}", token)
    deploy_id = (site.get("published_deploy") or {}).get("id")
    if not deploy_id:
        print("Geen published_deploy gevonden bij Netlify.", file=sys.stderr)
        return set()

    files = netlify_get(f"/deploys/{deploy_id}/files", token)
    slugs: set[str] = set()
    for entry in files:
        match = _DEMO_SLUG_RE.match(entry.get("path", ""))
        if match:
            slugs.add(match.group(1))
    return slugs


def fetch_live_page(slug: str) -> bytes | None:
    url = f"https://boumax.nl/{slug}/"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            if resp.status != 200:
                return None
            return resp.read()
    except urllib.error.URLError as exc:
        print(f"Kon {url} niet ophalen: {exc}", file=sys.stderr)
        return None


def ensure_images(target_dir: Path, slug: str) -> bool:
    """Zorgt dat target_dir/images/ het volledige gedeelde fotoset bevat.

    Alle demo's hergebruiken dezelfde generieke, merkloze foto's uit
    website-demo-schilders/images/ (zie routine-stap 3) - dat is dus een
    betrouwbare bron om ontbrekende foto's uit terug te zetten, zonder
    afhankelijk te zijn van Netlify's losse file-listing per demo.
    """
    if not TEMPLATE_IMAGES_DIR.is_dir():
        print("Waarschuwing: website-demo-schilders/images/ niet gevonden, kan foto's niet herstellen.", file=sys.stderr)
        return False

    images_dir = target_dir / "images"
    copied_any = False
    for src in sorted(TEMPLATE_IMAGES_DIR.glob("*")):
        if not src.is_file():
            continue
        dst = images_dir / src.name
        if dst.exists():
            continue
        images_dir.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())
        copied_any = True

    if copied_any:
        print(f"  Foto's aangevuld voor: {slug}")
    return copied_any


def main() -> int:
    token = os.environ.get("NETLIFY_AUTH_TOKEN")
    if not token:
        print("NETLIFY_AUTH_TOKEN ontbreekt (repo secret niet ingesteld?).", file=sys.stderr)
        return 1

    live_slugs = get_live_demo_slugs(token)
    print(f"Live demo's op boumax.nl: {len(live_slugs)}")

    changed: list[str] = []
    for slug in sorted(live_slugs):
        target_dir = DEPLOY_DIR / slug
        target_file = target_dir / "index.html"
        html_was_missing = not target_file.exists()

        if html_was_missing:
            print(f"Ontbreekt in repo, ophalen: {slug}")
            content = fetch_live_page(slug)
            if content is None:
                print(f"  Overslaan (kon live pagina niet ophalen): {slug}", file=sys.stderr)
                continue
            target_dir.mkdir(parents=True, exist_ok=True)
            target_file.write_bytes(content)

        # Ook draaien als index.html al bestond: eerdere runs (voor deze
        # fix) zetten soms alleen de HTML terug zonder de bijbehorende
        # foto's - dat moet hier alsnog met terugwerkende kracht hersteld
        # worden, anders blijft zo'n demo voor altijd kapot.
        images_were_added = ensure_images(target_dir, slug)

        if html_was_missing or images_were_added:
            changed.append(slug)

    if changed:
        print(f"Toegevoegd/hersteld: {', '.join(changed)}")
    else:
        print("Niets te synchroniseren, repo is al actueel.")

    # Voor de workflow: laat via een output-bestand weten of er iets veranderd is.
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as fh:
            fh.write(f"changed={'true' if changed else 'false'}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
