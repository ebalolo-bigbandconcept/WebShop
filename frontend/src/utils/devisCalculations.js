const LOCATION_SCENARIOS = new Set([
  "location_with_apport",
  "location_without_apport",
]);

export const isLocationScenario = (scenario) => LOCATION_SCENARIOS.has(scenario);

export const getDefaultVatRate = (isRenovation, scenario) => {
  if (isLocationScenario(scenario)) return 0.20;
  if (!scenario || scenario === "direct") return isRenovation ? 0.10 : 0.20;
  return 0.20;
};

export const computeLineTotals = (unitPrice, qty, taux) => {
  const montant_HT = (unitPrice * qty).toFixed(2);
  const montant_TVA = (unitPrice * taux * qty).toFixed(2);
  const montant_TTC = (unitPrice * (1 + taux) * qty).toFixed(2);
  return { montant_HT, montant_TVA, montant_TTC };
};

export const getUnitPriceForScenario = (article, scenario) => {
  if (isLocationScenario(scenario)) {
    if (article?.location_price !== null && article?.location_price !== undefined) {
      return parseFloat(article.location_price) || 0;
    }
  }
  return parseFloat(article?.prix_vente_HT) || 0;
};

export const getEffectiveUnitPriceForScenario = (
  article,
  scenario,
  locationTime = 1,
) => {
  const basePrice = getUnitPriceForScenario(article, scenario);
  if (!isLocationScenario(scenario)) return basePrice;
  const duration = Math.max(parseInt(locationTime, 10) || 1, 1);
  return basePrice * duration;
};

export const buildArticleLine = (article, qty, taux, scenario, locationTime = 1) => {
  const unit_price = getEffectiveUnitPriceForScenario(
    article,
    scenario,
    locationTime,
  );
  const quantity = parseFloat(qty) || 0;
  const totals = computeLineTotals(unit_price, quantity, taux);

  return {
    ...article,
    quantite: qty,
    taux_tva: { ...article.taux_tva, taux },
    ...totals,
  };
};

export const recalcArticleLine = (
  article,
  taux,
  scenario,
  locationTime = 1,
) => {
  const unit_price = getEffectiveUnitPriceForScenario(
    article,
    scenario,
    locationTime,
  );
  const quantity = parseFloat(article.quantite) || 0;
  const totals = computeLineTotals(unit_price, quantity, taux);

  return {
    ...article,
    taux_tva: { ...article.taux_tva, taux },
    ...totals,
  };
};
