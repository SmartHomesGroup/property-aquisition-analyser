#!/usr/bin/env node
// Headless screenshot of a page via the Chrome DevTools Protocol. No npm dependencies.
//
//   node tools/shot.mjs <url> <out.png> [--width 1280] [--height 800] [--dark] [--wait 3000]
//                        [--click "css"] [--type "css=text"] [--hover "css"]
//
// Prints console errors and uncaught exceptions from the page, which makes it a cheap smoke test.
// Needs `chromium` on PATH (snap chromium works).

import { spawn } from 'node:child_process';
import { writeFileSync, mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const args = process.argv.slice(2);
const positional = args.filter((a, i) => !a.startsWith('--') && !(args[i - 1]?.startsWith('--') && !['--dark'].includes(args[i - 1])));
const opt = (name, def) => {
	const i = args.indexOf(name);
	return i >= 0 ? args[i + 1] : def;
};
const [url, out] = positional;
if (!url || !out) {
	console.error('usage: shot.mjs <url> <out.png> [--width N] [--height N] [--dark] [--wait ms] [--click css] [--type css=text] [--hover css]');
	process.exit(2);
}
const width = +opt('--width', 1280);
const height = +opt('--height', 800);
const dark = args.includes('--dark');
const wait = +opt('--wait', 3000);

const port = 9222 + Math.floor(Math.random() * 500);
const profile = mkdtempSync(join(process.env.SNAP_USER_COMMON ?? process.env.HOME + '/snap/chromium/common', 'shot-'));
const chrome = spawn(
	'chromium',
	['--headless=new', '--disable-gpu', '--no-first-run', `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`, `--window-size=${width},${height}`, 'about:blank'],
	{ stdio: 'ignore' }
);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

let target;
for (let i = 0; i < 60 && !target; i++) {
	await sleep(250);
	try {
		target = (await (await fetch(`http://127.0.0.1:${port}/json`)).json()).find((t) => t.type === 'page');
	} catch {
		/* not up yet */
	}
}
if (!target) {
	chrome.kill();
	throw new Error('chromium did not start');
}

const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((r) => (ws.onopen = r));
let id = 0;
const pending = new Map();
const problems = [];
ws.onmessage = (m) => {
	const msg = JSON.parse(m.data);
	if (msg.id && pending.has(msg.id)) pending.get(msg.id)(msg.result ?? msg.error);
	if (msg.method === 'Runtime.exceptionThrown') problems.push('exception: ' + msg.params.exceptionDetails.text + ' ' + (msg.params.exceptionDetails.exception?.description ?? ''));
	if (msg.method === 'Runtime.consoleAPICalled' && ['error', 'warning'].includes(msg.params.type))
		problems.push(msg.params.type + ': ' + msg.params.args.map((a) => a.value ?? a.description ?? '').join(' '));
};
const send = (method, params = {}) => new Promise((r) => { pending.set(++id, r); ws.send(JSON.stringify({ id, method, params })); });

await send('Runtime.enable');
await send('Page.enable');
await send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-color-scheme', value: dark ? 'dark' : 'light' }] });
await send('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: 1, mobile: width < 600 });
await send('Page.navigate', { url });
await sleep(wait);

const centre = async (sel) => {
	const r = await send('Runtime.evaluate', { expression: `(() => { const el = document.querySelector(${JSON.stringify(sel)}); if (!el) return null; const b = el.getBoundingClientRect(); return { x: b.x + b.width / 2, y: b.y + b.height / 2 }; })()`, returnByValue: true });
	if (!r.result?.value) throw new Error('no element for ' + sel);
	return r.result.value;
};
const typeArg = opt('--type');
if (typeArg) {
	const [sel, text] = typeArg.split('=');
	const c = await centre(sel);
	await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: c.x, y: c.y, button: 'left', clickCount: 1 });
	await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: c.x, y: c.y, button: 'left', clickCount: 1 });
	await send('Input.insertText', { text });
	await send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13 });
	await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13 });
	await sleep(wait);
}
const click = opt('--click');
if (click) {
	const c = await centre(click);
	await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: c.x, y: c.y, button: 'left', clickCount: 1 });
	await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: c.x, y: c.y, button: 'left', clickCount: 1 });
	await sleep(wait);
}
const hover = opt('--hover');
if (hover) {
	const c = await centre(hover);
	await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: c.x, y: c.y });
	await sleep(600);
}

const shot = await send('Page.captureScreenshot', { format: 'png' });
writeFileSync(out, Buffer.from(shot.data, 'base64'));
console.log(out);
if (problems.length) console.log(problems.join('\n'));
else console.log('no console errors');
ws.close();
chrome.kill();
process.exit(0);
