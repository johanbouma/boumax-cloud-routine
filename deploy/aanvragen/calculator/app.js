const aantal = document.getElementById('aantal');
const prijs = document.getElementById('prijs');
const winst = document.getElementById('winst');
const resterend = document.getElementById('resterend');
const context = document.getElementById('result-context');
const fout = document.getElementById('input-error');
const euro = new Intl.NumberFormat('nl-NL', { style: 'currency', currency: 'EUR', maximumFractionDigits: 2 });
const bedrag = (waarde) => waarde < 0 ? '− ' + euro.format(Math.abs(waarde)) : euro.format(waarde);

function toon() {
  const invoer = [aantal.value, prijs.value, winst.value];
  const leeg = invoer.some((waarde) => waarde === '');
  const uitkomst = bereken(...invoer);
  fout.hidden = leeg || Boolean(uitkomst);

  if (!uitkomst) {
    resterend.textContent = '€ —';
    document.getElementById('winst-bedrag').textContent = '€ —';
    document.getElementById('kosten-bedrag').textContent = '€ —';
    document.getElementById('totaal-bedrag').textContent = '€ —';
    context.textContent = 'Vul de drie cijfers in om je uitkomst te zien.';
    document.querySelector('.result').classList.remove('negative');
    return;
  }

  const restBedrag = bedrag(uitkomst.resterendeWinst);
  resterend.textContent = restBedrag;
  document.getElementById('winst-bedrag').textContent = euro.format(Number(winst.value));
  document.getElementById('kosten-bedrag').textContent = '− ' + euro.format(uitkomst.aanvraagkosten);
  document.getElementById('totaal-bedrag').textContent = restBedrag;
  document.querySelector('.result').classList.toggle('negative', uitkomst.resterendeWinst < 0);
  context.textContent = uitkomst.resterendeWinst < 0
    ? 'Bij deze cijfers zijn de aanvraagkosten hoger dan de winst op één klant.'
    : uitkomst.resterendeWinst === 0
      ? 'Bij deze cijfers speel je precies quitte op de aanvraagkosten.'
      : 'Per nieuwe klant, na de kosten van de benodigde aanvragen.';
}

[aantal, prijs, winst].forEach((veld) => veld.addEventListener('input', toon));
document.getElementById('reset').addEventListener('click', () => {
  [aantal, prijs, winst].forEach((veld) => { veld.value = ''; });
  toon();
  aantal.focus();
});
toon();
