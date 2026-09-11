# -*- coding: utf-8 -*-
"""index.html 생성기.

  python3 build.py

읽는 것 : data/sections.json (칸 목록 = 메뉴 + 화면) · data/editions.json (편별 링크표)
쓰는 것 : index.html

🔴 index.html 을 손으로 고치지 않는다. 여기를 고치고 다시 돌린다.
🔴 편별 주소도 손으로 적지 않는다 — data/editions.json 은 작업 저장소의
   scripts/build-site-editions.py 가 게시 기록에서 «읽어» 만든다.

새 편이 올라간 뒤 (두 줄):
  python3 ~/projects/yesterdigest/scripts/build-site-editions.py
  python3 ~/projects/yesterdigest-site/build.py

새 «칸»(주식 동향·연구 이력)을 열 때:
  ① data/sections.json 에서 그 칸의 "보임" 을 true 로  → 메뉴에 «자동으로» 나온다
  ② 종류가 "화면"이면 아래 SECTION_BUILDERS 에 같은 id 로 함수를 등록
  ③ python3 build.py
"""
import datetime, html, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
YT_CHANNEL = 'https://www.youtube.com/@yesterdigest'
IG_ACCOUNT = 'https://www.instagram.com/yesterdigest/'
CHARACTER = '한입이'          # 유진님 2026-09-12 08:00 「한입이로 하자」

WD = ['월', '화', '수', '목', '금', '토', '일']

IC = {
 'yt': '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M23.5 6.2a3 3 0 0 0-2.1-2.1C19.5 3.6 12 3.6 12 3.6s-7.5 0-9.4.5A3 3 0 0 0 .5 6.2C0 8.1 0 12 0 12s0 3.9.5 5.8a3 3 0 0 0 2.1 2.1c1.9.5 9.4.5 9.4.5s7.5 0 9.4-.5a3 3 0 0 0 2.1-2.1c.5-1.9.5-5.8.5-5.8s0-3.9-.5-5.8zM9.6 15.6V8.4l6.2 3.6-6.2 3.6z"/></svg>',
 'ig': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="2.5" y="2.5" width="19" height="19" rx="5.4"/><circle cx="12" cy="12" r="4.2"/><circle cx="17.6" cy="6.4" r="1.2" fill="currentColor" stroke="none"/></svg>',
 'go': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h13M13 6l6 6-6 6"/></svg>',
 'prev': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M15 5l-7 7 7 7"/></svg>',
 'next': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 5l7 7-7 7"/></svg>',
 'menu': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>',
 'x': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>',
 'out': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/></svg>',
}


def e(s):
    return html.escape(str(s), quote=True)


def pretty(d):
    y, m, day = d.split('-')
    wd = WD[datetime.date(int(y), int(m), int(day)).weekday()]
    return '%s년 %s월 %s일' % (y, int(m), int(day)), wd


def cta_band(제목='전체는 계정에서 봐요.', 설명='매일 아침 7시에 새 편이 올라갑니다. 팔로우해 두면 놓치지 않아요.'):
    """계정으로 넘어가는 띠 — 화면마다 «끝»에 붙는다. 이 페이지의 목적이다."""
    return """      <section class="cta-band" aria-label="계정 바로가기">
        <div class="cta-inner">
          <img class="cta-char" src="/assets/brand/character-wave.png" alt="" width="780" height="780" loading="lazy">
          <div>
            <h2>%(제목)s</h2>
            <p>%(설명)s</p>
            <div class="cta-actions">
              <a class="btn btn-ig btn-xl" href="%(IG)s" target="_blank" rel="noopener">%(icig)s Instagram 팔로우 %(icgo)s</a>
              <a class="btn btn-yt btn-xl" href="%(YT)s" target="_blank" rel="noopener">%(icyt)s YouTube 구독 %(icgo)s</a>
            </div>
          </div>
        </div>
      </section>""" % dict(제목=e(제목), 설명=e(설명), IG=IG_ACCOUNT, YT=YT_CHANNEL,
                            icig=IC['ig'], icyt=IC['yt'], icgo=IC['go'])


# ── 화면(칸) ───────────────────────────────────────────────────────
def view_yesterdigest(cfg, data):
    """들어오면 처음 보이는 화면 — 손 흔드는 한입이가 맞이하고, 바로 계정 버튼."""
    return """      <section class="hero" aria-labelledby="hero-title">
        <div class="hero-inner">
          <div>
            <p class="name-chip"><img src="/assets/brand/logo-256.png" alt=""><span>안녕하세요, <b>%(CH)s</b>예요</span></p>
            <h1 id="hero-title">어제의 이슈를<br><span class="accent">한입에.</span></h1>
            <p class="hero-lead">
              놓치기 쉬운 어제의 뉴스를 골라, 사실을 확인하고, 한입 크기로 만듭니다.
              <b>매일 아침 7시</b> Instagram과 YouTube에 올라가요.
            </p>
            <div class="hero-actions">
              <a class="btn btn-ig btn-xl" href="%(IG)s" target="_blank" rel="noopener">%(icig)s Instagram 보러가기 %(icgo)s</a>
              <a class="btn btn-yt btn-xl" href="%(YT)s" target="_blank" rel="noopener">%(icyt)s YouTube 보러가기 %(icgo)s</a>
            </div>
            <p class="hero-sub"><a href="#editions" data-view="editions">지난 편 훑어보기 →</a></p>
          </div>
          <div class="hero-art">
            <!-- 정지 PNG 가 기본. 움직임을 마다하지 않는 환경에서만 home.js 가 GIF 로 바꾼다.
                 GIF 가 안 뜨면 PNG 로 되돌린다. 브랜드 캐릭터라 「AI 생성 참고 이미지」 표기는 붙이지 않는다
                 (2026-09-11 22:05 유진님 「안붙임.」) -->
            <img id="hero-char" src="/assets/brand/character-wave.png"
                 data-motion="/assets/brand/character-wave.gif"
                 width="780" height="780" alt="손을 흔드는 %(CH)s">
          </div>
        </div>
      </section>

%(cta)s

      <section class="section" aria-labelledby="about-title">
        <div class="section-heading reveal">
          <p class="eyebrow">What we do</p>
          <h2 id="about-title">뉴스를 고르고, 확인하고, 한입 크기로 전합니다.</h2>
          <p>
            YesterDigest는 뉴스 콘텐츠 제작과 게시를 돕는 운영자용 시스템입니다.
            일반 방문자에게 Google 로그인을 요구하거나 계정을 수집하지 않습니다.
          </p>
        </div>
        <div class="steps reveal">
          <article class="card">
            <span class="step-number" aria-hidden="true">1</span>
            <h3>주요 이슈 선별</h3>
            <p>공식 자료와 복수의 보도를 바탕으로 전날의 핵심 이슈를 선별하고 사실관계를 확인합니다.</p>
          </article>
          <article class="card">
            <span class="step-number" aria-hidden="true">2</span>
            <h3>콘텐츠 제작</h3>
            <p>선별한 이슈를 세로형 영상과 카드뉴스에 맞춰 간결하고 이해하기 쉬운 형식으로 제작합니다.</p>
          </article>
          <article class="card">
            <span class="step-number" aria-hidden="true">3</span>
            <h3>검토 후 게시</h3>
            <p>사람이 정확성·저작권·표현을 최종 확인한 뒤 공식 API를 통해 채널에 게시하고 관리합니다.</p>
          </article>
        </div>
      </section>

      <!-- Google OAuth — API 심사에 쓰이는 절. 지우거나 메뉴 밖으로 숨기지 않는다 -->
      <section class="data-section" aria-labelledby="oauth-title">
        <div class="data-inner">
          <div>
            <p class="eyebrow">Google OAuth</p>
            <h2 id="oauth-title">Google 권한은 채널 운영에만 사용합니다.</h2>
            <p>
              YesterDigest는 운영자가 소유한 YouTube 채널에 영상을 업로드하고,
              필요한 경우 게시한 영상을 관리하기 위해 Google OAuth를 사용합니다.
            </p>
            <p class="trust-note">Google 사용자 데이터를 판매하거나 광고 목적으로 제공하지 않습니다.</p>
          </div>
          <div class="data-list">
            <div class="data-item">
              <strong>YouTube 업로드</strong>
              <p>검토가 끝난 영상을 운영자의 YouTube 채널에 업로드합니다.</p>
            </div>
            <div class="data-item">
              <strong>게시물 관리</strong>
              <p>시스템을 통해 게시한 영상의 상태를 확인하고 필요한 경우 삭제합니다.</p>
            </div>
            <div class="data-item">
              <strong>제한된 보관</strong>
              <p>인증정보는 공개 홈페이지나 공개 저장소에 저장하지 않으며 운영 환경에서만 보호해 보관합니다.</p>
            </div>
          </div>
        </div>
      </section>

      <section class="section" aria-labelledby="contact-title">
        <div class="contact-panel reveal">
          <div>
            <h2 id="contact-title">문의 및 데이터 삭제 요청</h2>
            <p>서비스, 개인정보, Google 계정 접근 권한 또는 데이터 삭제와 관련해 문의할 수 있습니다.</p>
          </div>
          <a class="contact-email" href="mailto:yesterdigest@gmail.com">yesterdigest@gmail.com</a>
        </div>
      </section>""" % dict(CH=CHARACTER, IG=IG_ACCOUNT, YT=YT_CHANNEL,
                            icig=IC['ig'], icyt=IC['yt'], icgo=IC['go'],
                            cta=cta_band())


def view_editions(cfg, data):
    """지난 편 — «표지 한 장»씩만. 나머지는 계정에서 본다."""
    slides = []
    for ed in data['editions']['편']:
        d = ed['날짜']
        title, wd = pretty(d)
        color = ed.get('요일색') or '#FCB424'
        topics = ''.join('<li>%s</li>' % e(t) for t in ed.get('이슈', []))
        ig = ed.get('인스타_카드') or ed.get('인스타_릴스') or IG_ACCOUNT
        yt = ed.get('유튜브') or YT_CHANNEL
        릴스있음 = bool(ed.get('인스타_릴스'))
        더보기 = ('카드 %d장 전체와 릴스 1편은 계정에서 봅니다.' if 릴스있음
                  else '카드 %d장 전체는 계정에서 봅니다.') % ed.get('카드수', 0)

        slides.append("""          <article class="ed" style="--accent: %(color)s">
            <a class="ed-cover" href="%(ig)s" target="_blank" rel="noopener"
               aria-label="%(title)s 카드뉴스를 Instagram에서 보기">
              <!-- 이 화면은 처음엔 숨어 있다. display:none 이어도 브라우저는 src 를 받아버리므로
                   (실측: 표지 3장 317KB 가 첫 화면에서 받아졌다) 화면이 열릴 때 home.js 가 붙인다.
                   JS 가 없으면 아래 noscript 로 그대로 보인다. -->
              <img data-src="%(cover)s" width="720" height="900" decoding="async"
                   alt="%(title)s 어제한입 카드뉴스 표지">
              <noscript><img src="%(cover)s" width="720" height="900" alt="%(title)s 어제한입 카드뉴스 표지"></noscript>
              <span class="ed-peek">표지 미리보기</span>
            </a>
            <div class="ed-body">
              <p class="ed-date"><span class="ed-dot" aria-hidden="true"></span>%(title)s <small>(%(wd)s)</small></p>
              <ul class="ed-topics">%(topics)s</ul>
              <p class="ed-more">%(more)s</p>
              <div class="ed-cta">
                <a class="btn btn-ig" href="%(ig)s" target="_blank" rel="noopener">%(icig)s Instagram에서 보기 %(icgo)s</a>
                <a class="btn btn-yt" href="%(yt)s" target="_blank" rel="noopener">%(icyt)s YouTube에서 보기 %(icgo)s</a>
              </div>
            </div>
          </article>""" % dict(color=color, ig=ig, yt=yt, cover=ed['표지'], title=title,
                               wd=wd, topics=topics, more=더보기,
                               icig=IC['ig'], icyt=IC['yt'], icgo=IC['go']))

    return """      <section class="section">
        <div class="section-heading reveal">
          <p class="eyebrow">Daily 07:00</p>
          <h2>%(제목)s</h2>
          <p>어제의 이슈 네댓 개를 카드뉴스 한 벌과 세로 영상 한 편으로 만듭니다.
             여기서는 <b>표지 한 장</b>만 보여드려요 — 전체는 Instagram과 YouTube에 있습니다.</p>
        </div>
        <div class="carousel reveal">
          <button class="nav-arrow prev" type="button" aria-label="이전 편">%(prev)s</button>
          <div class="track" aria-label="지난 편">
%(slides)s
          </div>
          <button class="nav-arrow next" type="button" aria-label="다음 편">%(next)s</button>
        </div>
        <div class="dots" aria-label="편 위치"></div>
      </section>

%(cta)s""" % dict(제목=e(cfg['제목']), slides='\n'.join(slides),
                   prev=IC['prev'], next=IC['next'],
                   cta=cta_band('더 보려면 계정으로.',
                                '카드 전체와 릴스는 Instagram·YouTube에 있습니다.'))


SECTION_BUILDERS = {
    'yesterdigest': view_yesterdigest,
    'editions': view_editions,
    # 'stocks': view_stocks,   ← 주식 동향 칸을 열 때 여기에 등록한다
    # 'cv':     view_cv,       ← 연구 이력 칸을 열 때 여기에 등록한다
}


# ── 페이지 ─────────────────────────────────────────────────────────
def build():
    sections = json.load(open(os.path.join(HERE, 'data/sections.json'), encoding='utf-8'))
    editions = json.load(open(os.path.join(HERE, 'data/editions.json'), encoding='utf-8'))
    data = {'editions': editions}

    보이는칸 = [c for c in sections['칸'] if c.get('보임')]
    화면 = [c for c in 보이는칸 if c.get('종류') == '화면']
    if not 화면:
        raise SystemExit('보임:true 인 «화면» 칸이 하나도 없다.')
    기본 = next((c['id'] for c in 화면 if c.get('기본')), 화면[0]['id'])

    menu, views = [], []
    for c in 보이는칸:
        if c.get('종류') == '바깥':
            menu.append('        <a class="menu-item" href="%s">%s <span class="menu-out">%s</span></a>'
                        % (e(c['주소']), e(c['제목']), IC['out']))
            continue
        fn = SECTION_BUILDERS.get(c['id'])
        if not fn:
            raise SystemExit('칸 "%s" 은 보임:true 인데 만드는 함수가 없다. '
                             'build.py 의 SECTION_BUILDERS 에 등록해라.' % c['id'])
        menu.append('        <a class="menu-item" href="#%s" data-view="%s"%s>%s</a>'
                    % (e(c['id']), e(c['id']),
                       ' aria-current="page"' if c['id'] == 기본 else '', e(c['제목'])))
        views.append('    <section class="view%s" id="view-%s" data-view="%s">\n%s\n    </section>'
                     % (' is-active' if c['id'] == 기본 else '', e(c['id']), e(c['id']), fn(c, data)))

    자리 = ['  <!-- 자리: %s (%s) — data/sections.json 에서 "보임": true 로 켜면 메뉴와 화면에 자동으로 나온다 -->'
            % (c['id'], c['제목']) for c in sections['칸'] if not c.get('보임')]

    page = PAGE % dict(
        YT=YT_CHANNEL, IG=IG_ACCOUNT, CH=CHARACTER, 기본=기본,
        icyt=IC['yt'], icig=IC['ig'], icmenu=IC['menu'], icx=IC['x'],
        menu='\n'.join(menu), views='\n\n'.join(views), 자리='\n'.join(자리))
    open(os.path.join(HERE, 'index.html'), 'w', encoding='utf-8').write(page)
    print('index.html — 화면 %d개 · 메뉴 %d줄 · 자리만 %d개 (기본 화면: %s)'
          % (len(views), len(menu), len(자리), 기본))


PAGE = """<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>%(CH)s | YesterDigest</title>
  <meta name="description" content="캐릭터 %(CH)s가 전하는 이야기. 어제의 뉴스를 한입 크기로 — 매일 아침 7시 Instagram과 YouTube에 올라갑니다.">
  <meta name="theme-color" content="#0C3054">
  <meta property="og:type" content="website">
  <meta property="og:title" content="%(CH)s | YesterDigest">
  <meta property="og:description" content="어제의 뉴스를 한입 크기로. 매일 아침 7시.">
  <meta property="og:image" content="https://yesterdigest.com/assets/brand/logo-256.png">
  <meta property="og:url" content="https://yesterdigest.com/">
  <link rel="icon" href="/assets/logo.png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400..900&display=swap">
  <link rel="stylesheet" href="/assets/styles.css">
  <link rel="stylesheet" href="/assets/home.css">
</head>
<body data-default-view="%(기본)s">
  <a class="skip-link" href="#main">본문으로 건너뛰기</a>

  <header class="site-header">
    <nav class="nav" aria-label="주요 메뉴">
      <button class="menu-btn" type="button" id="menu-open"
              aria-label="메뉴 열기" aria-expanded="false" aria-controls="drawer">%(icmenu)s</button>
      <a class="brand-link" href="#%(기본)s" data-view="%(기본)s" aria-label="처음 화면으로">
        <img src="/assets/brand/logo-256.png" alt="">
        <span>%(CH)s<small>YesterDigest</small></span>
      </a>
      <div class="nav-actions">
        <a class="icon-link ig" href="%(IG)s" target="_blank" rel="noopener" aria-label="Instagram 계정 열기">%(icig)s</a>
        <a class="icon-link yt" href="%(YT)s" target="_blank" rel="noopener" aria-label="YouTube 채널 열기">%(icyt)s</a>
      </div>
    </nav>
  </header>

  <!-- 목록 — data/sections.json 의 «보임: true» 인 칸만 나온다 -->
  <div class="drawer-backdrop" id="drawer-backdrop" hidden></div>
  <aside class="drawer" id="drawer" hidden aria-label="화면 목록">
    <div class="drawer-head">
      <span class="drawer-title">메뉴</span>
      <button class="menu-btn" type="button" id="menu-close" aria-label="메뉴 닫기">%(icx)s</button>
    </div>
    <nav class="drawer-nav">
%(menu)s
    </nav>
    <div class="drawer-foot">
      <a class="btn btn-ig" href="%(IG)s" target="_blank" rel="noopener">%(icig)s Instagram</a>
      <a class="btn btn-yt" href="%(YT)s" target="_blank" rel="noopener">%(icyt)s YouTube</a>
    </div>
  </aside>

  <main id="main">
%(views)s
  </main>

%(자리)s

  <footer class="site-footer">
    <div class="footer-inner">
      <p>© 2026 YesterDigest</p>
      <div class="footer-links">
        <a href="%(IG)s" target="_blank" rel="noopener">Instagram</a>
        <a href="%(YT)s" target="_blank" rel="noopener">YouTube</a>
        <a href="/privacy/">개인정보처리방침</a>
        <a href="/terms/">이용약관</a>
        <a href="mailto:yesterdigest@gmail.com">문의</a>
      </div>
    </div>
  </footer>

  <script src="/assets/home.js" defer></script>
</body>
</html>
"""

if __name__ == '__main__':
    build()
