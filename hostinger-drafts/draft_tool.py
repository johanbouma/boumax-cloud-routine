"""
Hostinger Draft Tool - slaat een door jou aangeleverd antwoord uitsluitend
op als concept (\\Draft) in je eigen Hostinger/Titan-mailbox.

Verzendt NOOIT e-mail. Gebruikt geen SMTP. Alleen IMAP: inloggen, de
Drafts/Concepten-map vinden, het concept opslaan, en controleren dat het
er echt staat.

In DRY_RUN-modus (standaard) wordt er GEEN verbinding met de mailbox
gemaakt - het script laat alleen zien welk bericht zou worden opgeslagen.
Zet DRY_RUN pas op false in je eigen .env-bestand als je dat zelf wilt.
"""

from __future__ import annotations

import argparse
import html
import imaplib
import os
import re
import sys
import time
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
ENV_PATH = PROJECT_DIR / ".env"


# ---------------------------------------------------------------------------
# .env inlezen (bewust zonder externe library, zodat er niets geinstalleerd
# hoeft te worden - alleen Python's eigen standaardbibliotheek).
# ---------------------------------------------------------------------------
def load_env(path: Path) -> dict:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        values[key] = value
    return values


def get_config() -> dict:
    env = {**load_env(ENV_PATH)}
    # Omgevingsvariabelen (bijv. gezet met `setx`) hebben voorrang op .env,
    # zodat je nooit gedwongen bent geheimen in een bestand te zetten.
    for key in (
        "MAIL_IMAP_HOST",
        "MAIL_IMAP_PORT",
        "MAIL_USERNAME",
        "MAIL_PASSWORD",
        "DRY_RUN",
        "MAIL_DRAFTS_FOLDER_OVERRIDE",
    ):
        if os.environ.get(key):
            env[key] = os.environ[key]

    env.setdefault("MAIL_IMAP_HOST", "imap.hostinger.com")
    env.setdefault("MAIL_IMAP_PORT", "993")
    env.setdefault("DRY_RUN", "true")
    return env


def is_dry_run(config: dict) -> bool:
    return config.get("DRY_RUN", "true").strip().lower() not in ("false", "0", "no")


# ---------------------------------------------------------------------------
# Bericht opbouwen
# ---------------------------------------------------------------------------
_URL_RE = re.compile(r"(https?://[^\s<>\"]+)")


def linkify_html(body: str) -> str:
    """Zet platte tekst om in eenvoudige HTML met klikbare links, zodat
    URL's in de conceptmail niet als losse tekst blijven staan."""
    escaped = html.escape(body)

    def _wrap(match: re.Match) -> str:
        url = match.group(1)
        trailing = ""
        while url and url[-1] in ".,;:!?)":
            trailing = url[-1] + trailing
            url = url[:-1]
        return f'<a href="{url}">{url}</a>{trailing}'

    linked = _URL_RE.sub(_wrap, escaped)
    paragraphs = [p for p in linked.split("\n\n") if p.strip()]
    html_body = "".join(f"<p>{p.replace(chr(10), '<br>')}</p>" for p in paragraphs)
    return (
        "<!doctype html><html><body style=\"font-family:sans-serif;"
        "font-size:14px;line-height:1.5;color:#111111;\">"
        f"{html_body}</body></html>"
    )


def build_message(from_addr: str, to_addr: str, subject: str, body: str) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    domain = from_addr.split("@")[-1] if "@" in from_addr else "boumax.nl"
    msg["Message-ID"] = make_msgid(domain=domain)
    msg.set_content(body)
    msg.add_alternative(linkify_html(body), subtype="html")
    return msg


# ---------------------------------------------------------------------------
# IMAP-hulpfuncties
# ---------------------------------------------------------------------------
_LIST_LINE_RE = re.compile(r'^\((?P<flags>[^)]*)\)\s+"(?P<delim>[^"]*)"\s+(?P<name>.+)$')


def _parse_list_line(raw: bytes) -> tuple[list[str], str, str]:
    text = raw.decode("utf-8", errors="replace")
    match = _LIST_LINE_RE.match(text)
    if not match:
        return [], ".", text.strip()
    flags = match.group("flags").split()
    delim = match.group("delim")
    name = match.group("name").strip()
    if name.startswith('"') and name.endswith('"'):
        name = name[1:-1]
    return flags, delim, name


def find_drafts_folder(conn: imaplib.IMAP4_SSL) -> str:
    """Zoekt de Drafts/Concepten-map: eerst via de IMAP special-use flag
    \\Drafts (RFC 6154), anders op naam ("Drafts", "Concepten", ...)."""
    typ, data = conn.list()
    if typ != "OK" or not data:
        raise RuntimeError("Kon mappenlijst niet ophalen via IMAP LIST.")

    candidates: list[str] = []
    for raw in data:
        if raw is None:
            continue
        flags, _delim, name = _parse_list_line(raw)
        if any(f.lower() == r"\drafts" for f in flags):
            return name
        lowered = name.lower()
        if "draft" in lowered or "concept" in lowered:
            candidates.append(name)

    if not candidates:
        raise RuntimeError(
            "Geen Drafts/Concepten-map gevonden. Controleer de mapnaam in "
            "hPanel en zet 'm eventueel handmatig in .env als "
            "MAIL_DRAFTS_FOLDER_OVERRIDE."
        )

    # Kortste/meest voor de hand liggende naam eerst (bijv. "Drafts" boven
    # "INBOX.Oud.Drafts-archief").
    candidates.sort(key=len)
    return candidates[0]


def _quoted_folder(folder: str) -> str:
    if folder.startswith('"') and folder.endswith('"'):
        return folder
    if any(ch in folder for ch in " ()\"{}"):
        escaped = folder.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return folder


def append_draft(conn: imaplib.IMAP4_SSL, folder: str, msg: EmailMessage) -> None:
    typ, resp = conn.append(
        _quoted_folder(folder),
        r"(\Draft)",
        imaplib.Time2Internaldate(time.time()),
        msg.as_bytes(),
    )
    if typ != "OK":
        raise RuntimeError(f"IMAP APPEND is mislukt (server zei: {typ}).")


def verify_draft(conn: imaplib.IMAP4_SSL, folder: str, message_id: str) -> bool:
    typ, _ = conn.select(_quoted_folder(folder))
    if typ != "OK":
        raise RuntimeError(f"Kon map '{folder}' niet openen om te controleren.")
    typ, data = conn.search(None, "HEADER", "Message-ID", f'"{message_id}"')
    if typ != "OK":
        raise RuntimeError("IMAP SEARCH tijdens de controle is mislukt.")
    ids = data[0].split() if data and data[0] else []
    return len(ids) > 0


# ---------------------------------------------------------------------------
# Invoer ophalen
# ---------------------------------------------------------------------------
def read_multiline_body() -> str:
    print("Typ de antwoordtekst. Sluit af met een regel die alleen 'END' bevat:")
    lines: list[str] = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "END":
            break
        lines.append(line)
    return "\n".join(lines)


def gather_inputs(args: argparse.Namespace) -> tuple[str, str, str]:
    to_addr = args.to or input("Ontvanger (e-mailadres): ").strip()
    subject = args.subject or input("Onderwerp: ").strip()
    if args.body_file:
        body = Path(args.body_file).read_text(encoding="utf-8")
    else:
        body = read_multiline_body()
    return to_addr, subject, body


# ---------------------------------------------------------------------------
# Hoofdprogramma
# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--to", help="Ontvanger e-mailadres (anders wordt erom gevraagd)")
    parser.add_argument("--subject", help="Onderwerp (anders wordt erom gevraagd)")
    parser.add_argument(
        "--body-file",
        help="Pad naar een .txt-bestand met de antwoordtekst (anders interactief invoeren)",
    )
    args = parser.parse_args()

    config = get_config()
    dry_run = is_dry_run(config)

    to_addr, subject, body = gather_inputs(args)
    if not to_addr or not subject or not body.strip():
        print("Ontvanger, onderwerp en berichttekst mogen niet leeg zijn.", file=sys.stderr)
        return 1

    from_addr = config.get("MAIL_USERNAME") or "voorbeeld@boumax.nl"
    msg = build_message(from_addr, to_addr, subject, body)

    if dry_run:
        print("\n=== DRY RUN - er wordt NIETS opgeslagen in de mailbox ===")
        print(f"Van:        {from_addr}")
        print(f"Aan:        {to_addr}")
        print(f"Onderwerp:  {subject}")
        print(f"Message-ID: {msg['Message-ID']}")
        print("Inhoud:")
        print("-" * 60)
        print(body)
        print("-" * 60)
        if _URL_RE.search(body):
            print("(Er wordt ook een HTML-versie meegestuurd met dit als klikbare link.)")
        print(
            "\nDit is een simulatie. Zet DRY_RUN=false in je eigen .env "
            "pas nadat je dit resultaat hebt gecontroleerd."
        )
        return 0

    username = config.get("MAIL_USERNAME")
    password = config.get("MAIL_PASSWORD")
    host = config.get("MAIL_IMAP_HOST")
    port = int(config.get("MAIL_IMAP_PORT", "993"))

    if not username or not password:
        print(
            "MAIL_USERNAME en/of MAIL_PASSWORD ontbreken in .env. "
            "Vul ze aan (zie .env.example) voordat je DRY_RUN=false gebruikt.",
            file=sys.stderr,
        )
        return 1

    print(f"\nVerbinden met {host}:{port} als {username} ...")
    try:
        conn = imaplib.IMAP4_SSL(host, port)
        conn.login(username, password)
    except Exception:
        # Bewust geen exception-tekst printen: die kan servergegevens
        # bevatten. Het wachtwoord komt hier nooit in terecht.
        print(
            "Kon niet inloggen op de mailbox. Controleer host, poort, "
            "gebruikersnaam en wachtwoord in .env.",
            file=sys.stderr,
        )
        return 1

    try:
        folder_override = config.get("MAIL_DRAFTS_FOLDER_OVERRIDE")
        folder = folder_override or find_drafts_folder(conn)
        print(f"Concepten-map gevonden: {folder}")

        append_draft(conn, folder, msg)
        print("Concept opgeslagen. Controleren of het echt in de map staat ...")

        ok = verify_draft(conn, folder, msg["Message-ID"])
        if ok:
            print(f"Bevestigd: het concept staat in '{folder}'. Niets is verzonden.")
        else:
            print(
                "Waarschuwing: het concept kon na opslaan niet worden "
                "teruggevonden. Controleer handmatig in je mailbox.",
                file=sys.stderr,
            )
            return 1
    except Exception as exc:
        print(f"Er ging iets mis: {exc}", file=sys.stderr)
        return 1
    finally:
        try:
            conn.logout()
        except Exception:
            pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
