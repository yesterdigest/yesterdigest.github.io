/* 홈 — 화면 전환 · 목록(햄버거) · 편 캐러셀 · 맞이하는 캐릭터
   JS 가 안 돌면 모든 화면이 «그냥 다 보인다» (검색엔진·심사자도 전부 읽는다).
   🔴 카드를 다 보여주는 장치(라이트박스·영상 재생)는 일부러 두지 않는다 —
      더 보려면 Instagram·YouTube 로 넘어가야 한다 (유진님 2026-09-12 07:54). */
(function () {
  'use strict';
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var root = document.documentElement;
  root.classList.add('js');                 /* 이 클래스가 있어야 한 화면만 보인다 */

  var 상단바 = function () {};   /* 4번에서 채운다. show() 가 먼저 부르므로 여기서 만든다 */

  /* ── 1. 화면 전환 ───────────────────────────── */
  var views = [].slice.call(document.querySelectorAll('.view'));
  var 기본 = document.body.getAttribute('data-default-view');

  function show(id, push) {
    var target = document.getElementById('view-' + id);
    if (!target) { id = 기본; target = document.getElementById('view-' + id); }
    if (!target) return;
    views.forEach(function (v) { v.classList.toggle('is-active', v === target); });
    document.querySelectorAll('.menu-item[data-view]').forEach(function (a) {
      if (a.getAttribute('data-view') === id) a.setAttribute('aria-current', 'page');
      else a.removeAttribute('aria-current');
    });
    if (push && location.hash.slice(1) !== id) history.pushState(null, '', '#' + id);
    /* 이 화면의 그림은 «열릴 때» 받는다 — 숨은 화면 그림까지 첫 화면에서 받지 않도록 */
    target.querySelectorAll('img[data-src]').forEach(function (im) {
      im.src = im.getAttribute('data-src');
      im.removeAttribute('data-src');
    });
    window.scrollTo({ top: 0, behavior: 'auto' });
    /* 화면이 바뀐 것을 읽어주는 기계에도 알린다 */
    target.setAttribute('tabindex', '-1');
    target.focus({ preventScroll: true });
    상단바();
  }

  /* data-view 가 붙은 것은 «페이지 이동»이 아니라 «화면 전환» */
  document.addEventListener('click', function (ev) {
    var a = ev.target.closest('[data-view]');
    if (!a || a.target === '_blank') return;
    ev.preventDefault();
    close서랍();
    show(a.getAttribute('data-view'), true);
  });

  window.addEventListener('popstate', function () { show(location.hash.slice(1) || 기본, false); });
  show(location.hash.slice(1) || 기본, false);

  /* ── 2. 목록(햄버거) ────────────────────────── */
  var drawer = document.getElementById('drawer');
  var backdrop = document.getElementById('drawer-backdrop');
  var openBtn = document.getElementById('menu-open');
  var closeBtn = document.getElementById('menu-close');

  function open서랍() {
    drawer.hidden = false; backdrop.hidden = false;
    requestAnimationFrame(function () {
      drawer.classList.add('is-open'); backdrop.classList.add('is-open');
    });
    openBtn.setAttribute('aria-expanded', 'true');
    document.body.style.overflow = 'hidden';
    closeBtn.focus();
  }

  function close서랍() {
    if (drawer.hidden) return;
    drawer.classList.remove('is-open'); backdrop.classList.remove('is-open');
    openBtn.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
    setTimeout(function () { drawer.hidden = true; backdrop.hidden = true; }, 280);
    openBtn.focus();
  }

  openBtn.addEventListener('click', open서랍);
  closeBtn.addEventListener('click', close서랍);
  backdrop.addEventListener('click', close서랍);
  document.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape') close서랍();
  });
  /* 바깥 페이지(개인정보·약관)로 가는 줄은 그대로 이동시키되 서랍은 닫는다 */
  drawer.querySelectorAll('.menu-item:not([data-view])').forEach(function (a) {
    a.addEventListener('click', close서랍);
  });

  /* ── 3. 상단 바 — 맨 위에서는 배경과 이어지고, 내리면 드러난다 ──
     유진님 2026-09-12 09:24. 임계값은 «상단 바 높이의 40%»로 재서 잡는다(고정 숫자를 안 박는다). */
  var header = document.querySelector('.site-header');
  if (header) {
    var 문턱 = function () { return Math.max(12, header.offsetHeight * 0.4); };
    상단바 = function () {
      document.documentElement.style.setProperty('--header-h', header.offsetHeight + 'px');
      /* 🔴 투명 + 밝은 글자는 «어두운 첫 화면 위에 있을 때»만 쓴다.
         지난 편 화면은 위가 살구색이라, 거기서 투명하게 두면 흰 글자가 안 보인다. */
      var 어두운첫화면 = !!document.querySelector('.view.is-active .showcase');
      header.classList.toggle('is-stuck', window.scrollY > 문턱() || !어두운첫화면);
    };
    window.addEventListener('scroll', 상단바, { passive: true });
    window.addEventListener('resize', 상단바);
    상단바();
  }

  /* ── 4. 첫 화면 쇼케이스 — 가만히 두면 저절로 바뀐다 ──
     유진님 2026-09-12 09:26. 장 수는 data/showcase.json 이 정하므로 여기서는 «세어서» 쓴다. */
  var sc = document.querySelector('.showcase');
  if (sc) {
    var 장 = [].slice.call(sc.querySelectorAll('.sc-panel'));
    var dotBox = sc.querySelector('.sc-dots');
    var 간격 = parseInt(sc.getAttribute('data-interval'), 10) || 7000;
    var 지금 = 0, 타이머 = null, 멈춤 = false;

    var scDots = 장.map(function (p, i) {
      var b = document.createElement('button');
      b.type = 'button';
      b.setAttribute('role', 'tab');
      b.setAttribute('aria-label', (i + 1) + '번째 소개 화면');
      b.addEventListener('click', function () { 보이기(i); 세우기(); 돌리기(); });
      dotBox.appendChild(b);
      return b;
    });

    function 보이기(i) {
      지금 = (i + 장.length) % 장.length;
      장.forEach(function (p, k) {
        var on = k === 지금;
        p.classList.toggle('is-on', on);
        p.setAttribute('aria-hidden', on ? 'false' : 'true');
        if (on) {
          /* 이 장의 그림은 «처음 보일 때» 받는다 — 첫 그림이 늦지 않게 */
          p.querySelectorAll('img[data-src]').forEach(function (im) {
            im.src = im.getAttribute('data-src');
            im.removeAttribute('data-src');
          });
        }
      });
      scDots.forEach(function (d, k) {
        d.classList.toggle('is-on', k === 지금);
        d.setAttribute('aria-selected', k === 지금 ? 'true' : 'false');
      });
    }

    function 돌리기() {
      if (타이머 || 멈춤 || reduce || 장.length < 2) return;
      타이머 = setInterval(function () { 보이기(지금 + 1); }, 간격);
    }

    function 세우기() {
      if (타이머) { clearInterval(타이머); 타이머 = null; }
    }

    /* 마우스를 올리거나 초점이 들어오면 멈춘다 — 읽는 중에 넘어가지 않게.
       🔴 pointerenter 가 아니라 mouseenter 를 쓴다. 손가락은 pointerenter 는 일으키고
          pointerleave 는 «안 일으킬 때»가 있어, 폰에서 한 번 만지면 영영 멈춰버린다. */
    ['mouseenter', 'focusin'].forEach(function (ev) {
      sc.addEventListener(ev, function () { 멈춤 = true; 세우기(); });
    });
    ['mouseleave', 'focusout'].forEach(function (ev) {
      sc.addEventListener(ev, function () { 멈춤 = false; 돌리기(); });
    });
    document.addEventListener('visibilitychange', function () {
      if (document.hidden) 세우기(); else 돌리기();
    });

    /* 손가락으로 넘기기 */
    var sx = 0, sy = 0, 끌기 = false;
    sc.addEventListener('touchstart', function (ev) {
      sx = ev.touches[0].clientX; sy = ev.touches[0].clientY; 끌기 = true; 세우기();
    }, { passive: true });
    sc.addEventListener('touchend', function (ev) {
      if (!끌기) return;
      끌기 = false;
      var dx = ev.changedTouches[0].clientX - sx;
      var dy = ev.changedTouches[0].clientY - sy;
      if (Math.abs(dx) > 45 && Math.abs(dx) > Math.abs(dy)) 보이기(지금 + (dx < 0 ? 1 : -1));
      돌리기();
    }, { passive: true });

    보이기(0);
    돌리기();     /* prefers-reduced-motion 이면 돌리기()가 스스로 아무것도 안 한다 */
  }

  /* ── 5. 맞이하는 캐릭터 ─────────────────────── */
  /* 정지 PNG(105KB)가 먼저 뜨고, 그 위에 GIF(350KB)를 «따로 받아» 다 받은 뒤에만 바꾼다.
     첫 그림이 늦어지지 않고, 못 받으면 PNG 그대로 남는다.
     움직임을 마다하는 설정이면 아예 받지 않는다. */
  var 캐릭터 = document.getElementById('hero-char');
  if (캐릭터 && !reduce) {
    var 움직임 = 캐릭터.getAttribute('data-motion');
    if (움직임) {
      var pre = new Image();
      pre.onload = function () { 캐릭터.src = 움직임; 캐릭터.classList.add('is-waving'); };
      pre.src = 움직임;      /* onerror 는 두지 않는다 — 실패하면 PNG 가 그대로 있으면 된다 */
    }
  }

  /* ── 6. 스크롤 등장 — «스르륵» ─────────────────
     유진님 2026-09-12 10:16 「스르륵 나타나도록 해달라고 했는데 지금은 그냥 뚝 나눠져서 보여」.

     🔴 왜 안 보였나 — 예전 코드는 «3초 뒤에 남은 것을 전부» 보이게 하는 안전망을 뒀다.
        사람은 대개 3초 안에 스크롤을 안 내린다. 그래서 내려갔을 땐 아래 것들이 «이미 다 나타나 있어»
        나타나는 장면을 한 번도 못 본다. 「뚝 나눠져 보인다」가 이것이다.
     그래서 관찰자를 걷어내고 «창 아래 끝에 닿으면 그때» 한 덩어리씩 켠다.
     🔴 안전망은 남긴다 — 다만 «하나도 못 켰을 때»만 켜지게 해서, 정상일 때는 안 끼어든다. */
  var 나타날것 = [].slice.call(document.querySelectorAll('.reveal'));

  if (reduce) {
    나타날것.forEach(function (el) { el.classList.add('is-in'); });
  } else {
    var 예약 = false, 시계 = null;

    function 훑기() {
      예약 = false;
      var 문턱 = window.innerHeight * 0.88;   /* 창 아래에서 12% 올라온 선 */
      var n = 0;
      나타날것 = 나타날것.filter(function (el) {
        var r = el.getBoundingClientRect();
        if (r.height === 0 && r.top === 0) return true;      /* 아직 안 열린 화면 */
        if (r.top > 문턱) return true;
        /* 한 번에 여러 개가 걸리면 조금씩 시차를 둔다 — 한꺼번에 튀어나오지 않게 */
        el.style.setProperty('--d', (n++ * 110) + 'ms');
        el.classList.add('is-in');
        return false;
      });
      if (!나타날것.length && 시계) { clearInterval(시계); 시계 = null; }
    }

    function 예약하기() {
      if (예약) return;
      예약 = true;
      requestAnimationFrame(훑기);
    }

    window.addEventListener('scroll', 예약하기, { passive: true });
    window.addEventListener('resize', 예약하기);
    /* 🔴 안전망은 «시간»이 아니라 «되풀이»다.
       예전 코드는 3초 뒤에 남은 것을 «전부» 켰다. 사람은 대개 3초 안에 스크롤을 안 내리므로
       내려갔을 땐 아래가 이미 다 켜져 있어 나타나는 장면을 한 번도 못 봤다
       (유진님 2026-09-12 10:16 「그냥 뚝 나눠져서 보여」).
       그래서 «보이는 자리에 온 것만» 켜는 같은 검사를 0.6초마다 되풀이한다 —
       스크롤 신호가 안 오는 환경에서도 글이 사라지지 않고, 정상일 때도 미리 켜지지 않는다.
       다 켜지면 스스로 멈춘다. */
    시계 = setInterval(훑기, 600);
    훑기();
  }
})();
