/* Salon joylashuvini telefon GPS'i orqali belgilash.
 *
 * Xarita Yandex API kalitiga bog'liq. Kalit bo'lmasa yoki xarita
 * yuklanmasa, sartarosh joylashuvini umuman belgilay olmasdi — hidden
 * maydonlar `required` bo'lgani uchun forma ham yuborilmasdi.
 *
 * Bu tugma xaritaga umuman bog'liq emas: brauzerning o'z geolokatsiyasi
 * koordinatani to'g'ridan-to'g'ri beradi. Sartarosh odatda o'z salonida
 * turib ro'yxatdan o'tadi, shuning uchun bu ko'pincha xaritadan ham
 * qulayroq.
 *
 * Kerakli elementlar: #use-gps-btn, #use-gps-text, #location_lat, #location_lng
 */
(function () {
    'use strict';

    var btn = document.getElementById('use-gps-btn');
    if (!btn) return;

    var label = document.getElementById('use-gps-text');
    var latInput = document.getElementById('location_lat');
    var lngInput = document.getElementById('location_lng');
    if (!latInput || !lngInput) return;

    if (!navigator.geolocation) {
        btn.style.display = 'none';
        return;
    }

    function setLabel(key) {
        if (label) label.textContent = btn.dataset[key];
    }

    btn.addEventListener('click', function () {
        btn.disabled = true;
        btn.classList.remove('is-done', 'is-error');
        setLabel('labelLocating');

        navigator.geolocation.getCurrentPosition(
            function (pos) {
                latInput.value = pos.coords.latitude.toFixed(6);
                lngInput.value = pos.coords.longitude.toFixed(6);

                // Xaritadagi xato xabari ochiq turgan bo'lsa yopamiz —
                // joylashuv endi belgilangan.
                var err = document.getElementById('location-error');
                if (err) err.style.display = 'none';

                // Xarita yuklangan bo'lsa, nuqtani unda ham ko'rsatamiz.
                if (typeof window.tonsorSetMapPoint === 'function') {
                    try {
                        window.tonsorSetMapPoint(
                            pos.coords.latitude, pos.coords.longitude);
                    } catch (e) { /* xarita ishlamasa ham koordinata saqlanadi */ }
                }

                btn.classList.add('is-done');
                setLabel('labelDone');
                btn.disabled = false;
            },
            function () {
                btn.classList.add('is-error');
                setLabel('labelDenied');
                setTimeout(function () {
                    btn.classList.remove('is-error');
                    setLabel('labelDefault');
                    btn.disabled = false;
                }, 2800);
            },
            { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
        );
    });
})();
