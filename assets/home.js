/* 홈 — 화면 전환 · 목록(햄버거) · 지난 편 넘기기 · 소개 창
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

  /* data-view 가 붙은 «줄·단추»는 «페이지 이동»이 아니라 «화면 전환»
     🔴 2026-09-12 — 여기를 `[data-view]` 로 두면 «화면 자체»(<section class="view" data-view=…>)가
        걸린다. 그러면 그 화면 «아무 데나» 누른 것이 전부 「화면 전환」이 되어
          ① show() 의 scrollTo(0) 가 돌아 «보던 자리가 맨 위로 튄다»
             (유진님 14:52 「클릭하면 갑자기 이슈가 아래쪽으로 가버려」 — 실측 scrollY 138 → 0)
          ② ev.preventDefault() 가 걸려 «안쪽 링크가 통째로 죽는다»
             (실측: 지난 편의 INSTAGRAM·YOUTUBE·표지 링크가 눌러도 안 열렸다)
        그래서 «줄·단추만» 받는다. */
  document.addEventListener('click', function (ev) {
    var a = ev.target.closest('a[data-view], button[data-view]');
    if (!a || a.target === '_blank') return;
    ev.preventDefault();
    close서랍();
    show(a.getAttribute('data-view'), true);
  });

  window.addEventListener('popstate', function () { show(location.hash.slice(1) || 기본, false); });
  show(location.hash.slice(1) || 기본, false);

  /* ── 창이 열린 동안 «바깥»을 막는다 (5차 · A11Y-05) ──
     서랍·소개 창은 진짜 «창»이다(role=dialog · aria-modal). 열린 동안 머리줄·본문·구글 칸·바닥에 inert 를 걸어
     Tab 이 창 밖으로 새지 않게 하고, 닫으면 풀고 «연 단추»로 초점을 돌려준다. 지난 편 칸의 p.inert 와 같은 방식이다. */
  var 바깥 = ['.skip-link', '.site-header', '#main', '.oauth-note', '.site-footer'];   /* 5차 검수: 건너뛰기 링크로 초점이 샜다 */
  function 막기(on) {
    바깥.forEach(function (sel) {
      var el = document.querySelector(sel);
      if (el) el.inert = on;
    });
  }

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
    막기(true);
    closeBtn.focus();
  }

  function close서랍() {
    if (drawer.hidden) return;
    drawer.classList.remove('is-open'); backdrop.classList.remove('is-open');
    openBtn.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
    막기(false);                       /* 🔴 풀고 나서 초점을 준다 — inert 인 단추에는 초점이 안 간다 */
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
      /* 2026-09-24 — 첫 화면 맨 위는 이제 «제호»(.nameplate)다. 제호 위에서는 머리줄이 바탕과 한 몸(투명),
         내려가면 가는 선 한 줄로 갈라진다. 제호가 없는 화면(지난 편)에서는 처음부터 갈라진다. */
      var 어두운첫화면 = !!document.querySelector('.view.is-active .nameplate');
      header.classList.toggle('is-stuck', window.scrollY > 문턱() || !어두운첫화면);
    };
    window.addEventListener('scroll', 상단바, { passive: true });
    window.addEventListener('resize', 상단바);
    상단바();
  }

  /* ── 4·5. (옛) 첫 화면 쇼케이스 · 맞이하는 캐릭터 — 5차에 지웠다.
     쇼케이스 장(.showcase)과 움직이는 캐릭터(#hero-char · GIF)는 이미 페이지에 없다(4차 제호 판). 남은 코드만 걷었다. */

  /* ── 6. 지난 편 — 한 번 밀면 한 편 ─────────────
     🔴 2026-09-12 유진님 12:39.
       ① 「한번의 드래그로 한페이지씩 넘기듯이 … 연속적으로 드래그해야 조금씩 넘어가도록 되어있어」
       ② 「아래로 내리다가 갑자기 이 옆으로 넘어가는 게 떠서 끝까지 내려서 보고싶었던 사람들이 못볼거 같아
           … 이 옆으로 슬라이드로 넘기는 것은 클릭하고 스크롤해야 넘어가도록」

     2차는 스크롤 자리를 통째로 가로 이동에 썼다(sticky + 창높이×편수). 그래서 페이지가
     «안 내려가는» 것처럼 느껴졌다. 이제 세로 스크롤은 언제나 페이지 몫이고,
     옆으로 가는 것은 «한 번에 한 편»씩 index 로만 움직인다.

       평소            : 스크롤은 아래로만. 옆으로 안 간다
       끌기·스와이프    : 언제나 한 편 (문턱 45px · 가로가 세로보다 클 때만)
       화살표·방향키    : 언제나 한 편
       🔴 휠로 옆으로   : «눌러서 잡았을 때»만. 끝에 닿으면 스스로 풀려 페이지가 다시 내려간다
     🔴 움직임을 마다한 설정이면 아무것도 안 한다 — CSS 가 위아래로 쌓아준다. */
  document.querySelectorAll('.ed-rail').forEach(function (rail) {
    var stage = rail.querySelector('.ed-stage');
    var track = rail.querySelector('.ed-track');
    var fill = rail.querySelector('.ed-progress i');
    var hint = rail.querySelector('.ed-hint');
    var prev = rail.querySelector('.ed-prev');
    var next = rail.querySelector('.ed-next');
    if (!track) return;
    var 칸 = [].slice.call(track.children);
    var n = 칸.length;
    if (n < 2) { if (hint) hint.remove(); if (prev) prev.parentElement.remove(); return; }

    if (reduce) {                       /* 옆으로 밀지 않는다. 위아래로 쌓아 보여준다 */
      stage.style.overflow = 'visible';
      stage.style.paddingBlock = '0';
      stage.removeAttribute('tabindex');
      track.style.flexDirection = 'column';
      track.style.gap = '56px';
      track.style.transform = 'none';
      칸.forEach(function (p) {
        p.style.flex = 'none';
        p.querySelectorAll('img[data-src]').forEach(그림받기);
      });
      [hint, fill && fill.parentElement, prev && prev.parentElement].forEach(function (el) {
        if (el) el.style.display = 'none';
      });
      return;
    }

    rail.style.setProperty('--n', n);
    var i = 0, 잡힘 = false, 최근 = 0;

    function 그림받기(im) {
      if (!im.getAttribute) return;
      var src = im.getAttribute('data-src');
      if (!src) return;
      im.src = src;
      im.removeAttribute('data-src');
    }

    function 그리기() {
      track.style.setProperty('--i', i);
      if (fill) fill.style.setProperty('--p', (i * 100) + '%');
      칸.forEach(function (p, k) {
        /* 🔴 안 보이는 칸은 Tab 으로 걸리지 않게 한다 — 안 그러면 화면 밖 링크에 초점이 간다 */
        p.inert = k !== i;
        p.setAttribute('aria-hidden', k === i ? 'false' : 'true');
        /* 🔴 왼쪽 이웃은 «안을 좌우로 뒤집는다» — 안 그러면 보이는 것이 글칸의 «꼬리»뿐이라
           거의 안 보인다 (실측: 왼쪽 이웃의 배경 대비 최대 6.9 ↔ 오른쪽 이웃 28.7).
           뒤집으면 왼쪽 이웃도 «표지»가 안쪽 가장자리에 와서 좌우가 같은 결이 된다. */
        p.dataset['곁'] = k < i ? '왼' : k > i ? '오' : '';
        if (Math.abs(k - i) <= 1) p.querySelectorAll('img[data-src]').forEach(그림받기);
      });
      if (prev) prev.disabled = i === 0;
      if (next) next.disabled = i === n - 1;
      /* 🔴 끝에 서면 «빈 쪽»에 표시를 띄운다 (유진님 16:29). 둘을 «따로» 둔다 —
         편이 둘뿐이면 한 편이 처음이자 마지막이라 양쪽이 다 빈다. */
      stage.classList.toggle('is-first', i === 0);
      stage.classList.toggle('is-last', i === n - 1);
    }

    function 가기(d) {
      var j = Math.max(0, Math.min(n - 1, i + d));
      if (j === i) return false;
      i = j; 그리기();
      return true;
    }

    /* 안내 글 — 마우스(fine)면 「DRAG · ← →」, 손가락(coarse)이면 「SWIPE」 (5차 · 옛 TAP TO BROWSE) */
    var 손가락 = window.matchMedia ? window.matchMedia('(pointer: coarse)') : null;
    function 안내() {
      if (!hint) return;
      hint.textContent = hint.getAttribute(잡힘 ? 'data-on' : (손가락 && 손가락.matches ? 'data-coarse' : 'data-fine'));
    }
    if (손가락 && 손가락.addEventListener) 손가락.addEventListener('change', 안내);

    function 잡기(on) {
      var 바뀜 = 잡힘 !== on;
      잡힘 = on;
      stage.classList.toggle('is-held', on);
      /* 🔴 머리줄은 z-index 20 이라 무대의 «주변 음영»(box-shadow) 위에 뜬다.
         CSS 가 위로 못 올라가므로 여기서 body 에 표시를 남긴다 (유진님 16:05 「위 아래는 음영처리」).
         🔴 5차 — 잡힌 동안 머리줄은 흐리게(.3) 두지 않고 inert 로 막는다(누를 수 없는 것이 흐린 글자로 남지 않게) */
      document.body.classList.toggle('ed-held', on);
      if (바뀜 && header) header.inert = on;
      안내();
    }

    /* 🔴 누른 칸을 «화면 세로 가운데»로 (유진님 2026-09-12 14:52 「딱 화면 중앙으로 이동」).
       무대 안쪽(칸)을 scrollIntoView 하면 overflow:hidden 인 무대가 «가로로» 스스로 움직여
       transform 자리가 틀어진다. 그래서 «창»만 그만큼 민다. */
    function 가운데로() {
      var r = 칸[i].getBoundingClientRect();
      var d = r.top + r.height / 2 - window.innerHeight / 2;
      if (Math.abs(d) < 2) return;
      window.scrollBy({ top: d, behavior: reduce ? 'auto' : 'smooth' });
    }

    /* 누르면 잡힌다 — 안쪽 링크·단추를 누른 것은 그대로 링크다 */
    stage.addEventListener('click', function (ev) {
      if (ev.target.closest('a, button')) return;
      if (끌었다) { 끌었다 = false; return; }
      잡기(!잡힘);
      /* 🔴 초점이 «옮겨질 때»는 아래 focus 처리기가 가운데로 옮긴다. 여기서 또 부르면
         부드럽게 미는 동안에는 scrollY 가 아직 안 움직여서 «두 배로» 지나친다.
         그래서 초점이 이미 무대에 있어 focus 가 안 뜨는 경우에만 직접 부른다. */
      var 초점이온다 = document.activeElement !== stage;
      stage.focus({ preventScroll: true });   /* 브라우저가 제멋대로 옮기지 못하게 막고 */
      if (!초점이온다) 가운데로();             /* 우리가 «가운데»로 옮긴다 */
    });

    /* 키보드로 닿았을 때도 같게 — Tab 으로 무대에 들어오면 가운데에 온다 */
    stage.addEventListener('focus', 가운데로);

    /* 🔴 잡혔을 때만 휠이 옆으로 간다. 끝에 닿으면 «풀고» 페이지가 이어서 내려간다 */
    stage.addEventListener('wheel', function (ev) {
      if (!잡힘) return;                              /* 평소에는 그냥 페이지가 내려간다 */
      if (Math.abs(ev.deltaX) > Math.abs(ev.deltaY)) return;   /* 가로 휠은 브라우저에 맡긴다 */
      var d = ev.deltaY > 0 ? 1 : -1;
      if ((d > 0 && i === n - 1) || (d < 0 && i === 0)) { 잡기(false); return; }
      ev.preventDefault();
      var t = Date.now();
      if (t - 최근 < 520) return;      /* 넘어가는 동안 들어온 것은 무시 — 여러 편이 튀지 않게 */
      최근 = t;
      가기(d);
    }, { passive: false });

    /* 끌기·스와이프 — 한 번에 한 편. 세로 스크롤은 막지 않는다(CSS touch-action: pan-y) */
    var sx = 0, sy = 0, 눌림 = false, 끌었다 = false;
    stage.addEventListener('pointerdown', function (ev) {
      if (ev.button) return;
      sx = ev.clientX; sy = ev.clientY; 눌림 = true; 끌었다 = false;
    });
    stage.addEventListener('pointerup', function (ev) {
      if (!눌림) return;
      눌림 = false;
      var dx = ev.clientX - sx, dy = ev.clientY - sy;
      if (Math.abs(dx) > 45 && Math.abs(dx) > Math.abs(dy)) {
        끌었다 = true;                    /* 이 뒤에 오는 click 은 «잡기»가 아니다 */
        가기(dx < 0 ? 1 : -1);
      }
    });
    stage.addEventListener('pointercancel', function () { 눌림 = false; });

    /* 방향키 — 잡지 않아도 된다. Esc 로 푼다 */
    stage.addEventListener('keydown', function (ev) {
      if (ev.key === 'ArrowRight') { ev.preventDefault(); 가기(1); }
      else if (ev.key === 'ArrowLeft') { ev.preventDefault(); 가기(-1); }
      else if (ev.key === 'Escape') 잡기(false);
    });
    document.addEventListener('keydown', function (ev) { if (ev.key === 'Escape') 잡기(false); });

    if (prev) prev.addEventListener('click', function () { 가기(-1); });
    if (next) next.addEventListener('click', function () { 가기(1); });

    그리기();
    안내();
  });

  /* ── 7. 소개 영상 «틀» — 커졌다 줄어든다 ────────
     영상은 아직 없다. 움직임과 자리만 미리 만들어 둔다 (유진님 11:19 · 팀장 판단으로 영상은 오늘 안 만든다).
     영상이 생기면 .intro-slot 안만 <video> 로 바꾸면 되고, 이 코드는 그대로 쓴다. */
  var introBtn = document.getElementById('intro-open');   /* = 유튜브 장 폰 안의 «재생 단추» */
  var introBox = document.getElementById('intro-modal');
  if (introBox) {
    var introClose = document.getElementById('intro-close');
    var 되돌릴곳 = null;

    function 열기() {
      되돌릴곳 = document.activeElement;
      introBox.hidden = false;
      requestAnimationFrame(function () { introBox.classList.add('is-open'); });
      document.body.style.overflow = 'hidden';
      막기(true);
      introClose.focus();
    }

    function 닫기() {
      if (introBox.hidden) return;
      introBox.classList.remove('is-open');          /* 줄어든다 */
      document.body.style.overflow = '';
      막기(false);                                   /* 🔴 풀고 나서 초점을 «연 단추»로 돌려준다 */
      setTimeout(function () { introBox.hidden = true; }, 340);
      if (되돌릴곳 && 되돌릴곳.focus) 되돌릴곳.focus();
    }

    /* 🔴 2026-09-12 유진님 15:17 — 「유튜브 소개 페이지에서 재생버튼을 누르면 이 웹에서
       소개영상을 띄워야지 유튜브 채널로 가는거 아니야. 기억해.」
       🔴 5차 — 재생 단추는 이제 링크 «밖»(덮개 링크 .dv-cover 의 형제)이다. 이동을 막는 꼼수
       (preventDefault · stopPropagation)가 필요 없어 지웠다. 폰의 «다른 곳»은 덮개 링크라 그 편 게시물로 간다. */
    if (introBtn) introBtn.addEventListener('click', 열기);
    introClose.addEventListener('click', 닫기);
    introBox.addEventListener('click', function (ev) { if (ev.target === introBox) 닫기(); });
    document.addEventListener('keydown', function (ev) { if (ev.key === 'Escape') 닫기(); });
  }

  /* ── 8. 스크롤 등장 — «스르륵» ─────────────────
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
    var 예약 = false;

    /* 🔴 «켜고 끝»이 아니라 «오르내릴 때마다» 다시 켠다 (유진님 2026-09-12 11:19
       「한번 내렸다가 다시 올리고 내리면 또 스르륵이 되어야하는데 지금은 그게 안되네」).
       예전 코드는 한 번 켠 것을 목록에서 «빼버려서» 두 번째부터는 아무 일도 안 일어났다.

       켜는 선과 끄는 선을 «다르게» 둔다(히스테리시스) —
         켠다: 창 아래에서 12% 올라온 선에 닿을 때
         끈다: 창 «아래»로 완전히 내려갔을 때만
       두 선이 같으면 그 언저리에서 깜빡인다. 그리고 끄는 선이 «창 밖»이라
       🔴 보이는 글이 사라지는 일은 구조적으로 없다. */
    function 훑기() {
      예약 = false;
      var 창 = window.innerHeight;
      var 켤선 = 창 * 0.88;
      var n = 0;
      나타날것.forEach(function (el) {
        var r = el.getBoundingClientRect();
        if (r.height === 0 && r.top === 0) return;          /* 아직 안 열린 화면 */
        var 켜짐 = el.classList.contains('is-in');
        if (!켜짐 && r.top < 켤선) {
          /* 한 번에 여러 개가 걸리면 조금씩 시차를 둔다 — 한꺼번에 튀어나오지 않게 */
          el.style.setProperty('--d', (n++ * 110) + 'ms');
          el.classList.add('is-in');
        } else if (켜짐 && r.top > 창) {
          el.classList.remove('is-in');                     /* 창 밖(아래)으로 나갔을 때만 */
        }
      });
    }

    function 예약하기() {
      if (예약) return;
      예약 = true;
      requestAnimationFrame(훑기);
    }

    window.addEventListener('scroll', 예약하기, { passive: true });
    window.addEventListener('resize', 예약하기);
    /* 🔴 안전망: 스크롤 신호가 아예 안 오는 환경에서도 글이 사라지지 않게 0.6초마다 같은 검사를
       되풀이한다. «보이는 자리에 온 것만» 켜므로 미리 켜지지도 않는다. */
    setInterval(훑기, 600);
    훑기();
  }

  /* ── 분야 탭 셋 (2026-09-26 업그레이드) ─────────────────────
     WAI-ARIA 탭 짜임: 누르거나 ← → Home End 로 고른다. 고르지 않은 판은 hidden.
     🔴 JS 가 없으면 세 판이 «전부» 보인다(data-hidden 은 JS 가 있을 때만 hidden 으로 바뀐다).
     🔴 탭은 data-view 를 달지 않는다 — 화면 전환(closest('a[data-view], button[data-view]'))과 안 엉킨다. */
  document.querySelectorAll('[role="tablist"]').forEach(function (list) {
    var tabs = [].slice.call(list.querySelectorAll('[role="tab"]'));
    function 고르기(t, focus) {
      tabs.forEach(function (x) {
        var on = x === t;
        x.setAttribute('aria-selected', on ? 'true' : 'false');
        x.tabIndex = on ? 0 : -1;
        var panel = document.getElementById(x.getAttribute('aria-controls'));
        if (panel) {
          panel.hidden = !on;
          if (on) panel.querySelectorAll('img[data-src]').forEach(function (im) {
            im.src = im.getAttribute('data-src'); im.removeAttribute('data-src');
          });
        }
      });
      if (focus) t.focus();
    }
    tabs.forEach(function (t, i) {
      var panel = document.getElementById(t.getAttribute('aria-controls'));
      if (panel && panel.hasAttribute('data-hidden')) { panel.hidden = true; panel.removeAttribute('data-hidden'); }
      t.addEventListener('click', function () { 고르기(t, false); });
      t.addEventListener('keydown', function (ev) {
        var n = { ArrowRight: i + 1, ArrowLeft: i - 1, Home: 0, End: tabs.length - 1 }[ev.key];
        if (n === undefined) return;
        ev.preventDefault();
        고르기(tabs[(n + tabs.length) % tabs.length], true);
      });
    });
  });
  /* ── 채널 성장 그래프 (GROWTH · 2026-09-26 7차 시안) ─────────
     수는 build.py 가 실은 #growth-data(= data/growth.json)에서만 읽는다. 손으로 적은 수 0.
     그래프 하나 = 계열 하나 · 선 2px · 점 8px · 빠진 날(null)은 선을 «끊고» 옅은 띠.
     폭은 figure 의 실제 폭으로 그린다(viewBox 늘이기 없음 → 글자가 폰에서 안 작아진다). 숨은 화면(폭 0)은 ResizeObserver 가 열릴 때 그린다.
     마우스·손가락: 가까운 날에 세로선 + 말풍선 · 키보드: 그래프에 초점 → ← → Home End. */
  (function () {
    var src = document.getElementById('growth-data');
    if (!src) return;
    var G; try { G = JSON.parse(src.textContent); } catch (e) { return; }
    var NS = 'http://www.w3.org/2000/svg';
    function el(n, a, p) { var x = document.createElementNS(NS, n); for (var k in a) x.setAttribute(k, a[k]); if (p) p.appendChild(x); return x; }
    function 수(v) { return v == null ? '—' : v.toLocaleString('en-US'); }
    function 날(d) { return (+d.slice(5, 7)) + '.' + (+d.slice(8, 10)); }
    function 눈금(max) {                         /* 0 부터 «보기 좋은» 간격 3~5칸 */
      if (max <= 0) max = 1;
      var raw = max / 4, p = Math.pow(10, Math.floor(Math.log10(raw))), s = [1, 2, 2.5, 5, 10].map(function (m) { return m * p; })
        .filter(function (v) { return v >= raw; })[0];
      if (s < 1) s = 1;
      var t = []; for (var v = 0; v <= max + 1e-9 || t.length < 2; v += s) t.push(Math.round(v * 100) / 100);
      if (t[t.length - 1] < max) t.push(t[t.length - 1] + s);
      return t;
    }
    function draw(fig) {
      var S = G.그래프[+fig.getAttribute('data-series')], W = Math.round(fig.clientWidth), H = 190;
      if (!S || W < 40) return;
      if (fig._w === W) return; fig._w = W;
      var old = fig.querySelector('svg'); if (old) old.remove();
      var tipOld = fig.querySelector('.gr-tip'); if (tipOld) tipOld.remove();
      var vals = S.값, n = vals.length, have = vals.filter(function (v) { return v != null; });
      var ticks = 눈금(Math.max.apply(null, have)), top = ticks[ticks.length - 1];
      var svg = el('svg', { width: W, height: H, viewBox: '0 0 ' + W + ' ' + H, 'aria-hidden': 'true', focusable: 'false' });
      fig.insertBefore(svg, fig.firstChild);
      /* 왼쪽 눈금 글자 폭은 «재서» 정한다(짐작 폭은 글꼴이 바뀌면 그림 밖으로 샌다 — 7차 첫 측정에서 잡힘) */
      var yl = Math.max.apply(null, ticks.map(function (t) {
        var m = el('text', {}, svg); m.textContent = 수(t); var w = m.getComputedTextLength(); m.remove(); return w;
      })) + 10;
      var L = Math.ceil(yl) + 2, R = 14, T = 10, B = 24, pw = W - L - R, ph = H - T - B;
      var X = function (i) { return L + (n === 1 ? pw / 2 : pw * i / (n - 1)); };
      var Y = function (v) { return T + ph - ph * v / top; };
      ticks.forEach(function (t) {
        el('line', { x1: L, x2: W - R, y1: Y(t), y2: Y(t), 'class': t === 0 ? 'gr-axis' : 'gr-gridline' }, svg);
        var tx = el('text', { x: L - 8, y: Y(t) + 4, 'text-anchor': 'end' }, svg); tx.textContent = 수(t);
      });
      var step = n > 1 ? pw / (n - 1) : pw;
      vals.forEach(function (v, i) {                     /* 빠진 날 띠 */
        if (v == null) el('rect', { x: X(i) - step / 2, y: T, width: step, height: ph, 'class': 'gr-gapband' }, svg);
      });
      var every = Math.max(1, Math.ceil(n / Math.max(2, Math.floor(pw / 38))));
      var show = []; for (var q = 0; q < n; q += every) show.push(q);
      if (show[show.length - 1] !== n - 1) { if (n - 1 - show[show.length - 1] < every) show.pop(); show.push(n - 1); }
      G.날짜.forEach(function (d, i) {
        if (show.indexOf(i) < 0) return;
        var tx = el('text', { x: X(i), y: H - 6, 'text-anchor': i === 0 ? 'start' : (i === n - 1 ? 'end' : 'middle') }, svg);
        tx.textContent = 날(d);
      });
      var d = '', pen = false;                            /* 선 — null 에서 끊는다 */
      vals.forEach(function (v, i) {
        if (v == null) { pen = false; return; }
        d += (pen ? 'L' : 'M') + X(i).toFixed(1) + ' ' + Y(v).toFixed(1); pen = true;
      });
      el('path', { d: d, 'class': 'gr-line' }, svg);
      vals.forEach(function (v, i) { if (v != null) el('circle', { cx: X(i), cy: Y(v), r: 4, 'class': 'gr-dot' }, svg); });
      var li = -1; vals.forEach(function (v, i) { if (v != null) li = i; });
      var lt = el('text', { x: X(li) - 6, y: Y(vals[li]) - 10, 'text-anchor': 'end', 'class': 'gr-last' }, svg);
      lt.textContent = 수(vals[li]);                       /* 마지막 값만 직접 적는다(점마다 숫자 금지) */
      var cross = el('line', { y1: T, y2: T + ph, 'class': 'gr-cross', visibility: 'hidden' }, svg);
      var hot = el('circle', { r: 5.5, 'class': 'gr-hot', visibility: 'hidden' }, svg);
      var tip = document.createElement('div'); tip.className = 'gr-tip'; tip.hidden = true; fig.appendChild(tip);
      var cur = -1;
      function pick(i) {
        cur = i; var v = vals[i];
        cross.setAttribute('x1', X(i)); cross.setAttribute('x2', X(i)); cross.setAttribute('visibility', 'visible');
        if (v != null) { hot.setAttribute('cx', X(i)); hot.setAttribute('cy', Y(v)); hot.setAttribute('visibility', 'visible'); }
        else hot.setAttribute('visibility', 'hidden');
        tip.innerHTML = '';
        tip.appendChild(document.createTextNode(날(G.날짜[i]) + '  '));
        var b = document.createElement('b'); b.textContent = v == null ? '기록 없음' : 수(v) + S.단위; tip.appendChild(b);
        tip.hidden = false;
        var tw = tip.offsetWidth, x = X(i) - tw / 2; x = Math.max(0, Math.min(W - tw, x));
        tip.style.left = x + 'px';
        tip.style.top = (v == null ? T : Math.max(0, Y(v) - 44)) + 'px';
      }
      function clear() { cur = -1; cross.setAttribute('visibility', 'hidden'); hot.setAttribute('visibility', 'hidden'); tip.hidden = true; }
      function near(ev) {
        var r = svg.getBoundingClientRect(), x = ev.clientX - r.left;
        return Math.max(0, Math.min(n - 1, Math.round((x - L) / (n > 1 ? pw / (n - 1) : 1))));
      }
      svg.addEventListener('pointermove', function (ev) { pick(near(ev)); });
      svg.addEventListener('pointerdown', function (ev) { pick(near(ev)); });
      svg.addEventListener('pointerleave', function (ev) { if (ev.pointerType === 'mouse') clear(); });
      fig._key = function (ev) {
        var k = { ArrowRight: cur + 1, ArrowLeft: cur < 0 ? n - 1 : cur - 1, Home: 0, End: n - 1 }[ev.key];
        if (k === undefined) return; ev.preventDefault(); pick(Math.max(0, Math.min(n - 1, k)));
      };
      fig._clear = clear;
    }
    var figs = [].slice.call(document.querySelectorAll('.gr-fig[data-series]'));
    figs.forEach(function (f) {
      f.tabIndex = 0;
      f.addEventListener('keydown', function (ev) { if (f._key) f._key(ev); });
      f.addEventListener('blur', function () { if (f._clear) f._clear(); });
    });
    if ('ResizeObserver' in window) {
      var ro = new ResizeObserver(function (es) { es.forEach(function (e) { draw(e.target); }); });
      figs.forEach(function (f) { ro.observe(f); });
    } else { window.addEventListener('resize', function () { figs.forEach(draw); }); figs.forEach(draw); }
  })();
})();
