# boumax-cloud-routine

Bron-repo voor de dagelijkse Boumax-acquisitie cloud-routine (08:05 Europe/Amsterdam).

**Bevat:**
- `deploy/` — exacte huidige staat van de live site boumax.nl (index.html, privacy.html, branding, en per-prospect demo-mappen zoals `demo-sikkens/`). Dit is precies wat elke keer als geheel naar Netlify gaat — nooit alleen de nieuwe demo apart deployen, anders verdwijnt de rest van de live site.
- `website-demo-schilders/` — het generieke, nog niet gepersonaliseerde demo-sjabloon (demo.html + images/) waar een nieuwe prospect-demo op gebaseerd wordt.
- `netlify-deploy/deploy.py` — deployt de hele `deploy/`-map naar boumax.nl via Netlify's API (token via lokale `.env`, nooit gecommit).

**Nooit in deze repo:** wachtwoorden, Hostinger-mailwachtwoord, of enig `.env`-bestand. Het Netlify-token en het sheet-webhook-token worden per routine-run apart meegegeven, niet hier opgeslagen.

**Workflow van de dagelijkse routine:** zie de routine-configuratie zelf (via claude.ai/code/routines) voor de volledige instructies. Kort samengevat: kies volgende prospect uit de sheet → personaliseer een nieuwe map onder `deploy/demo-<naam>/` → deploy → verifieer live → commit de nieuwe demo-map terug naar deze repo (zodat morgen weer met de actuele staat gestart wordt) → werk de sheet bij.
