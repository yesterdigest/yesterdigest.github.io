/* 판 바꾸기 — 밝은 크림(기본) ↔ 어두운 먹.
   2026-09-24 유진님 「웹색상은 밝은 크림시문지로 바꾸되 다크모드 기눙도 넣어줘」 (팀장 전달).

   🔴 첫 방문은 «크림»이다 — OS 가 다크여도 크림. 유진님이 크림을 기본으로 고르셨다.
   🔴 «처음 그리기 전» 판 고르기는 각 페이지 <head> 의 인라인 한 줄이 한다(번쩍임 방지).
      이 파일은 «누르는 단추»와 «기억»만 맡는다. 홈·개인정보처리방침·이용약관이 같이 쓴다.
   🔴 저장소(localStorage)는 막혀 있을 수 있다(사생활 창 · 차단 설정) — 읽기·쓰기 모두 try 로 감싸고,
      실패하면 조용히 그 자리 판만 바뀌고 기억은 안 한다. */
(function () {
  'use strict';
  var root = document.documentElement;
  var KEY = 'yd-theme';

  function 지금() { return root.getAttribute('data-theme') === 'dark' ? 'dark' : 'light'; }

  function 칠하기() {
    var t = 지금();
    var meta = document.querySelector('meta[name="theme-color"]');
    /* 주소창 색(모바일) — 색을 여기 적지 않고 CSS 의 --bg 를 «읽어» 쓴다 (색은 CSS 변수 한 곳에만) */
    var bg = getComputedStyle(root).getPropertyValue('--bg').trim();
    if (meta && bg) meta.setAttribute('content', bg);
    [].forEach.call(document.querySelectorAll('[data-theme-toggle]'), function (b) {
      /* 단추에는 «누르면 갈 판»을 적는다 — 크림일 때 DARK, 먹일 때 LIGHT.
         🔴 5차 — 이름(aria-label)도 같이 바꾼다. 보이는 글씨로 시작한다(WCAG 2.5.3) · 폰에서는 글씨가 숨어도 이름은 남는다 */
      var 갈곳 = t === 'dark' ? 'LIGHT' : 'DARK';
      var l = b.querySelector('.theme-label');
      if (l) l.textContent = 갈곳;
      b.setAttribute('aria-label', t === 'dark' ? 'LIGHT · 라이트 모드로 바꾸기' : 'DARK · 다크 모드로 바꾸기');
      b.setAttribute('data-now', t);
    });
  }

  function 바꾸기(t) {
    /* 🔴 5차 — 바꾸는 «그 한 순간»만 움직임을 끈다(.theme-switching → styles.css). 색마다 늦게 따라와 얼룩지지 않게.
       다음 프레임에 뗀다 — 그 뒤의 hover·열림 움직임은 그대로다 */
    root.classList.add('theme-switching');
    root.setAttribute('data-theme', t);
    try { localStorage.setItem(KEY, t); } catch (e) { /* 막혀 있으면 기억만 못 한다 */ }
    칠하기();
    var 떼기 = function () { root.classList.remove('theme-switching'); };
    if (window.requestAnimationFrame) requestAnimationFrame(function () { requestAnimationFrame(떼기); });
    else setTimeout(떼기, 50);
  }

  document.addEventListener('click', function (ev) {
    var b = ev.target.closest && ev.target.closest('[data-theme-toggle]');
    if (!b) return;
    ev.preventDefault();
    바꾸기(지금() === 'dark' ? 'light' : 'dark');
  });

  /* 다른 탭에서 바꾸면 이 탭도 따라간다 */
  window.addEventListener('storage', function (ev) {
    if (ev.key !== KEY) return;
    root.setAttribute('data-theme', ev.newValue === 'dark' ? 'dark' : 'light');
    칠하기();
  });

  /* 🔴 제목 글꼴 «제안» 스위치 (2026-09-25 4차) — 기본은 주아(홈페이지-규칙 §3 · 유진님 「배달의 민족 주아로 가자」).
     주소 끝에 ?font=serif 를 붙인 사람에게만 명조(Noto Serif KR)로 «미리 보기»를 보여준다. 기억하지 않는다 —
     주소에서 떼면 바로 주아다. 규칙 §3 이 바뀌기 전에는 이 스위치를 기본으로 켜지 않는다. */
  try {
    if (/[?&]font=serif(&|$)/.test(location.search)) {
      var l = document.createElement('link');
      l.rel = 'stylesheet';
      l.href = 'https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@600;900&display=swap';
      document.head.appendChild(l);
      root.setAttribute('data-font', 'serif');
    }
  } catch (e) { /* 주소를 못 읽으면 주아 그대로 */ }

  /* 🔴 레터링 제호 «제안» 스위치 (5차) — 홈 <head> 의 인라인 한 줄이 먼저 켠다(번쩍임 없이). 여기는 받침이다.
     ?font=serif 처럼 기억하지 않는다. 기본 제호는 주아 활자(규칙 §3) — 유진님이 §3 을 바꾸시기 전에는 기본으로 켜지 않는다. */
  try {
    if (/[?&]masthead=lettering(&|$)/.test(location.search)) root.setAttribute('data-masthead', 'lettering');
  } catch (e) { /* 주소를 못 읽으면 주아 그대로 */ }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', 칠하기);
  else 칠하기();
})();
