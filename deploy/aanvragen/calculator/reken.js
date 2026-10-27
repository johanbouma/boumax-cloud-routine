function bereken(aantal, prijs, winst) {
  const waarden = [aantal, prijs, winst];
  if (waarden.some((waarde) => waarde === '' || waarde === null || waarde === undefined || !Number.isFinite(Number(waarde)))) return null;
  [aantal, prijs, winst] = waarden.map(Number);
  if (aantal <= 0 || prijs < 0 || winst < 0) return null;

  const aanvraagkosten = Math.round((aantal * prijs + Number.EPSILON) * 100) / 100;
  return {
    aanvraagkosten,
    resterendeWinst: Math.round((winst - aanvraagkosten + Number.EPSILON) * 100) / 100,
  };
}

if (typeof module !== 'undefined' && module.exports) module.exports = { bereken };
