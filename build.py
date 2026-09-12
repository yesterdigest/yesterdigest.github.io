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
import datetime, html, json, os, re, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
YT_CHANNEL = 'https://www.youtube.com/@yesterdigest'
IG_ACCOUNT = 'https://www.instagram.com/yesterdigest/'
CHARACTER = '한입이'          # 유진님 2026-09-12 08:00 「한입이로 하자」

WD = ['월', '화', '수', '목', '금', '토', '일']
# 영문 딱지용 — 유진님 2026-09-12 10:30 「홈페이지는 영어를 적절히 활용해줘」.
# 🔴 «읽지 않아도 되는 것»만 영어다 (날짜 표기·절 제목·단추). 읽어야 하는 말은 한글로 둔다.
EN_MON = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
EN_WD = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']

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


def en_date(d):
    """「SEP 11, 2026」·「FRI」 — 영문 딱지용."""
    y, m, day = [int(x) for x in d.split('-')]
    return '%s %d, %d' % (EN_MON[m - 1], day, y), EN_WD[datetime.date(y, m, day).weekday()]


# 🔴 「전체는 계정에서 봐요.」 띠는 2026-09-12 09:09 유진님 지시로 없앴다.
#    「지금 너무 인스타 유튜브로 이어지는 링크가 겹쳐... 둘중 하나만 살리자.」
#    → 첫 화면의 단추 둘만 남긴다. 편 카드 안의 단추는 «그 편 게시물»로 가는 것이라 겹치지 않아 그대로 둔다.
#    되살리려면 이 자리에 cta_band() 를 다시 만들고 화면 함수에서 부르면 된다.

def 기기목업(그림, alt, 재생=False, 주소=None, 설명=None):
    """스마트폰 «그림» 안에 우리 화면을 넣는다.

    🔴 테두리는 CSS 로 직접 그린다(.device). 남의 기기 사진·남의 앱 화면 캡처를 쓰지 않는다 (§3.6).
    🔴 2026-09-12 개편 — 유진님 11:19 「실제 shorts표현과 릴스표현을 사실화하면 좋겠어」.
       «진짜 폰처럼» 보이게 하는 것이지 «그 앱을 똑같이 그리는» 것이 아니다.
         해도 되는 것 : 세로 비율 · 둥근 모서리 · 재생 삼각형 · 진행 막대 · 위아래 어두운 그라데이션
                        · 오른쪽 세로 아이콘 «자리» · 아래 캡션 «자리» 같은 일반적인 형태
         🔴 하면 안 되는 것 : Instagram·YouTube 의 고유 UI·아이콘·글꼴·색 체계를 복제하는 것
       그래서 오른쪽 줄과 캡션은 «알아볼 수 있는 그림»이 아니라 «빈 동그라미와 막대»다.
    🔴 유진님 11:19 「누르면 각 디테일한 페이지로 이동하도록」 — 기기 전체가 링크다.
       키보드로도 닿아야 해서 <a> 로 감싼다.
    """
    재생표 = ('<span class="device-play" aria-hidden="true">'
              '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg></span>'
              '<span class="device-bar" aria-hidden="true"><i></i></span>') if 재생 else ''
    겉 = ('<a class="device-link" href="%s" target="_blank" rel="noopener" aria-label="%s">'
          % (e(주소), e(설명 or alt))) if 주소 else '<div class="device-link">'
    겉닫 = '</a>' if 주소 else '</div>'
    return """%(겉)s
                <div class="device%(릴)s">
                  <span class="device-slit" aria-hidden="true"></span>
                  <div class="device-screen">
                    <div class="device-top">
                      <img src="/assets/brand/logo-256.png" alt="" width="40" height="40">
                      <span>@yesterdigest</span>
                      <i class="device-dots" aria-hidden="true"></i>
                    </div>
                    <div class="device-media">
                      <img data-src="%(그림)s" alt="%(alt)s">
                      <span class="device-scrim" aria-hidden="true"></span>
                      <span class="device-rail" aria-hidden="true"><i></i><i></i><i></i></span>
                      %(재생표)s
                    </div>
                    <span class="device-cap" aria-hidden="true"><i></i><i></i></span>
                  </div>
                </div>
              %(겉닫)s""" % dict(겉=겉, 겉닫=겉닫, 릴=' device--reel' if 재생 else '',
                                 그림=그림, alt=e(alt), 재생표=재생표)


def hero_deco():
    """첫 화면 «가장자리»를 채우는 것들 — 전부 장식이라 읽는 기계에는 안 보인다.

    🔴 2026-09-12 두 번째 판. 유진님 11:19 「뒷배경이 너무 아재같아」.
       첫 판은 «흐린 큰 원 · 격자선 · 빛 번짐»이었다. 그게 «아재»로 읽힌 어휘다 —
       2010년대 SaaS 첫 화면의 결이다. **그 셋을 다시 쓰지 않는다.**

    이번 어휘는 «부드럽게 번지는 것»이 아니라 «또렷한 구조»다.
      · 속이 빈 거대한 글자(테두리만) — 가장자리를 넘어 걸친다
      · 비스듬히 가로지르는 «날이 선» 띠 (앰버 실선 한 줄)
      · 등고선 — 1px 동심원. 흐린 원과 정반대다
      · 모서리를 잡아주는 «ㄱ자» 선과 작은 네모
      · 옅은 알갱이 (평평한 색이 싸 보이는 것만 막는다)
    🔴 우리 유튜브 채널 아트의 결(꽉 찬 동그라미·짧은 막대·점 무리)도 그대로 금지다 (10:21).
    🔴 색은 남색 + 앰버 둘뿐. 늘리지 않는다.
    """
    return """        <div class="hero-deco" aria-hidden="true">
          <span class="band"></span>
          <span class="contour"></span>
          <span class="wordmark">YESTERDIGEST</span>
          <span class="corner corner-tl"></span>
          <span class="corner corner-br"></span>
          <span class="node node-a"></span>
          <span class="node node-b"></span>
          <span class="grain"></span>
        </div>"""


def ticker():
    """첫 화면 맨 아래 «흐르는 띠». 우리 말만 쓴다.

    🔴 같은 내용을 «두 번» 넣는다 — 애니메이션이 -50% 로 밀기 때문에 그래야 이음매가 안 보인다.
    """
    한판 = ('어제한입 <b>&#183;</b> YESTERDIGEST <b>&#183;</b> 매일 아침 7시 '
            '<b>&#183;</b> 시간은 금이다 <b>&#183;</b> ') * 3
    return ('        <div class="ticker" aria-hidden="true"><div class="ticker-run">'
            '<span>%s</span><span>%s</span></div></div>' % (한판, 한판))


def showcase(editions):
    """첫 화면 — 가만히 두면 «일정 시간마다» 장이 바뀐다 (유진님 2026-09-12 09:26 · 09:48).

    장은 data/showcase.json 에서 온다. 「보임: true」인 것만 나오고, 하나를 더하면
    점 표시·자동 넘김·손가락 넘김이 «저절로» 따라온다 — 나중에 CV·자동화 매매를 한 장씩 붙이려고
    이렇게 짰다. 한 장에는 그 계정 «하나»의 단추만 둔다(한 화면에 계정 단추가 겹치지 않게 · 09:09).
    """
    sc = json.load(open(os.path.join(HERE, 'data/showcase.json'), encoding='utf-8'))
    장 = [c for c in sc['장'] if c.get('보임')]
    if not 장:
        raise SystemExit('data/showcase.json 에 보임:true 인 장이 없다.')

    최신 = editions['편'][0] if editions.get('편') else {}
    표지 = 최신.get('표지')
    릴스 = '/assets/reel/%s.jpg' % 최신.get('날짜', '')
    if not os.path.exists(os.path.join(HERE, 릴스.lstrip('/'))):
        릴스 = 표지                       # 릴스 표지 그림이 없으면 카드 표지로 대신한다

    단추종류 = {
        'youtube': ('btn-yt', IC['yt'], 'YouTube 보러가기', YT_CHANNEL),
        'instagram': ('btn-ig', IC['ig'], 'Instagram 보러가기', IG_ACCOUNT),
    }

    패널 = []
    for i, c in enumerate(장):
        머리 = ''
        if c.get('칩'):
            머리 = ('<p class="name-chip"><img src="/assets/brand/logo-256.png" alt="">'
                    '<span><b>%s</b></span></p>' % e(c['칩']))
        elif c.get('눈금'):
            머리 = '<p class="eyebrow">%s</p>' % e(c['눈금'])
        if c.get('시각칩'):
            # 「매일 아침 7시」는 «약속»이라 2·3장에만 작게 (1장 모토와 섞지 않는다)
            머리 += '<p class="when-chip">%s</p>' % e(c['시각칩'])

        줄 = []
        for n, t in enumerate(c['제목줄']):
            if not t:
                continue
            줄.append('<span class="accent">%s</span>' % e(t) if n == c.get('강조줄') else e(t))
        제목 = '<br>'.join(줄)

        # 🔴 모토는 «두 줄까지». 큰 줄은 제목(h1)이고, 이 받침이 둘째 줄이다.
        #    근거는 data/showcase.json 의 _문구_근거 에 적어 뒀다 — 지어낸 말이 아니다.
        모토 = ('<p class="motto-sub">%s</p>' % e(c['받침'])) if c.get('받침') else ''

        단추 = ''
        if c.get('단추'):
            cls, icon, 글, 주소 = 단추종류[c['단추']]
            단추 = ('<div class="hero-actions"><a class="btn %s btn-xl" href="%s" target="_blank" rel="noopener">'
                    '%s %s %s</a></div>' % (cls, 주소, icon, e(글), IC['go']))

        if c['그림'] == '로고':
            그림 = ('<div class="hero-art"><img id="hero-char" src="/assets/brand/character-wave.png" '
                    'data-motion="/assets/brand/character-wave.gif" width="780" height="780" '
                    'alt="손을 흔드는 %s"></div>' % e(CHARACTER))
        elif c['그림'] == '카드목업' and 표지:
            # 🔴 누르면 «그 편» 게시물로 (유진님 11:19). 편별 주소가 없으면 계정으로 떨어진다.
            그림 = ('<div class="hero-art hero-art-device">%s</div>'
                    % 기기목업(표지, '가장 최근 편 카드뉴스 표지',
                               주소=최신.get('인스타_카드') or IG_ACCOUNT,
                               설명='가장 최근 편 카드뉴스를 Instagram에서 보기'))
        elif c['그림'] == '릴스목업' and 릴스:
            그림 = ('<div class="hero-art hero-art-device">%s</div>'
                    % 기기목업(릴스, '가장 최근 편 릴스 표지', 재생=True,
                               주소=최신.get('유튜브') or YT_CHANNEL,
                               설명='가장 최근 편 영상을 YouTube에서 보기'))
        else:
            그림 = ''

        패널.append("""          <article class="sc-panel%(on)s" id="sc-%(id)s" data-sc="%(id)s"%(hidden)s>
            <div class="hero-inner">
              <div class="hero-text">
                %(머리)s
                <h1>%(제목)s</h1>
                %(모토)s
                <p class="hero-lead">%(설명)s</p>
                %(단추)s
              </div>
              %(그림)s
            </div>
          </article>""" % dict(on=' is-on' if i == 0 else '', id=e(c['id']),
                                hidden='' if i == 0 else ' aria-hidden="true"',
                                머리=머리, 제목=제목, 설명=e(c['설명']), 모토=모토,
                                단추=단추, 그림=그림))

    return """      <section class="hero showcase" data-interval="%(초d)d" aria-roledescription="carousel" aria-label="어제한입 소개">
%(장식)s
        <div class="sc-stack">
%(패널)s
        </div>
        <div class="sc-foot">
          <div class="sc-dots" role="tablist" aria-label="소개 화면 고르기"></div>
          <p class="hero-sub">
            <a href="#editions" data-view="editions">Latest drops <span aria-hidden="true">&#8595;</span></a>
            <!-- 🔴 소개 영상 «자리»다. 영상 파일은 아직 없다 (팀장 2026-09-12: 오늘은 렌더를 안 돌린다).
                 여기서 만들어 두는 것은 «움직임»이다 — 누르면 커지고, 닫으면 줄어든다.
                 영상이 생기면 intro_modal() 안의 .intro-slot 에 <video> 를 넣기만 하면 된다. -->
            <button class="intro-btn" type="button" id="intro-open" aria-haspopup="dialog">
              <span class="intro-play" aria-hidden="true"></span>INTRO
            </button>
          </p>
        </div>
%(띠)s
      </section>""" % dict(초d=int(sc.get('넘김초', 4)) * 1000, 패널='\n'.join(패널),
                            장식=hero_deco(), 띠=ticker())


# ── 화면(칸) ───────────────────────────────────────────────────────
def view_yesterdigest(cfg, data):
    """들어오면 처음 보이는 화면 — 첫 화면(자동으로 바뀌는 장) + 하는 일 + 문의."""
    return showcase(data['editions']) + """

      <section class="section" aria-labelledby="about-title">
        <div class="section-inner">
          <div class="section-heading reveal">
            <p class="eyebrow">What we do</p>
            <h2 id="about-title">고르고,<br>확인하고,<br>한입 크기로.</h2>
            <!-- 🔴 여기 있던 구글 OAuth 두 문장은 «맨 아래» oauth_note() 로 옮겼다
                 (유진님 2026-09-12 08:53 「어디에 좀 안보이는곳에 둘 순없어?」 ·
                  09:48 「소개가 너무 정직해」). 지운 것이 아니라 «옮긴» 것이다 — 되돌리지 마라. -->
            <p>어제 하루를 한입 크기로 잘라, 아침 7시에 놓아둡니다.
               무엇을 골랐는지와 어떻게 확인했는지를 먼저 챙기고요.</p>
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
        </div>
      </section>
"""


def view_editions(cfg, data):
    """지난 편 — «아래로 내리면 옆으로 넘어간다».

    🔴 2026-09-12 유진님 11:19 ⑦ 「아래로 드래그하면 옆으로 넘어가면서 각 이슈를 간략하게
       제목만 행별로 적어서 지금 처럼 인스타 유튜브페이지를 누르면 딱 그 해당하는 날짜로 가도록」
       → 세로 스크롤이 «가로 이동»을 민다 (sticky + translateX). 가로 스크롤 막대는 생기지 않는다.
         폰에서도 손가락 «세로» 스크롤로 넘어간다.
    🔴 이슈 제목을 «다시» 적는다 — 앞서 「표지에 있는 것을 또 쓰지 말라」고 정리했는데,
       유진님이 11:19 에 «제목만 행별로 적어라»고 직접 말씀하셨다. 유진님 말씀이 나중이고 위다.
    🔴 인스타·유튜브 단추는 «그 날짜» 게시물로 간다 (지금도 그렇다. 그대로 둔다).
    """
    panels = []
    for i, ed in enumerate(data['editions']['편']):
        d = ed['날짜']
        title, wd = pretty(d)
        엔날짜, 엔요일 = en_date(d)
        color = ed.get('요일색') or '#FCB424'
        이슈 = ed.get('이슈', [])
        줄 = ''.join('<li><span>%02d</span>%s</li>' % (n + 1, e(t)) for n, t in enumerate(이슈))
        ig = ed.get('인스타_카드') or ed.get('인스타_릴스') or IG_ACCOUNT
        yt = ed.get('유튜브') or YT_CHANNEL
        릴스있음 = bool(ed.get('인스타_릴스'))
        더보기 = ('카드 %d장 전체와 릴스 1편은 계정에서 봅니다.' if 릴스있음
                  else '카드 %d장 전체는 계정에서 봅니다.') % ed.get('카드수', 0)

        panels.append("""            <article class="ed" style="--accent: %(color)s">
              <a class="ed-cover" href="%(ig)s" target="_blank" rel="noopener"
                 aria-label="%(title)s 카드뉴스를 Instagram에서 보기">
                <!-- 이 화면은 처음엔 숨어 있다. display:none 이어도 브라우저는 src 를 받아버리므로
                     (실측: 표지 3장 317KB 가 첫 화면에서 받아졌다) 화면이 열릴 때 home.js 가 붙인다. -->
                <img data-src="%(cover)s" width="720" height="900" decoding="async"
                     alt="%(title)s 어제한입 카드뉴스 표지">
                <noscript><img src="%(cover)s" width="720" height="900" alt="%(title)s 어제한입 카드뉴스 표지"></noscript>
              </a>
              <div class="ed-text">
                <p class="ed-day"><span class="ed-dot" aria-hidden="true"></span>%(엔날짜)s<i>%(엔요일)s</i></p>
                <ol class="ed-topics">%(줄)s</ol>
                <p class="ed-more">%(more)s</p>
                <div class="ed-cta">
                  <a class="btn btn-ig" href="%(ig)s" target="_blank" rel="noopener"
                     aria-label="%(title)s 카드뉴스를 Instagram에서 보기">%(icig)s <span>INSTAGRAM</span></a>
                  <a class="btn btn-yt" href="%(yt)s" target="_blank" rel="noopener"
                     aria-label="%(title)s 영상을 YouTube에서 보기">%(icyt)s <span>YOUTUBE</span></a>
                </div>
                <p class="sr-only">%(title)s (%(wd)s)</p>
              </div>
            </article>""" % dict(color=color, ig=ig, yt=yt, cover=ed['표지'], title=title, wd=wd,
                                 엔날짜=엔날짜, 엔요일=엔요일, 줄=줄, more=더보기,
                                 icig=IC['ig'], icyt=IC['yt']))

    return """      <section class="section section--rail">
        <div class="section-inner">
          <div class="section-heading reveal">
            <p class="eyebrow">Latest drops</p>
            <h2>%(제목)s</h2>
            <p>어제의 이슈 네댓 개를 카드뉴스 한 벌과 세로 영상 한 편으로 만듭니다.
               아래로 내리면 <b>편이 옆으로</b> 넘어가요 — 전체는 Instagram과 YouTube에 있습니다.</p>
          </div>
        </div>
        <div class="ed-rail" style="--n: %(n)d">
          <div class="ed-stage">
            <div class="ed-track">
%(panels)s
            </div>
            <div class="ed-progress" aria-hidden="true"><i></i></div>
          </div>
        </div>
      </section>""" % dict(제목=e(cfg['제목']), panels='\n'.join(panels), n=len(panels))


SECTION_BUILDERS = {
    'yesterdigest': view_yesterdigest,
    'editions': view_editions,
    # 'stocks': view_stocks,   ← 주식 동향 칸을 열 때 여기에 등록한다
    # 'cv':     view_cv,       ← 연구 이력 칸을 열 때 여기에 등록한다
}


# Jua 가 실제로 그리는 자리 (assets/home.css 의 --title-font 선택자와 «짝»이다.
# 거기에 선택자를 더하면 여기에도 더해야 한다 — 안 그러면 그 글자만 본문 글씨로 튄다)
JUA_자리 = [r'<h1[^>]*>(.*?)</h1>', r'<h2[^>]*>(.*?)</h2>', r'<h3[^>]*>(.*?)</h3>',
            r'class="brand-link"[^>]*>.*?<span>(.*?)</span>',
            r'class="drawer-title">(.*?)</span>',
            r'class="name-chip"[^>]*>(.*?)</p>']

# 날마다 바뀌는 것 — 오늘 페이지에 없어도 반드시 넣는다
JUA_바탕 = ('0123456789년월일()' + '월화수목금토일'
            + 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz' + ' .,·-~!?:')


def jua_글자(page):
    """이 페이지에서 Jua 가 그릴 글자를 모은다 → Google Fonts text= 로 넘긴다."""
    글자 = set(JUA_바탕)
    for pat in JUA_자리:
        for m in re.findall(pat, page, re.S):
            글자 |= set(re.sub(r'<[^>]+>', '', m))
    글자 -= set('\n\r\t')
    return ''.join(sorted(글자))


def intro_modal():
    """소개 영상 «틀» — 영상은 아직 없다. 움직임만 미리 만들어 둔다.

    유진님 2026-09-12 11:19 「짧은 어제한입 소개 영상을 만들어줘」 →
    팀장 판단으로 «영상 만들기»는 오늘 안 한다(렌더가 이 기계의 메모리를 크게 쓴다).
    🔴 대신 «누르면 커졌다가 끝나면 줄어드는» 움직임과 자리를 오늘 만들어 둔다.
       영상이 생기면 .intro-slot 안의 내용만 <video src=... playsinline> 로 바꾸면 된다.
    🔴 자리를 비워 두되 «빈 네모»를 보여주지 않는다 — 우리 캐릭터가 대신 서 있는다.
    """
    return """  <div class="intro-modal" id="intro-modal" hidden>
    <div class="intro-box" role="dialog" aria-modal="true" aria-labelledby="intro-title">
      <button class="intro-close" type="button" id="intro-close" aria-label="닫기">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>
      </button>
      <div class="intro-slot">
        <img src="/assets/brand/character-wave.png" alt="" width="380" height="380">
        <p id="intro-title">소개 영상은 준비 중이에요</p>
        <p class="intro-sub">10초 안에 어제한입이 어떤 곳인지 보여드릴게요.</p>
      </div>
    </div>
  </div>
"""


def oauth_note():
    """Google OAuth 안내 + 문의 — «작게 · 맨 아래».

    유진님 2026-09-12 08:53 「google oauth관련된건 작게넣거나 어디에 좀 안보이는곳에 둘 순없어? 너무 깨네 저게」
             09:48 「소개가 너무 정직해」
    🔴 그래서 본문에 흩어져 있던 것을 여기 «한 자리»로 내렸다 (2026-09-12 두 번째 개편).
       ① 소개 첫 문단의 구글 두 문장  ② 「문의 및 데이터 삭제 요청」 절 통째로
    🔴 문구는 한 글자도 고치지 않는다. 심사에 쓰인 문장이다. 크기와 자리만 바꿨다.
    🔴 지우면 안 된다 — Google 의 App Homepage 요건이 «앱이 어떤 목적으로 사용자 데이터를
       요구하는지 홈페이지에서 투명하게 설명할 것»과 «개인정보처리방침 링크»를 요구한다
       (support.google.com/cloud/answer/13807376).
    🔴 메일 주소 · 개인정보처리방침 · 이용약관은 «여기서도 눌러서 갈 수 있어야» 한다.
    🔴 «작게»이지 «흐리게»가 아니다 — 글자 14px 이상, 어두운 바탕에 밝은 글자로 대비를 지킨다.
    """
    return """  <section class="oauth-note" aria-labelledby="oauth-title">
    <div class="oauth-inner reveal">
      <p class="oauth-eyebrow">Google OAuth</p>
      <h2 id="oauth-title">Google 권한은 채널 운영에만 사용합니다.</h2>
      <p class="oauth-lead">YesterDigest는 운영자가 소유한 YouTube 채널에 영상을 업로드하고,
        필요한 경우 게시한 영상을 관리하기 위해 Google OAuth를 사용합니다.</p>
      <p class="oauth-lead">YesterDigest는 뉴스 콘텐츠 제작과 게시를 돕는 운영자용 시스템입니다.
        일반 방문자에게 Google 로그인을 요구하거나 계정을 수집하지 않습니다.</p>
      <ul class="oauth-list">
        <li><strong>YouTube 업로드</strong> 검토가 끝난 영상을 운영자의 YouTube 채널에 업로드합니다.</li>
        <li><strong>게시물 관리</strong> 시스템을 통해 게시한 영상의 상태를 확인하고 필요한 경우 삭제합니다.</li>
        <li><strong>제한된 보관</strong> 인증정보는 공개 홈페이지나 공개 저장소에 저장하지 않으며 운영 환경에서만 보호해 보관합니다.</li>
      </ul>
      <p class="oauth-strong">Google 사용자 데이터를 판매하거나 광고 목적으로 제공하지 않습니다.</p>
      <div class="oauth-contact" id="contact">
        <div>
          <h3 id="contact-title">문의 및 데이터 삭제 요청</h3>
          <p>서비스, 개인정보, Google 계정 접근 권한 또는 데이터 삭제와 관련해 문의할 수 있습니다.</p>
        </div>
        <p class="oauth-links">
          <a class="oauth-mail" href="mailto:yesterdigest@gmail.com">yesterdigest@gmail.com</a>
          <a href="/privacy/">개인정보처리방침</a>
          <a href="/terms/">이용약관</a>
        </p>
      </div>
    </div>
  </section>
"""


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
        menu='\n'.join(menu), views='\n\n'.join(views), 자리='\n'.join(자리),
        intro=intro_modal(), oauth=oauth_note())
    글자 = jua_글자(page)
    page = page.replace('__JUA_TEXT__', urllib.parse.quote(글자, safe=''))
    open(os.path.join(HERE, 'index.html'), 'w', encoding='utf-8').write(page)
    print('index.html — 화면 %d개 · 메뉴 %d줄 · 자리만 %d개 (기본 화면: %s)'
          % (len(views), len(menu), len(자리), 기본))
    print('  Jua 는 글자 %d자만 받는다 (text=)' % len(글자))


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
  <!-- 글씨체 — 유진님 2026-09-12 09:01 「배달의 민족 주아로 가자」
       제목·강조 Jua · 본문 Gothic A1. 둘 다 SIL OFL 1.1 (google/fonts ofl/jua · ofl/gothica1 · METADATA license=OFL).
       🔴 배민 배포본이 아니라 «Google Fonts» 에서 받는다 — 배포처가 다르면 약관이 다르다 (CLAUDE.md §3.6).
       🔴 홈페이지에만 쓴다. 영상·카드뉴스 글씨체는 안 건드린다 (유진님 08:41). -->
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Gothic+A1:wght@400;700&display=swap">
  <!-- 영문 전용 (유진님 2026-09-12 10:30 「영어를 적절히 활용해줘」).
       🔴 주아는 한글 글씨체다 — 영문을 주아로 찍으면 어색해서 영문에만 따로 물린다.
       Inter · SIL OFL 1.1 (google/fonts ofl/inter · METADATA license=OFL) · Google Fonts 배포본.
       라틴 문자만 받는다 (latin subset) — 무게는 셋뿐이라 가볍다. -->
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@500;700;800&display=swap">
  <!-- Jua 는 «이 페이지가 실제로 쓰는 글자»만 받는다 (text=). 제목·이름·날짜에만 쓰므로 글자가 정해져 있다.
       아래 글자 목록은 build.py 가 만들어진 HTML 에서 «세어» 넣는다 — 손으로 고치지 않는다.
       숫자·년월일·요일 일곱 자는 날마다 바뀌므로 «반드시» 바탕 묶음으로 넣는다. -->
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Jua&display=swap&text=__JUA_TEXT__">
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

%(intro)s
%(oauth)s
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
