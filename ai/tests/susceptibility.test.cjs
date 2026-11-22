const test = require('node:test'), assert = require('node:assert'); const F = require('../susceptibility/core.js');
const now = Date.parse('2026-11-22T12:00:00Z'), hist = { daily_p99_mm: 40 };
const sim = (p24, t = '2026-11-22T11:00Z') => ({ valid_time: t, p24_mm: p24, p6_mm: 0 });
test('sem chuva = verde', () => assert.strictEqual(F.scoreParish({ sus: { f100: 1 }, terr: {}, basins: [{ sim: sim(0), hist }] }, now).cls.key, 'verde'));
test('chuva P99 + zona APA T20 = vermelho', () => assert.strictEqual(F.scoreParish({ sus: { f20: 1 }, terr: {}, basins: [{ sim: sim(40), hist }] }, now).cls.key, 'vermelho'));
test('dados desatualizados = sem dados', () => assert.strictEqual(F.scoreParish({ sus: { f20: 1 }, terr: {}, basins: [{ sim: sim(40, '2026-11-22T06:00Z'), hist }] }, now).cls.key, 'sem_dados'));
test('monotonia na chuva', () => { const s = p => F.scoreParish({ sus: { f100: 0.5 }, terr: {}, basins: [{ sim: sim(p), hist }] }, now).score; assert.ok(s(5) <= s(20) && s(20) <= s(40)); });
test('modelo marcado não aprendido', () => assert.strictEqual(F.MODEL.learned, false));
