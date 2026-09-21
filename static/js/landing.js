/**
 * TONSOR — Landing scroll choreography
 * Reveal-on-scroll (up / left / right / scale), parallax depth,
 * count-up stats, sticky horizontal scroll section, progress bar + nav state.
 * Scoped: only runs when a .lx landing root is present.
 */
(function () {
    'use strict';

    if (!document.querySelector('.lx')) return;

    var progressBar = document.querySelector('.lx-progress > span');
    var navbar = document.querySelector('.navbar');
    var pin = document.querySelector('.lx-pin');
    var track = document.querySelector('.lx-htrack');
    var parallax = document.querySelectorAll('.lx-parallax');

    var prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    /* ---------- Reveal on scroll ---------- */
    var revealEls = document.querySelectorAll('.lx-reveal');
    if ('IntersectionObserver' in window) {
        var io = new IntersectionObserver(function (entries) {
            entries.forEach(function (e) {
                if (e.isIntersecting) {
                    e.target.classList.add('in');
                    io.unobserve(e.target);
                }
            });
        }, { threshold: 0.18, rootMargin: '0px 0px -70px 0px' });
        revealEls.forEach(function (el) { io.observe(el); });
    } else {
        revealEls.forEach(function (el) { el.classList.add('in'); });
    }

    /* ---------- Count-up stats ---------- */
    var counters = document.querySelectorAll('[data-count]');
    if ('IntersectionObserver' in window) {
        var cio = new IntersectionObserver(function (entries) {
            entries.forEach(function (e) {
                if (e.isIntersecting) { runCount(e.target); cio.unobserve(e.target); }
            });
        }, { threshold: 0.6 });
        counters.forEach(function (el) { cio.observe(el); });
    } else {
        counters.forEach(function (el) { finishCount(el); });
    }

    function finishCount(el) {
        var dec = parseInt(el.dataset.decimals || '0', 10);
        el.textContent = parseFloat(el.dataset.count).toFixed(dec) + (el.dataset.suffix || '');
    }
    function runCount(el) {
        if (prefersReduced) { finishCount(el); return; }
        var target = parseFloat(el.dataset.count);
        var dec = parseInt(el.dataset.decimals || '0', 10);
        var suffix = el.dataset.suffix || '';
        var dur = 1500, start = performance.now();
        function tick(now) {
            var p = Math.min((now - start) / dur, 1);
            var eased = 1 - Math.pow(1 - p, 3);
            el.textContent = (target * eased).toFixed(dec) + suffix;
            if (p < 1) requestAnimationFrame(tick);
            else el.textContent = target.toFixed(dec) + suffix;
        }
        requestAnimationFrame(tick);
    }

    /* ---------- Pin length matched to the actual horizontal travel ----------
       A fixed 360vh made wide screens scroll ~3.5 viewports to move the cards a couple
       hundred pixels. Size the pin from how far the track really has to move instead. */
    function sizePin() {
        if (!pin || !track) return;
        if (prefersReduced) { pin.style.height = ''; return; }
        var maxX = track.scrollWidth - track.parentElement.clientWidth;
        if (maxX < 0) maxX = 0;
        // Phones scroll a shorter runway per pixel of travel, otherwise the section drags.
        var factor = window.innerWidth <= 900 ? 0.8 : 1.15;
        pin.style.height = Math.round(window.innerHeight + maxX * factor) + 'px';
    }

    /* ---------- rAF-driven scroll loop ---------- */
    var ticking = false;
    function onScroll() {
        if (!ticking) { requestAnimationFrame(update); ticking = true; }
    }
    function update() {
        ticking = false;
        var sy = window.pageYOffset;
        var docH = document.documentElement.scrollHeight - window.innerHeight;

        if (progressBar) {
            progressBar.style.transform = 'scaleX(' + (docH > 0 ? (sy / docH) : 0) + ')';
        }
        if (navbar) {
            navbar.classList.toggle('scrolled', sy > 40);
        }

        if (!prefersReduced) {
            for (var i = 0; i < parallax.length; i++) {
                var sp = parseFloat(parallax[i].dataset.speed || '0.15');
                parallax[i].style.transform = 'translate3d(0,' + (sy * sp) + 'px,0)';
            }
        }

        /* Sticky horizontal scroll — runs on phones and tablets too, not just desktop */
        if (pin && track) {
            if (!prefersReduced) {
                var rect = pin.getBoundingClientRect();
                var total = pin.offsetHeight - window.innerHeight;
                var prog = total > 0 ? (-rect.top) / total : 0;
                prog = prog < 0 ? 0 : (prog > 1 ? 1 : prog);
                var maxX = track.scrollWidth - track.parentElement.clientWidth;
                if (maxX < 0) maxX = 0;
                track.style.transform = 'translate3d(' + (-prog * maxX) + 'px,0,0)';
            } else {
                track.style.transform = '';
            }
        }
    }

    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', function () { sizePin(); update(); });
    window.addEventListener('load', function () { sizePin(); update(); });
    sizePin();
    update();
})();
