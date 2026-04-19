/* ============================================================
   StudyStream  ss-shared.js  — NO DOMContentLoaded anywhere.
   Every function runs immediately as an IIFE.
   Script loads at bottom of <body> so DOM is always ready.
   ============================================================ */

// ── Theme ─────────────────────────────────────────────────────
(function () {
    var html = document.documentElement;
    var saved = localStorage.getItem('ss-theme') || 'dark';
    html.setAttribute('data-theme', saved);
    var toggle = document.getElementById('themeToggle');
    if (toggle) {
        toggle.checked = saved === 'light';
        toggle.addEventListener('change', function () {
            var next = this.checked ? 'light' : 'dark';
            html.setAttribute('data-theme', next);
            localStorage.setItem('ss-theme', next);
        });
    }
})();

// ── User Menu Pill ────────────────────────────────────────────
(function () {
    var trigger  = document.getElementById('userMenuTrigger');
    var dropdown = document.getElementById('userMenuDropdown');
    var caret    = document.querySelector('#userMenuTrigger .ss-user-caret');
    if (!trigger || !dropdown) return;

    function open()  { dropdown.classList.add('open');    if(caret) caret.style.transform='rotate(180deg)'; trigger.setAttribute('aria-expanded','true');  }
    function close() { dropdown.classList.remove('open'); if(caret) caret.style.transform='';              trigger.setAttribute('aria-expanded','false'); }
    function toggle(e) { e.stopPropagation(); dropdown.classList.contains('open') ? close() : open(); }

    trigger.addEventListener('click', toggle);
    document.addEventListener('click', function (e) {
        if (!trigger.contains(e.target) && !dropdown.contains(e.target)) close();
    });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });
})();

// ── CSRF ──────────────────────────────────────────────────────
window.getCsrf = function () {
    var match = document.cookie.split(';').map(function(c){return c.trim();}).find(function(c){return c.startsWith('csrftoken=');});
    return match ? match.split('=')[1] : '';
};

// ── Color Swatches ────────────────────────────────────────────
window.buildSwatches = function (containerId, hiddenId, colors, defaultColor) {
    var container = document.getElementById(containerId);
    var hidden    = document.getElementById(hiddenId);
    if (!container || !hidden) return;
    if (!hidden.value) hidden.value = defaultColor;
    colors.forEach(function (hex) {
        var s = document.createElement('div');
        s.className = 'ss-swatch' + (hex.toLowerCase() === (hidden.value || '').toLowerCase() ? ' active' : '');
        s.style.background = hex;
        s.title = hex;
        s.addEventListener('click', function () {
            container.querySelectorAll('.ss-swatch').forEach(function (x) { x.classList.remove('active'); });
            s.classList.add('active');
            hidden.value = hex;
        });
        container.appendChild(s);
    });
};
