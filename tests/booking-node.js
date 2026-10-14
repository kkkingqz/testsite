#!/usr/bin/env node
// Dependency-free unit tests for the Cal.com integration. No real bookings are made.
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname,'../public/assets/js/booking.js'),'utf8');

function run(eventUrl, opts = {}) {
  const node = () => ({
    hidden: false,
    textContent: '',
    href: '',
    classList: {toggle() {}},
    querySelector() { return null; },
  });
  const elements = {'cal-inline':node(),'booking-status':node(),'booking-open-link':node()};
  elements['booking-open-link'].hidden = true;
  const scripts = [];
  const observers = [];
  const context = {
    window: { KTAWF_BOOKING:{eventUrl,theme:'light',brandColor:'#25382e'}, setTimeout(){} },
    document: {
      getElementById: id => elements[id],
      createElement: type => {
        assert.equal(type,'script');
        return {listeners:{}, addEventListener(name, cb) {this.listeners[name] = cb;}};
      },
      head: {appendChild(script) {scripts.push(script);}},
    },
    MutationObserver: class {constructor(cb){this.cb=cb;observers.push(this);} observe(){} disconnect(){}},
    URL,
  };
  if(opts.color) context.window.KTAWF_BOOKING.brandColor=opts.color;
  vm.runInNewContext(source,context,{timeout:1000});
  return { elements,scripts,observers,Cal: context.window.Cal};
}

let r=run('');
assert.equal(r.scripts.length,0);
assert.match(r.elements['booking-status'].textContent,/не активовано/);
assert.equal(r.elements['booking-open-link'].hidden,true);
console.log('PASS unconfigured: no fabricated calendar and no network loader');

r=run('https://cal.com/test-user/45min');
assert.equal(r.scripts.length,1);
assert.equal(r.scripts[0].src,'https://app.cal.com/embed/embed.js');
assert.equal(r.elements['booking-open-link'].href,'https://cal.com/test-user/45min');
assert.equal(r.elements['booking-open-link'].hidden,false);
assert.deepEqual(Array.from(r.Cal.q,record=>record[0]),['init','inline','ui']);
assert.equal(r.Cal.q[0][1].origin,'https://app.cal.com');
assert.equal(r.Cal.q[1][1].calLink,'test-user/45min');
assert.equal(r.Cal.q[2][1].styles.branding.brandColor,'#25382e');
console.log('PASS global event: correct Cal.com inline commands and fallback URL');

r.scripts[0].listeners.error();
assert.match(r.elements['booking-status'].textContent,/Не вдалося/);
console.log('PASS external script fails: informative fallback status');

r=run('https://cal.eu/test-user/45min');
assert.equal(r.scripts[0].src,'https://app.cal.eu/embed/embed.js');
assert.equal(r.Cal.q[0][1].origin,'https://app.cal.eu');
console.log('PASS EU event: correct Cal.eu embed origin');

for (const invalid of ['https://evil.example/user/45min','http://cal.com/user/45min','https://cal.com/user','https://cal.com/user/<tag>','https://user:pass@cal.com/user/45min']) {
  r=run(invalid);
  assert.equal(r.scripts.length,0);
  assert.equal(r.elements['booking-open-link'].hidden,true);
}
console.log('PASS invalid destinations: blocked without loading scripts');
