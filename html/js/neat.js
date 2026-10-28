/* N.E.A.T Microcredit — shared behaviour. No dependencies.
   Sections: header/nav · site search · reveal · counters · calculator · forms */
(function () {
  'use strict';
  var $ = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };
  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var desktop = window.matchMedia('(min-width: 1040px)');

  /* ---------- Header: scrolled state ---------- */
  var header = $('.site-header');
  if (header) {
    var onScroll = function () { header.classList.toggle('is-scrolled', window.scrollY > 8); };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  /* ---------- Navigation: mobile drawer + product submenu ---------- */
  var nav = $('#site-nav'), toggle = $('#nav-toggle'), backdrop = $('.nav-backdrop');
  function setNav(open) {
    if (!nav || !toggle) return;
    nav.classList.toggle('is-open', open);
    if (backdrop) backdrop.classList.toggle('is-open', open);
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    document.body.classList.toggle('nav-open', open);
    if (open) { var first = $('a, button', nav); if (first && !desktop.matches) first.focus({ preventScroll: true }); }
  }
  if (toggle && nav) {
    toggle.addEventListener('click', function () { setNav(toggle.getAttribute('aria-expanded') !== 'true'); });
    if (backdrop) backdrop.addEventListener('click', function () { setNav(false); toggle.focus(); });
    // selecting any link closes the drawer
    $$('a', nav).forEach(function (a) { a.addEventListener('click', function () { setNav(false); }); });
    desktop.addEventListener && desktop.addEventListener('change', function () { setNav(false); closeSubs(); });
    // keep keyboard focus inside the open drawer on mobile
    nav.addEventListener('keydown', function (e) {
      if (e.key !== 'Tab' || desktop.matches || !nav.classList.contains('is-open')) return;
      var f = $$('a[href], button', nav).filter(function (el) { return el.offsetParent !== null; });
      var all = [toggle].concat(f);
      var i = all.indexOf(document.activeElement);
      if (e.shiftKey && i <= 0) { e.preventDefault(); all[all.length - 1].focus(); }
      else if (!e.shiftKey && i === all.length - 1) { e.preventDefault(); all[0].focus(); }
    });
  }
  function closeSubs(except) {
    $$('.nav__trigger').forEach(function (t) {
      if (t === except) return;
      t.setAttribute('aria-expanded', 'false');
      var p = document.getElementById(t.getAttribute('aria-controls'));
      if (p) p.classList.remove('is-open');
    });
  }
  $$('.nav__trigger').forEach(function (t) {
    t.addEventListener('click', function () {
      var open = t.getAttribute('aria-expanded') !== 'true';
      closeSubs(t);
      t.setAttribute('aria-expanded', String(open));
      var p = document.getElementById(t.getAttribute('aria-controls'));
      if (p) p.classList.toggle('is-open', open);
    });
  });
  document.addEventListener('click', function (e) {
    if (desktop.matches && !e.target.closest('.has-sub')) closeSubs();
  });
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    if (nav && nav.classList.contains('is-open')) { setNav(false); if (toggle) toggle.focus(); }
    var openTrig = $('.nav__trigger[aria-expanded="true"]');
    if (openTrig && desktop.matches) { closeSubs(); openTrig.focus(); }
  });

  /* ---------- Site search (uses a native <dialog>) ---------- */
  var dlg = $('#search-dialog');
  if (dlg) {
    var INDEX = [
      ['Home', 'index.html', 'Homepage overview', 'home landing main'],
      ['About Us', 'about.html', 'Our story, mission, vision, board and team', 'about company mission vision history board team values'],
      ['N.E.A.T Products', 'products.html', 'Overview of all our financial products', 'products fund loan finance'],
      ['Micro Fund', 'microFund.html', 'Quick fund for urgent financing needs', 'micro fund funding quick loan calculator'],
      ['S.M.E Fund', 'sme.html', 'Funding to grow and expand your business', 'sme small medium enterprise fund loan requirements'],
      ['Asset Fund', 'assetFund.html', 'Financial support to own business assets', 'asset fund equipment finance'],
      ['Savings', 'saving.html', 'Savings, current and fixed deposit accounts', 'savings save account deposit open account'],
      ['Business Advisory', 'advisory.html', 'Business advisory and capacity building', 'advisory consulting business support training'],
      ['Equity Investment', 'equity.html', 'Risk capital through equity investment', 'equity investment shares invest'],
      ['Term Deposit', 'termDeposit.html', 'Fixed-term deposits with a rate for your chosen term', 'term deposit fixed interest rate'],
      ['Get a Loan', 'get.html', 'Expression of interest — choose a branch', 'loan borrow credit apply funding expression interest'],
      ['Investment Form', 'investment.html', 'Tell us how much you would like to invest', 'invest investment form'],
      ['FAQs', 'faqs.html', 'Answers to common questions', 'faq questions help account requirements'],
      ['Career', 'career.html', 'Careers and applications at N.E.A.T', 'career jobs vacancy hiring work apply'],
      ['Contact Us', 'contact.html', 'Head office, branches and message form', 'contact reach phone email address location find us branches help'],
      ['Privacy Policy', 'privacyPolicy.html', 'How we handle personal data', 'privacy data policy'],
      ['Terms of Service', 'termsOfService.html', 'Terms for using our services', 'terms service legal'],
      ['Disclaimer', 'disclaimer.html', 'Website disclaimer', 'disclaimer legal copyright'],
      ['Email Login', 'https://webmail.neatmicrocredit.com.ng/', 'Staff webmail', 'email login webmail staff']
    ];
    var input = $('#search-input'), list = $('#search-results');
    var render = function () {
      var q = input.value.trim().toLowerCase();
      list.innerHTML = '';
      var hits = INDEX.filter(function (r) { return !q || (r[0] + ' ' + r[2] + ' ' + r[3]).toLowerCase().indexOf(q) > -1; });
      if (!hits.length) { var li = document.createElement('li'); li.className = 'search-empty'; li.textContent = 'No matches. Try a different word.'; list.appendChild(li); return; }
      hits.forEach(function (r, i) {
        var li = document.createElement('li'), a = document.createElement('a');
        a.href = r[1]; if (i === 0) a.className = 'is-active';
        var s = document.createElement('strong'); s.textContent = r[0];
        var d = document.createElement('span'); d.textContent = r[2];
        a.appendChild(s); a.appendChild(d); li.appendChild(a); list.appendChild(li);
      });
    };
    $$('[data-open-search]').forEach(function (b) {
      b.addEventListener('click', function () { setNav(false); if (dlg.showModal) dlg.showModal(); else dlg.setAttribute('open', ''); input.value = ''; render(); input.focus(); });
    });
    $$('[data-close-search]').forEach(function (b) { b.addEventListener('click', function () { dlg.close(); }); });
    dlg.addEventListener('click', function (e) { if (e.target === dlg) dlg.close(); });
    input.addEventListener('input', render);
    input.addEventListener('keydown', function (e) {
      var links = $$('a', list), cur = links.indexOf($('a.is-active', list));
      if (e.key === 'Enter') { e.preventDefault(); if (links[Math.max(cur, 0)]) location.href = links[Math.max(cur, 0)].href; }
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        e.preventDefault(); if (!links.length) return;
        var n = (cur + (e.key === 'ArrowDown' ? 1 : -1) + links.length) % links.length;
        links.forEach(function (l) { l.classList.remove('is-active'); }); links[n].classList.add('is-active'); links[n].scrollIntoView({ block: 'nearest' });
      }
    });
  }

  /* ---------- Reveal on scroll ---------- */
  var reveals = $$('.reveal');
  if (reveals.length) {
    if (!('IntersectionObserver' in window) || reduceMotion) { reveals.forEach(function (el) { el.classList.add('is-visible'); }); }
    else {
      var io = new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('is-visible'); io.unobserve(e.target); } }); }, { threshold: .12, rootMargin: '0px 0px -6% 0px' });
      reveals.forEach(function (el) { io.observe(el); });
    }
  }

  /* ---------- Counters (run once, on entering the viewport) ---------- */
  var fmt = new Intl.NumberFormat('en-NG');
  $$('[data-count]').forEach(function (el) {
    var target = parseFloat(el.getAttribute('data-count')), pre = el.getAttribute('data-prefix') || '', suf = el.getAttribute('data-suffix') || '';
    var final = pre + fmt.format(target) + suf; el.textContent = final;           // readable without animation
    if (reduceMotion || !('IntersectionObserver' in window)) return;
    var done = false;
    new IntersectionObserver(function (es, obs) {
      es.forEach(function (e) {
        if (!e.isIntersecting || done) return; done = true; obs.disconnect();
        var t0 = null, dur = 1400;
        var step = function (t) {
          if (t0 === null) t0 = t; var p = Math.min((t - t0) / dur, 1), eased = 1 - Math.pow(1 - p, 3);
          el.textContent = pre + fmt.format(Math.round(target * eased)) + suf;
          if (p < 1) requestAnimationFrame(step); else el.textContent = final;
        };
        el.textContent = pre + '0' + suf; requestAnimationFrame(step);
      });
    }, { threshold: .4 }).observe(el);
  });

  /* ---------- Funding calculator ----------
     Rule preserved from the previous site: total = amount + 30% of amount,
     weekly repayment = total ÷ number of weeks (rounded to the nearest naira).
     This is an ESTIMATE and not an offer. Rate/limits come from data-* attributes. */
  function naira(n) { return '\u20A6' + fmt.format(Math.round(n)); }
  $$('[data-calc]').forEach(function (root) {
    var amt = $('[data-amount]', root), wk = $('[data-weeks]', root);
    var rate = parseFloat(root.getAttribute('data-rate')) || 30;
    var outAmt = $('[data-out-amount]', root), outWk = $('[data-out-weeks]', root), outPay = $('[data-out-weekly]', root), outTot = $('[data-out-total]', root);
    function clampInput(el) {
      var min = parseFloat(el.min), max = parseFloat(el.max), v = parseFloat(el.value);
      if (isNaN(v)) v = min; v = Math.min(Math.max(v, min), max); el.value = v; return v;
    }
    function paint(el) { var p = (el.value - el.min) / (el.max - el.min) * 100; el.style.setProperty('--fill', p + '%'); }
    function update() {
      var a = clampInput(amt), w = clampInput(wk);
      var total = a + a * (rate / 100), weekly = total / w;
      outAmt.textContent = naira(a); outWk.textContent = w + (w === 1 ? ' week' : ' weeks');
      outPay.textContent = naira(weekly); outTot.textContent = naira(total);
      amt.setAttribute('aria-valuetext', naira(a)); wk.setAttribute('aria-valuetext', w + (w === 1 ? ' week' : ' weeks'));
      paint(amt); paint(wk);
    }
    amt.addEventListener('input', update); wk.addEventListener('input', update); update();
  });

  /* ---------- Forms ----------
     None of the original forms had a backend. Rather than pretend to submit, these
     open the visitor's email app with their answers filled in (to a real NEAT address).
     When a real endpoint exists, replace this block with a fetch() to it. */
  $$('form[data-mailto]').forEach(function (form) {
    var status = $('.form-status', form.parentNode) || $('.form-status', form);
    form.setAttribute('novalidate', '');
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      if (!form.checkValidity()) { form.reportValidity(); var bad = $(':invalid', form); if (bad) bad.focus(); return; }
      var lines = [], seen = {};
      $$('input, select, textarea', form).forEach(function (el) {
        if (!el.name || el.type === 'file' || el.type === 'submit' || el.type === 'button') return;
        var label = el.getAttribute('data-label') || el.name, val;
        if (el.type === 'checkbox' || el.type === 'radio') {
          if (!el.checked) return; val = el.value && el.value !== 'on' ? el.value : 'Yes';
          if (seen[el.name]) { seen[el.name].val += ', ' + val; return; }
          seen[el.name] = { label: label, val: val, i: lines.length }; lines.push(seen[el.name]); return;
        }
        val = (el.value || '').trim(); if (!val) return; lines.push({ label: label, val: val });
      });
      var body = lines.map(function (l) { return l.label + ': ' + l.val; }).join('\n');
      var to = form.getAttribute('data-to'), subject = form.getAttribute('data-subject') || 'Website enquiry';
      window.location.href = 'mailto:' + to + '?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);
      if (status) {
        status.hidden = false;
        status.innerHTML = '';
        var p = document.createElement('p'); p.style.margin = 0;
        p.textContent = 'Your email app should open with your details filled in. Press Send there to submit \u2014 nothing is sent until you do. ' + (form.getAttribute('data-note') || '') + ' If nothing opens, email us directly at ';
        var a = document.createElement('a'); a.href = 'mailto:' + to; a.textContent = to; p.appendChild(a); p.appendChild(document.createTextNode('.'));
        status.appendChild(p); status.setAttribute('tabindex', '-1'); status.focus();
      }
    });
  });

  /* CV file name feedback (career form) */
  var cv = $('#cv-file'), cvName = $('#cv-name');
  if (cv && cvName) cv.addEventListener('change', function () { cvName.textContent = cv.files && cv.files[0] ? 'Selected: ' + cv.files[0].name + ' (attach this file in the email that opens)' : ''; });
})();
