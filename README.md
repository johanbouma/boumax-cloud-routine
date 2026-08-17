# boumax-cloud-routine

Bron-repo voor de dagelijkse Boumax-acquisitie cloud-routine (08:05 Europe/Amsterdam).

**Bevat:**
- `deploy/` — exacte huidige staat van de live site boumax.nl (index.html, privacy.html, branding, en per-prospect demo-mappen zoals `demo-sikkens/`). Dit is precies wat elke keer als geheel naar Netlify gaat — nooit alleen de nieuwe demo apart deployen, anders verdwijnt de rest van de live site.
- `website-demo-schilders/` — het generieke, nog niet gepersonaliseerde demo-sjabloon (demo.html + images/) waar een nieuwe prospect-demo op gebaseerd wordt.
- `netlify-deploy/deploy.py` — deployt de hele `deploy/`-map naar boumax.nl via Netlify's API (token via lokale `.env`, nooit gecommit). **Heeft twee modi:**
  - Zonder argumenten: uitgebreide lokale sync met Git (fetch + echte driewegsmerge + push), voor gebruik op de ontwikkelmachine. Importeert `sync_with_github.py`, dat bewust NIET in deze repo staat.
  - **`--cloud`**: slaat die sync over en deployt gewoon de `deploy/`-map zoals die in deze kloon staat. **De dagelijkse cloud-routine gebruikt altijd `--cloud`** — zonder die vlag crasht het script met `ModuleNotFoundError` omdat `sync_with_github.py` hier ontbreekt (dat is opzettelijk: de cloud-sandbox kan toch niet naar deze repo pushen, dus die module heeft daar geen functie).
- `hostinger-drafts/draft_tool.py` — slaat een kant-en-klare mailtekst uitsluitend als concept (IMAP `\Draft`) op in de Hostinger-mailbox. Bevat geen SMTP-code, kan fysiek geen e-mail versturen.
- `.github/workflows/sync-demos.yml` + `scripts/sync_missing_demos.py` — een aparte, dagelijkse GitHub Action (draait op GitHub's eigen infra, niet in de Claude-sandbox) die na de routine automatisch demo-mappen die live staan op Netlify maar nog niet in deze repo staan, terugzet. Dit is de manier waarop nieuwe demo's van de cloud-routine in deze repo terechtkomen — de routine zelf probeert nooit te pushen (dat lukt structureel niet vanuit de Claude-cloud-sandbox, bevestigde bug in Anthropics GitHub-connector).

**Nooit in deze repo:** wachtwoorden, Hostinger-mailwachtwoord, of enig `.env`-bestand. Het Netlify-token en het sheet-webhook-token worden per routine-run apart meegegeven, niet hier opgeslagen.

**Workflow van de dagelijkse routine:** zie de routine-configuratie zelf (via claude.ai/code/routines) voor de volledige instructies. Kort samengevat: kies volgende prospect uit de sheet → personaliseer een nieuwe map onder `deploy/demo-<naam>/` → `python netlify-deploy/deploy.py --cloud` → verifieer live → werk de sheet bij. De nieuwe demo-map komt de volgende ochtend automatisch in deze repo via de aparte GitHub Action hierboven, niet doordat de routine zelf commit/pusht.
