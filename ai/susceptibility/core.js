/* Floods AI — suscetibilidade em tempo real (v0: regras declaradas, NÃO aprendido).
   EXPERIMENTAL — NÃO OPERACIONAL. Não é probabilidade, nem aviso, nem previsão de inundação.
   score = dinâmica(chuva observada vs. climatologia ERA5 da bacia) × (0,3 + 0,7 × estática da freguesia)
   O módulo aceita pesos aprendidos (weights) quando existir um modelo validado; hoje weights = null. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(); else root.FloodsSusc = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  const MODEL = { id: 'rules-v0', learned: false, status: 'EXPERIMENTAL — NÃO OPERACIONAL' };
  const CLASSES = [
    { key: 'verde', label: 'Verde · baixa', color: '#2f9e44', max: 0.25 },
    { key: 'amarelo', label: 'Amarelo · moderada', color: '#f2c200', max: 0.5 },
    { key: 'laranja', label: 'Laranja · elevada', color: '#f08c00', max: 0.75 },
    { key: 'vermelho', label: 'Vermelho · muito elevada', color: '#e03131', max: Infinity }
  ];
  const NODATA = { key: 'sem_dados', label: 'Sem dados / desatualizado', color: '#adb5bd' };
  const MAX_AGE_H = 3;
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));

  function classify(score) { return score == null ? NODATA : CLASSES.find(c => score < c.max); }

  // estática da freguesia: fracções APA T20/T100/T1000, proximidade de rios, HAND<5 m
  function staticScore(sus, terr) {
    if (!sus && !terr) return null;
    const s = sus || {}, t = terr || {};
    return clamp(Math.max(
      (s.f20 || 0) * 1.0, (s.f100 || 0) * 0.7, (s.f1000 || 0) * 0.4,
      (s.river300 || 0) * 0.5, (t.hand_lt5_frac || 0) * 0.5));
  }

  // dinâmica da bacia: chuva observada/estimada em 24 h vs. P99 diário ERA5 (10 anos) da própria bacia
  function dynamicScore(sim, hist, now) {
    if (!sim || !hist || !hist.daily_p99_mm) return { dyn: null, reason: 'sem simulação ou climatologia' };
    const ageH = (now - Date.parse(sim.valid_time || sim.observed_at)) / 36e5;
    if (!(ageH <= MAX_AGE_H)) return { dyn: null, reason: 'dados com mais de ' + MAX_AGE_H + ' h' };
    const r24 = (sim.p24_mm ?? 0) / hist.daily_p99_mm;
    const r6 = (sim.p6_mm ?? 0) / (0.6 * hist.daily_p99_mm);
    return { dyn: clamp(Math.max(r24, r6)), ageH, modelled: !!sim.modelled_rainfall, p24: sim.p24_mm, p99: hist.daily_p99_mm };
  }

  function scoreParish({ sus, terr, basins }, now, weights = null) {
    const st = staticScore(sus, terr);
    const dyns = (basins || []).map(b => dynamicScore(b.sim, b.hist, now)).filter(d => d.dyn != null);
    if (st == null || !dyns.length) return { score: null, cls: NODATA, static: st, dynamic: null };
    const dyn = Math.max(...dyns.map(d => d.dyn));
    const w = weights || { base: 0.3, static: 0.7 };
    const score = clamp(dyn * (w.base + w.static * st));
    return { score, cls: classify(score), static: st, dynamic: dyn, modelled: dyns.some(d => d.modelled) };
  }

  return { MODEL, CLASSES, NODATA, MAX_AGE_H, classify, staticScore, dynamicScore, scoreParish };
});
