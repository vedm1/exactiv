/* Contact form (EXW1-ui, PRD-W section 7). The form works without this file: native validation and
   a plain POST. This file adds inline field errors and the minimum fill time token (EXW1).
   It stores nothing in the browser, sets no cookie and calls only this origin (W-G3, G11). */
(function () {
  'use strict';

  var form = document.getElementById('contact-form');
  if (!form || !window.fetch) { return; }

  var FIELDS = ['name', 'email', 'company', 'role', 'topic', 'data_region', 'message'];
  var MIN_FILL_MS = 3500; // the service refuses a token younger than 3 s
  var TOKEN_STALE_MS = 3600000; // the service refuses a token older than 2 h
  var status = document.getElementById('form-status');
  var button = form.querySelector('button[type=submit]');
  var token = '';
  var tokenAt = 0;
  var sending = false;

  form.noValidate = true; // this script shows the errors, in place of the browser bubble

  function control(name) { return form.elements.namedItem(name); }
  function slot(name) { return document.getElementById('f-' + name + '-error'); }
  function text(code) {
    return form.getAttribute('data-msg-' + code.replace(/_/g, '-')) || form.getAttribute('data-msg-failed');
  }
  function say(code) { status.textContent = text(code); status.hidden = false; }

  function clearErrors() {
    FIELDS.forEach(function (name) {
      var el = control(name);
      slot(name).hidden = true;
      slot(name).textContent = '';
      el.removeAttribute('aria-invalid');
      el.closest('.ex-field').classList.remove('ex-field--error');
    });
    status.hidden = true;
    status.textContent = '';
  }

  function showError(name, code) {
    var el = control(name);
    if (!el) { return null; }
    slot(name).textContent = text(code);
    slot(name).hidden = false;
    el.setAttribute('aria-invalid', 'true');
    el.closest('.ex-field').classList.add('ex-field--error');
    return el;
  }

  function length(value) { return Array.from(value.normalize('NFC')).length; }

  // The limits come from the attributes of the fields. The service checks the same limits again.
  function check() {
    var errors = [];
    FIELDS.forEach(function (name) {
      var el = control(name);
      var value = el.value.trim();
      if (!value) {
        if (el.required) { errors.push([name, 'required']); }
        return;
      }
      var n = length(value);
      if (el.minLength > 0 && n < el.minLength) { errors.push([name, 'too_short']); }
      else if (el.maxLength > 0 && n > el.maxLength) { errors.push([name, 'too_long']); }
      else if (name === 'email' && !/^[^\s@]+@[^\s@]+$/.test(value)) { errors.push([name, 'invalid_email']); }
    });
    return errors;
  }

  function showAll(errors) {
    var first = null;
    errors.forEach(function (pair) {
      var el = showError(pair[0], pair[1]);
      if (el && !first) { first = el; }
    });
    say('fix');
    if (first) { first.focus(); }
  }

  function loadToken() {
    return fetch('/form-token', { cache: 'no-store' })
      .then(function (r) { return r.json(); })
      .then(function (d) { token = d.token || ''; tokenAt = Date.now(); form.elements.namedItem('form_token').value = token; })
      .catch(function () { token = ''; }); // no token: the service applies its stricter limit
  }

  function done() { sending = false; button.disabled = false; }

  function fallback() { // let the browser send the form itself
    HTMLFormElement.prototype.submit.call(form);
  }

  function payload() {
    var body = {};
    FIELDS.concat(['website', 'form_token']).forEach(function (name) { body[name] = control(name).value; });
    return body;
  }

  function send() {
    sending = true;
    button.disabled = true;
    var fresh = !tokenAt || Date.now() - tokenAt > TOKEN_STALE_MS ? loadToken() : Promise.resolve();
    fresh.then(function () {
      var wait = tokenAt ? Math.max(0, tokenAt + MIN_FILL_MS - Date.now()) : 0;
      setTimeout(post, wait);
    });
  }

  function post() {
    fetch('/enquiries', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify(payload())
    }).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (data) { return { status: r.status, data: data }; });
    }).then(function (res) {
      if (res.status === 201) { window.location.assign('/contact/thanks/'); return; }
      if (res.status === 422 && Array.isArray(res.data.errors)) {
        showAll(res.data.errors.map(function (e) { return [e.field, e.code]; }));
        done();
        return;
      }
      if (res.status === 429) { say('rate_limited'); done(); return; }
      fallback();
    }).catch(fallback);
  }

  form.addEventListener('submit', function (event) {
    event.preventDefault();
    if (sending) { return; }
    clearErrors();
    var errors = check();
    if (errors.length) { showAll(errors); return; }
    send();
  });

  loadToken();
}());
