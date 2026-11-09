#!/usr/bin/env node
// Grava audio/rota-xy.json com a posição na tela de cada contato, para o panorama do som seguir a bola.
import { chromium, syncCampaign, filmURL } from './pw.mjs';
import { writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
const html = resolve('index.html');
syncCampaign(html);
const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
await p.goto(filmURL(html));
await p.evaluate(async () => { await window.ready; });
const xy = await p.evaluate(() => window.ROTA_XY);
await b.close();
writeFileSync('audio/rota-xy.json', JSON.stringify(xy));
console.log(xy.length, 'contatos em audio/rota-xy.json');
