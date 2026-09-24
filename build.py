# -*- coding: utf-8 -*-
"""index.html 생성기.

  python3 build.py

읽는 것 : data/sections.json (칸 목록 = 메뉴 + 화면) · data/editions.json (편별 링크표)
쓰는 것 : index.html · sitemap.xml

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
import datetime, html, json, os, re, subprocess, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
YT_CHANNEL = 'https://www.youtube.com/@yesterdigest'
IG_ACCOUNT = 'https://www.instagram.com/yesterdigest/'
# 🔴 2026-09-24 — 대표 이름은 «어제한입 / YesterDigest» 하나다.
#    유진님 16:3x (팀장 전달) 「응 한입이라는 것도 버려도 되니까 고급스럽게」 — 정본 §2 「대표는 한입이」가 이 말씀으로 풀렸다.
#    옛 값: CHARACTER = '한입이' (2026-09-12 08:00 「한입이로 하자」) · 뺀 자리 목록 → .review/뺀것.md
BRAND = '어제한입'
# 🔴 로고 «한 줄» — 새 로고(logo-0924 · assets/brand-2026-09/final/)가 오면 이 주소만 바꾼다.
#    머리줄·서랍·바닥·폰 목업의 계정 사진이 전부 이 한 줄을 쓴다. 자리 크기는 CSS(.logo-slot)가 정한다.
# 🔴 2026-09-25 4차 — 새 로고 «베어 문 원»(B안 계열 · 자국 하나)으로 바꿨다. 먹 원판 + 머스터드 원.
#    옛 값: '/assets/brand/logo-256.png' (캐릭터 얼굴 배지). 되돌리려면 이 한 줄만 되돌린다.
#    원본: assets/brand/badge.svg(원형) · icon.svg(네모 · 파비콘) · mark.svg(원만) — 색은 배너 토큰.
LOGO_MARK = '/assets/brand/badge.svg'
# 베어 문 원 한 개 — 제호 끝의 «마침표»로 쓴다 (본 저장소 assets/brand-2026-09/final/wordmark-fusion 의 생각)
MARK_PATH = 'M69.5 9A96 96 0 1 1 9 69.5A44 44 0 0 0 69.5 9Z'


def 캐릭터(cls='', alt=''):
    """캐릭터 — assets/brand/character.svg 를 «페이지 안»에 넣는다 (판마다 색을 CSS 토큰으로 바꾸려고).

    2026-09-25 4차: 본 저장소 assets/brand-2026-09/character/d1-refined-line 을 다듬은 판.
    (선 굵기 통일 · 신문의 까만 사진 덩어리 → 테두리 칸 · 발밑 그림자 · 색은 배너 토큰)
    🔴 실존 인물 얼굴이 아니다 — 브랜드 캐릭터 그림이다.
    """
    svg = open(os.path.join(HERE, 'assets/brand/character.svg'), encoding='utf-8').read()
    svg = re.sub(r'<style>.*?</style>', '', svg, flags=re.S)
    svg = re.sub(r'<title>.*?</title>', '', svg, flags=re.S)
    svg = re.sub(r' width="\d+" height="\d+"', '', svg, count=1)
    if alt:
        svg = svg.replace('<svg ', '<svg role="img" aria-label="%s" class="ch %s" ' % (e(alt), cls), 1)
    else:
        svg = svg.replace('<svg ', '<svg aria-hidden="true" focusable="false" class="ch %s" ' % cls, 1)
    return svg.strip()

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
 'home': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linejoin="round" aria-hidden="true"><path d="M3.5 10.6 12 3.8l8.5 6.8V20a.8.8 0 0 1-.8.8h-4.4v-6h-6.6v6H4.3a.8.8 0 0 1-.8-.8z"/></svg>',
 'find': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" aria-hidden="true"><circle cx="10.6" cy="10.6" r="6.8"/><path d="M15.6 15.6 21 21"/></svg>',
 'who': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="8.2" r="4"/><path d="M4.4 20.4c1-4 4-6 7.6-6s6.6 2 7.6 6"/></svg>',
 'heart': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linejoin="round" aria-hidden="true"><path d="M12 20.2 4.6 13a4.6 4.6 0 0 1 6.5-6.5l.9.9.9-.9A4.6 4.6 0 1 1 19.4 13z"/></svg>',
 'bubble': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linejoin="round" aria-hidden="true"><path d="M4 5.5h16a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1h-8.4L7 21v-4.5H4a1 1 0 0 1-1-1v-9a1 1 0 0 1 1-1z"/></svg>',
 'share': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linejoin="round" aria-hidden="true"><path d="M3 19c.6-5.2 4.4-8 10-8V6.4L21.5 13 13 19.6V15c-4.4 0-7.6 1.2-10 4z"/></svg>',
 'mark': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linejoin="round" aria-hidden="true"><path d="M6.5 3.5h11a1 1 0 0 1 1 1v16l-6.5-4.4L5.5 20.5v-16a1 1 0 0 1 1-1z"/></svg>',
 'sun': '<svg class="ic-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4.2"/><path d="M12 2.5v2.2M12 19.3v2.2M2.5 12h2.2M19.3 12h2.2M5.3 5.3l1.6 1.6M17.1 17.1l1.6 1.6M5.3 18.7l1.6-1.6M17.1 6.9l1.6-1.6"/></svg>',
 'moon': '<svg class="ic-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round" aria-hidden="true"><path d="M20 14.6A8.2 8.2 0 0 1 9.4 4a8.2 8.2 0 1 0 10.6 10.6z"/></svg>',
 'out': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/></svg>',
}


def e(s):
    return html.escape(str(s), quote=True)


def pretty(d):
    y, m, day = d.split('-')
    wd = WD[datetime.date(int(y), int(m), int(day)).weekday()]
    return '%s년 %s월 %s일' % (y, int(m), int(day)), wd


def en_date(d):
    """「2026.09.11」·「FRI」 — 신문 지면식 날짜 (2026-09-24 · 옛 판 「SEP 11, 2026」)."""
    y, m, day = [int(x) for x in d.split('-')]
    return '%d.%02d.%02d' % (y, m, day), EN_WD[datetime.date(y, m, day).weekday()]


# 🔴 「전체는 계정에서 봐요.」 띠는 2026-09-12 09:09 유진님 지시로 없앴다.
#    「지금 너무 인스타 유튜브로 이어지는 링크가 겹쳐... 둘중 하나만 살리자.」
#    → 첫 화면의 단추 둘만 남긴다. 편 카드 안의 단추는 «그 편 게시물»로 가는 것이라 겹치지 않아 그대로 둔다.
#    되살리려면 이 자리에 cta_band() 를 다시 만들고 화면 함수에서 부르면 된다.

def 기기목업(그림, alt, 재생=False, 주소=None, 설명=None, 윗줄='', 아랫줄='', 캡션=''):
    """스마트폰 «그림» 안에 우리 화면을 넣는다.

    🔴 테두리는 CSS 로 직접 그린다(.device). 남의 기기 사진·남의 앱 화면 캡처를 쓰지 않는다 (§3.6).
    🔴 2026-09-12 3차 — 유진님 12:39 「내가 첨부한 쇼츠와 릴스 화면을 참고해서 업데이트해줘」.
       팀장이 상표 선을 «다시 그었다» (docs/reports/2026-09-12-홈페이지-3차-지시.md §상표):
         해도 되는 것 : 짜임·배치(오른쪽 세로 줄 · 왼쪽 아래 계정/제목 · 아래 진행 막대 · 설명란 자리)
                        · «보통 기호»(하트 · 말풍선 · 화살표 · 북마크 · 점 셋) · 비율과 간격의 결
         🔴 하면 안 되는 것 : 그 회사 «로고»(유튜브 재생 사각형 · 인스타 카메라) · 고유 아이콘 모양 베끼기
                              · 그 회사 글꼴·브랜드 색 체계 · 그 회사가 만든 화면이라는 오해
       🔴 2차의 «빈 동그라미 셋»은 유진님 눈에 «깨진 것»으로 보였다. 선이 너무 안쪽이었다.
    🔴 글은 «우리 것»만 넣는다 — 우리 계정명, 그날 날짜, 그날 실제 이슈 제목. 지어낸 글씨(lorem) 금지.
    🔴 유진님 11:19 「누르면 각 디테일한 페이지로 이동하도록」 — 기기 전체가 링크다.
    """
    겉 = ('<a class="device-link" href="%s" target="_blank" rel="noopener" aria-label="%s">'
          % (e(주소), e(설명 or alt))) if 주소 else '<div class="device-link">'
    겉닫 = '</a>' if 주소 else '</div>'

    def 기호(이름, 글):
        return '<span class="dv-act">%s<b>%s</b></span>' % (IC[이름], e(글))

    if 재생:
        # ── 세로 영상 판 — 그림이 화면을 꽉 채우고 그 «위에» 얹힌다
        속 = """<div class="dv-media">
                      <img data-src="%(그림)s" alt="%(alt)s">
                      <span class="dv-scrim" aria-hidden="true"></span>
                    </div>
                    <div class="dv-over" aria-hidden="true">
                      <div class="dv-rail">%(줄)s</div>
                      <div class="dv-foot">
                        <p class="dv-who"><img src="__LOGO__" alt="" width="40" height="40"><span>@yesterdigest</span><em>구독</em></p>
                        <p class="dv-title">%(윗줄)s<br>%(아랫줄)s</p>
                      </div>
                      <span class="dv-bar"><i></i></span>
                    </div>
                    <button class="dv-play" type="button" id="intro-open" aria-haspopup="dialog"
                            aria-label="어제한입 소개 영상 보기">
                      <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg>
                    </button>""" % dict(
            그림=그림, alt=e(alt), 윗줄=e(윗줄), 아랫줄=e(아랫줄),
            줄=''.join(기호(n, g) for n, g in
                       (('heart', '좋아요'), ('bubble', '댓글'), ('share', '공유'))))
    else:
        # ── 피드 한 장 판 — 계정 줄 · 그림 · 동작 줄 · 설명란
        속 = """<div class="dv-top">
                      <img src="__LOGO__" alt="" width="40" height="40">
                      <span>yesterdigest</span>
                      <i class="dv-dots" aria-hidden="true"></i>
                    </div>
                    <div class="dv-media">
                      <img data-src="%(그림)s" alt="%(alt)s">
                    </div>
                    <div class="dv-acts" aria-hidden="true">
                      %(heart)s%(bubble)s%(share)s<span class="dv-mark">%(mark)s</span>
                    </div>
                    <div class="dv-cap" aria-hidden="true">
                      <p><b>yesterdigest</b> %(윗줄)s</p>
                      <p class="dv-cap-sub">%(아랫줄)s</p>
                      <p class="dv-cap-foot">%(캡션)s</p>
                    </div>
                    <div class="dv-peek" aria-hidden="true">
                      <div class="dv-top">
                        <img src="__LOGO__" alt="" width="40" height="40">
                        <span>yesterdigest</span>
                        <i class="dv-dots"></i>
                      </div>
                      <span class="dv-peek-img"></span>
                    </div>
                    <div class="dv-nav" aria-hidden="true">%(home)s%(find)s%(heart)s%(who)s</div>""" % dict(
            그림=그림, alt=e(alt), 윗줄=e(윗줄), 아랫줄=e(아랫줄), 캡션=e(캡션),
            heart=IC['heart'], bubble=IC['bubble'], share=IC['share'], mark=IC['mark'],
            home=IC['home'], find=IC['find'], who=IC['who'])

    return """%(겉)s
                <div class="device%(릴)s">
                  <span class="device-slit" aria-hidden="true"></span>
                  <div class="device-screen">
                    %(속)s
                  </div>
                </div>
              %(겉닫)s""" % dict(겉=겉, 겉닫=겉닫, 릴=' device--reel' if 재생 else '', 속=속.replace('__LOGO__', LOGO_MARK))


def nameplate(editions, sc):
    """첫 화면 맨 위 — «신문 제호(nameplate)».

    🔴 2026-09-24 유진님 16:3x (팀장 전달)
       「웹색상은 밝은 크림시문지로 바꾸되 다크모드 기눙도 넣어줘」
       「응 촤대한 고급스럽게, 지금은 너무 유치하니까 고급화하는쪽으로가자」
       「응 한입이라는 것도 버려도 되니까 고급스럽게」
    짜임 (위에서 아래로) — 신문 1면 머리 그대로:
       날짜줄(호수 · 최신 편 날짜 · 게시 시각) → 귀(왼: 모토 · 오른: 게시 약속) + 큰 활자 제호 → 태그라인
       → 가는 이중 괘선 → 배너 «아랫줄» 보도사진 띠
    🔴 배너의 가운데 줄(옛 캐릭터 로고)은 쓰지 않는다 — 로고는 새로 만드는 중이고(logo-0924),
       옛 로고가 첫 화면 주인공이면 안 된다 (팀장 지시).
    🔴 글은 전부 «있던 말»이다: 모토 두 줄 = data/showcase.json 장 main(유진님 2026-09-06 「"시간은 금이다" 이게 내 모토야」),
       태그라인 = 배너 안 글자, 호수 = data/editions.json 의 편 수, 날짜 = 최신 편 날짜. 지어낸 말 없음.
    """
    편 = editions.get('편', [])
    최신 = 편[0] if 편 else {}
    d = 최신.get('날짜') or datetime.date.today().isoformat()
    y, m, day = [int(x) for x in d.split('-')]
    요일 = EN_WD[datetime.date(y, m, day).weekday()]
    main = next((c for c in sc['장'] if c['id'] == 'main'), {})
    모토 = (main.get('제목줄') or ['시간은 금이다'])[0]
    받침 = main.get('받침', '')
    return """      <section class="nameplate" aria-labelledby="np-title">
        <div class="np-inner">
          <p class="np-dateline">
            <span>No. %(호)d</span>
            <span class="np-date"><time datetime="%(d)s">%(점날짜)s</time> %(요일)s</span>
            <span>DAILY 06:00 &#183; 08:00</span>
          </p>
          <div class="np-head">
            <div class="np-ear np-ear-l">
              <p class="np-ear-k">Motto</p>
              <p class="np-ear-t">%(모토)s</p>
              <p class="np-ear-s">%(받침)s</p>
            </div>
            <div class="np-mast">
              <h1 id="np-title" class="np-title">어제한입<svg class="np-dot" viewBox="0 0 200 200" aria-hidden="true" focusable="false"><path d="%(mark)s"/></svg></h1>
              <p class="np-tag" lang="en">Yesterday, digested.</p>
            </div>
            <div class="np-ear np-ear-r">
              <p class="np-ear-k">Every morning</p>
              <p class="np-ear-t">매일 아침 6시와 8시</p>
              <p class="np-ear-s">Instagram &#183; YouTube</p>
            </div>
          </div>
          <hr class="np-rule">
          <figure class="np-strip">
            <picture>
              <!-- 🔴 WebP 먼저, JPG 받침. 이 기계 ffmpeg 에는 webp 인코더가 없어 크롬으로 만든다: node tools/make-banner-webp.mjs
                   폰(≤640)은 가운데(서울 하늘)만 잘라낸 판 — 가로 6:1 띠를 그대로 줄이면 사진이 실처럼 가늘어진다 -->
              <source media="(max-width: 640px)" type="image/webp" sizes="100vw"
                      srcset="/assets/brand/strip-m-720.webp 720w, /assets/brand/strip-m-1080.webp 1080w" width="1080" height="386">
              <source media="(max-width: 640px)" sizes="100vw"
                      srcset="/assets/brand/strip-m-720.jpg 720w, /assets/brand/strip-m-1080.jpg 1080w" width="1080" height="386">
              <source type="image/webp" sizes="min(100vw, 1680px)"
                      srcset="/assets/brand/strip-1280.webp 1280w, /assets/brand/strip-1920.webp 1920w, /assets/brand/strip-2560.webp 2560w" width="2560" height="425">
              <img src="/assets/brand/strip-1920.jpg" sizes="min(100vw, 1680px)"
                   srcset="/assets/brand/strip-1280.jpg 1280w, /assets/brand/strip-1920.jpg 1920w, /assets/brand/strip-2560.jpg 2560w"
                   width="2560" height="425" fetchpriority="high" decoding="async"
                   alt="신문 더미, 남산타워가 보이는 서울 강변, 출근길 사람들 — 흑백 보도사진 띠">
            </picture>
          </figure>
        </div>
      </section>
""" % dict(호=len(편), d=e(d), 점날짜='%d.%02d.%02d' % (y, m, day), 요일=요일,
           모토=e(모토), 받침=e(받침), mark=MARK_PATH)


def formats(editions, sc):
    """두 판 — 카드뉴스(Instagram) · 세로 영상(YouTube)을 «나란히» 펼친다.

    🔴 2026-09-24 — 3장이 4초마다 넘어가던 쇼케이스를 «고정된 두 판»으로 바꿨다.
       스스로 움직이는 첫 화면은 «통통 튀는» 인상의 한 몫이었고(팀장 유치함 목록),
       한입이 장(main)은 모토만 제호 «귀»로 옮기고 뺐다 (.review/뺀것.md).
    🔴 §5 — 재생 버튼은 유튜브 판 폰 «안»에 그대로 있다. 누르면 이 웹에서 소개 영상 창(id=intro-open).
       폰의 다른 곳은 그 편 게시물로 간다. 기기목업() 을 그대로 쓴다.
    🔴 §1 — 한 판에 계정 단추 «하나»씩 (유진님 09:09 「둘중 하나만 살리자」).
    """
    장 = {c['id']: c for c in sc['장']}
    최신 = editions['편'][0] if editions.get('편') else {}
    표지 = 최신.get('표지')
    릴스 = '/assets/reel/%s.jpg' % 최신.get('날짜', '')
    if not os.path.exists(os.path.join(HERE, 릴스.lstrip('/'))):
        릴스 = 표지
    이슈 = 최신.get('이슈', [])
    _y, _m, _d = (최신.get('날짜') or '2026-01-01').split('-')
    날짜말 = '%d월 %d일' % (int(_m), int(_d))
    첫이슈 = 이슈[0] if 이슈 else '어제의 이슈'
    나머지 = (' 외 %d건' % (len(이슈) - 1)) if len(이슈) > 1 else ''

    단추종류 = {
        'instagram': ('btn-ig', IC['ig'], 'VIEW ON INSTAGRAM', IG_ACCOUNT),
        'youtube': ('btn-yt', IC['yt'], 'VIEW ON YOUTUBE', YT_CHANNEL),
    }
    판 = []
    for n, key in enumerate(('instagram', 'youtube')):
        c = 장.get(key)
        if not c or not c.get('보임'):
            continue
        줄 = []
        for k, t in enumerate(c['제목줄']):
            if t:
                줄.append('<span class="accent">%s</span>' % e(t) if k == c.get('강조줄') else e(t))
        cls, icon, 글, 주소 = 단추종류[key]
        if key == 'instagram' and 표지:
            그림 = 기기목업(표지, '가장 최근 편 카드뉴스 표지',
                          주소=최신.get('인스타_카드') or IG_ACCOUNT,
                          설명='가장 최근 편 카드뉴스를 Instagram에서 보기',
                          윗줄='%s 어제 이슈 %d개를 카드 %d장으로 정리했어요.'
                               % (날짜말, len(이슈), 최신.get('카드수', 0)),
                          아랫줄=첫이슈 + 나머지, 캡션='DAILY 06:00 · 08:00')
        elif key == 'youtube' and 릴스:
            그림 = 기기목업(릴스, '가장 최근 편 릴스 표지', 재생=True,
                          주소=최신.get('유튜브') or YT_CHANNEL,
                          설명='가장 최근 편 영상을 YouTube에서 보기',
                          윗줄='%s 어제 이슈 %d개' % (날짜말, len(이슈)),
                          아랫줄=첫이슈 + 나머지)
        else:
            그림 = ''
        판.append("""          <article class="fmt fmt-%(key)s reveal" aria-labelledby="fmt-%(key)s-title">
            <div class="fmt-art">%(그림)s</div>
            <div class="fmt-text">
              <p class="fmt-k"><span>No. %(no)02d</span><span>%(눈금)s</span><span>%(시각)s</span></p>
              <h2 id="fmt-%(key)s-title">%(제목)s</h2>
              <p class="fmt-lead">%(설명)s</p>
              <a class="btn %(cls)s" href="%(주소)s" target="_blank" rel="noopener">%(icon)s <span>%(글)s</span> %(go)s</a>
            </div>
          </article>""" % dict(key=key, 그림=그림, no=n + 1, 눈금=e(c.get('눈금', '')),
                                시각=e(c.get('시각칩', '')), 제목='<br>'.join(줄),
                                설명=e(c['설명']), cls=cls, 주소=주소, icon=icon, 글=e(글), go=IC['go']))

    return """      <section class="formats" aria-label="어제한입 두 판">
        <div class="fmt-inner">
          <p class="sec-k"><span>The daily edition</span><span>Two formats</span></p>
          <div class="fmt-grid">
%(판)s
          </div>
          <!-- 🔴 2026-09-12 유진님 15:17 — 소개 영상으로 들어가는 문은 «유튜브 판 폰 안의 재생 단추» 하나뿐이다.
               INTRO 단추는 없앤 그대로다. 창(.intro-modal)은 그대로 둔다. -->
          <p class="hero-sub">
            <a href="#editions" data-view="editions">Latest drops <span aria-hidden="true">&#8594;</span></a>
          </p>
        </div>
      </section>
""" % dict(판='\n'.join(판))


# ── 화면(칸) ───────────────────────────────────────────────────────
def view_yesterdigest(cfg, data):
    """들어오면 처음 보이는 화면 — 제호 + 두 판 + 하는 일. (문의는 맨 아래 oauth_note)"""
    sc = json.load(open(os.path.join(HERE, 'data/showcase.json'), encoding='utf-8'))
    return nameplate(data['editions'], sc) + formats(data['editions'], sc) + """
      <section class="section section--about" aria-labelledby="about-title">
        <div class="section-inner">
          <div class="section-heading reveal">
            <p class="eyebrow">What we do</p>
            <h2 id="about-title">고르고,<br>확인하고,<br>한입 크기로.</h2>
            <!-- 🔴 여기 있던 구글 OAuth 두 문장은 «맨 아래» oauth_note() 로 옮겼다
                 (유진님 2026-09-12 08:53 · 09:48). 지운 것이 아니라 «옮긴» 것이다 — 되돌리지 마라. -->
            <div class="about-side">
              <figure class="about-figure">""" + 캐릭터('about-ch', '신문을 들고 선 어제한입 캐릭터') + """</figure>
              <p>어제 하루를 한입 크기로 잘라, 아침 6시와 8시에 놓아둡니다.
                 무엇을 골랐는지와 어떻게 확인했는지를 먼저 챙기고요.</p>
            </div>
          </div>
          <div class="steps reveal">
            <article class="card">
              <span class="step-number" aria-hidden="true">01</span>
              <h3>주요 이슈 선별</h3>
              <p>공식 자료와 복수의 보도를 바탕으로 전날의 핵심 이슈를 선별하고 사실관계를 확인합니다.</p>
            </article>
            <article class="card">
              <span class="step-number" aria-hidden="true">02</span>
              <h3>콘텐츠 제작</h3>
              <p>선별한 이슈를 세로형 영상과 카드뉴스에 맞춰 간결하고 이해하기 쉬운 형식으로 제작합니다.</p>
            </article>
            <article class="card">
              <span class="step-number" aria-hidden="true">03</span>
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
        # 🔴 2026-09-24 — 편마다 다른 «요일색»을 홈페이지에서는 안 쓴다(색 가짓수 = 유치함의 한 몫).
        #    먹·크림·머스터드 한 벌로 간다. 요일색은 카드·영상 쪽 규칙이라 data 에는 그대로 둔다.
        호 = len(data['editions']['편']) - i
        이슈 = ed.get('이슈', [])
        줄 = ''.join('<li><span>%02d</span>%s</li>' % (n + 1, e(t)) for n, t in enumerate(이슈))
        ig = ed.get('인스타_카드') or ed.get('인스타_릴스') or IG_ACCOUNT
        yt = ed.get('유튜브') or YT_CHANNEL
        릴스있음 = bool(ed.get('인스타_릴스'))
        더보기 = ('카드 %d장 전체와 릴스 1편은 계정에서 봅니다.' if 릴스있음
                  else '카드 %d장 전체는 계정에서 봅니다.') % ed.get('카드수', 0)

        panels.append("""            <article class="ed">
              <a class="ed-cover" href="%(ig)s" target="_blank" rel="noopener"
                 aria-label="%(title)s 카드뉴스를 Instagram에서 보기">
                <!-- 이 화면은 처음엔 숨어 있다. display:none 이어도 브라우저는 src 를 받아버리므로
                     (실측: 표지 3장 317KB 가 첫 화면에서 받아졌다) 화면이 열릴 때 home.js 가 붙인다. -->
                <img data-src="%(cover)s" width="720" height="900" decoding="async"
                     alt="%(title)s 어제한입 카드뉴스 표지">
                <noscript><img src="%(cover)s" width="720" height="900" alt="%(title)s 어제한입 카드뉴스 표지"></noscript>
              </a>
              <div class="ed-text">
                <p class="ed-day"><span class="ed-no">No. %(호)d</span><time datetime="%(d)s">%(엔날짜)s</time><i>%(엔요일)s</i></p>
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
            </article>""" % dict(호=호, d=d, ig=ig, yt=yt, cover=ed['표지'], title=title, wd=wd,
                                 엔날짜=엔날짜, 엔요일=엔요일, 줄=줄, more=더보기,
                                 icig=IC['ig'], icyt=IC['yt']))

    return """      <section class="section section--rail">
        <div class="section-inner">
          <div class="section-heading reveal">
            <p class="eyebrow">Latest drops</p>
            <h2>%(제목)s</h2>
            <p>어제의 이슈 네댓 개를 카드뉴스 한 벌과 세로 영상 한 편으로 만듭니다.
               옆으로 <b>밀거나 화살표</b>로 지난 편을 넘겨보세요 — 전체는 Instagram과 YouTube에 있습니다.</p>
          </div>
        </div>
        <div class="ed-rail" style="--n: %(n)d">
          <!-- 🔴 무대를 «누르면» 잡힌다. 잡혔을 때만 휠이 옆으로 간다 (유진님 12:39 ②).
               잡지 않아도 끌기·스와이프·화살표 단추·방향키로 넘길 수 있고, Tab 으로도 닿는다. -->
          <div class="ed-stage" tabindex="0" role="group"
               aria-roledescription="carousel" aria-label="지난 편 넘겨보기">
            <div class="ed-track">
%(panels)s
            </div>
            <!-- 🔴 첫 편의 왼쪽 · 마지막 편의 오른쪽은 «그냥 빈다»(.ed-track 주석). 그 빈 것이
                 「여기가 끝」이라는 뜻인데 전달이 안 돼 유진님이 16:29 「양쪽에 전날, 다음날께
                 왜 안보여?」라고 물으셨다. 그래서 빈 자리에 «아주 옅은» 표시를 둔다.
                 이웃 예고(.26)보다 조용하게 · 누를 수 없게 · 읽는 기계에는 안 잡히게. -->
            <span class="ed-edge ed-edge-new" aria-hidden="true">NEWEST</span>
            <span class="ed-edge ed-edge-old" aria-hidden="true">OLDEST</span>
            <p class="ed-hint" data-off="TAP TO BROWSE" data-on="SCROLL TO BROWSE · ESC">TAP TO BROWSE</p>
            <div class="ed-nav">
              <button type="button" class="ed-prev" aria-label="이전 편">%(icp)s</button>
              <button type="button" class="ed-next" aria-label="다음 편">%(icn)s</button>
            </div>
            <div class="ed-progress" aria-hidden="true"><i></i></div>
          </div>
        </div>
      </section>""" % dict(제목=e(cfg['제목']), panels='\n'.join(panels), n=len(panels),
                            icp=IC['prev'], icn=IC['next'])


SECTION_BUILDERS = {
    'yesterdigest': view_yesterdigest,
    'editions': view_editions,
    # 'stocks': view_stocks,   ← 주식 동향 칸을 열 때 여기에 등록한다
    # 'cv':     view_cv,       ← 연구 이력 칸을 열 때 여기에 등록한다
}


# 🔴 한글 «제목» 글씨 = 배달의민족 주아 — 홈페이지-규칙 §3 (유진님 2026-09-12 09:01 「배달의 민족 주아로 가자」).
#    2026-09-24 3차에 명조를 시험했으나 팀장 정리: «정본은 §3 이고 명조는 제안이다» → 기본을 주아로 되돌렸다.
#    제목 글꼴은 CSS 변수 하나(--font-display · assets/styles.css)가 정한다. 명조 판은 <html data-font="serif"> 로
#    «바꿔 찍는» 제안일 뿐이고, 이 페이지는 명조를 받지 않는다 (.review/shot3.mjs 가 찍을 때만 붙인다).
#    «이 페이지가 실제로 제목 글꼴로 그리는 글자»만 받는다 (Google Fonts text=).
#    아래 자리는 assets/home.css 의 --font-display 선택자와 «짝»이다. 거기에 선택자를 더하면 여기도 더한다 —
#    안 그러면 그 글자만 대체 글꼴로 튄다.
제목글꼴_자리 = [r'<h1[^>]*>(.*?)</h1>', r'<h2[^>]*>(.*?)</h2>', r'<h3[^>]*>(.*?)</h3>',
            r'class="brand-name"[^>]*>(.*?)</span>',
            r'class="np-ear-t"[^>]*>(.*?)</p>']

# 날마다 바뀌는 것 — 오늘 페이지에 없어도 반드시 넣는다
제목글꼴_바탕 = ('0123456789년월일()' + '월화수목금토일'
            + 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz' + ' .,·-~!?:')


def 제목글꼴_글자(page):
    """이 페이지에서 제목 글꼴(주아)이 그릴 글자를 모은다 → Google Fonts text= 로 넘긴다."""
    글자 = set(제목글꼴_바탕)
    for pat in 제목글꼴_자리:
        for m in re.findall(pat, page, re.S):
            글자 |= set(html.unescape(re.sub(r'<[^>]+>', '', m)))
    글자 -= set('\n\r\t')
    return ''.join(sorted(글자))


def intro_modal():
    """소개 영상 «틀» — 영상은 아직 없다. 움직임과 자리만 미리 만들어 둔다.

    유진님 2026-09-12 11:19 「짧은 어제한입 소개 영상을 만들어줘」 · 15:17 「재생버튼을 누르면 이 웹에서 소개영상을 띄워야지」
    🔴 «누르면 커졌다가 끝나면 줄어드는» 움직임은 그대로. 영상이 생기면 .intro-slot 안만 <video> 로 바꾼다.
    🔴 2026-09-24 — 캐릭터 그림을 뺐다(「한입이 버려도 된다」). 크림 종이 한 장에 활자만 둔다.
       빈 창으로 두지 않는다 — 반응이 없으면 «고장»으로 보인다(§5).
    """
    return """  <div class="intro-modal" id="intro-modal" hidden>
    <div class="intro-box" role="dialog" aria-modal="true" aria-labelledby="intro-title">
      <button class="intro-close" type="button" id="intro-close" aria-label="닫기">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>
      </button>
      <div class="intro-slot">
        <div class="intro-ch">%s</div>
        <p class="intro-k">Intro film</p>
        <p id="intro-title">COMING SOON</p>
        <p class="intro-sub">10초 안에 어제한입이 어떤 곳인지 보여드릴게요.</p>
      </div>
    </div>
  </div>
""" % 캐릭터('intro-chr')


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
       (이 줄은 앞선 세션이 남긴 «작업 기준»이다. 🔴 정본 규칙이 아니다 —
        CLAUDE.md 에 글자 크기 규칙은 없다. 정본으로 만들려면 유진님 승인을 받아야 한다)
    """
    return """  <section class="oauth-note" aria-labelledby="oauth-title">
    <div class="oauth-inner reveal">
      <div class="oauth-head">
        <p class="oauth-eyebrow">Google OAuth</p>
        <h2 id="oauth-title">Google 권한은 채널 운영에만 사용합니다.</h2>
      </div>
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
def 자산판번호(page):
    """css·js 주소 뒤에 «내용 해시»를 붙인다 — `/assets/home.css?v=a1b2c3d4`

    🔴 왜 있나 — 2026-09-12 12:24 유진님 「웹 클릭이 아무곳도 안돼」.
       고쳐서 올렸는데도 «유진님 브라우저가 옛 home.css 를 들고 있어» 여전히 고장난 채였다.
       HTML 은 새로 받아도 CSS·JS 는 캐시가 오래 남는다 — 새로고침으로 안 풀리는 전형이다.
       고칠 때마다 「안 바뀌었는데?」가 반복되므로 «구조»로 막는다.

    🔴 시각이나 커밋이 아니라 «파일 내용»의 해시를 쓴다. 두 가지가 같이 지켜진다:
       ① 내용이 바뀌면 주소가 바뀐다 → 브라우저가 반드시 새로 받는다
       ② 내용이 같으면 주소도 같다 → 다시 돌려도 index.html 이 안 바뀐다(md5 동일 검사 유지)
    """
    import hashlib
    붙인것 = []
    for 주소 in ('/assets/styles.css', '/assets/home.css', '/assets/home.js', '/assets/theme.js',
               '/assets/og/home.png'):
        f = os.path.join(HERE, 주소.lstrip('/'))
        if not os.path.exists(f):
            print('  \u26a0\ufe0f 자산 없음 — 판번호 못 붙임: %s' % 주소)
            continue
        h = hashlib.md5(open(f, 'rb').read()).hexdigest()[:8]
        # 끝따옴표로만 맞춘다 — og 그림은 "https://yesterdigest.com/assets/og/home.png" 처럼
        # 앞에 도메인이 붙어 있어서 «따옴표-주소-따옴표» 로는 안 잡힌다
        page = page.replace('%s"' % 주소, '%s?v=%s"' % (주소, h))
        붙인것.append('%s?v=%s' % (주소.rsplit('/', 1)[-1], h))
    print('  자산 판번호 — ' + ' \u00b7 '.join(붙인것))
    return page


def sitemap():
    """sitemap.xml 을 «손으로 안 고쳐도» 맞게 유지한다.

    🔴 lastmod 는 파일 시각이 아니라 «git 이 아는 마지막 고친 날»이다.
       파일 시각을 쓰면 build.py 를 돌릴 때마다 내용은 그대로인데 날짜만 바뀌어
       git 에 매일 의미 없는 변경이 쌓인다.
    🔴 주소는 «실제로 있는 주소»만 넣는다. 이 홈페이지는 화면을 #해시로 바꾸므로
       어제한입·EDITIONS 는 따로 주소가 없다 — 넣으면 구글이 404 취급한다.
    """
    쪽 = [('/', 'index.html'), ('/privacy/', 'privacy/index.html'), ('/terms/', 'terms/index.html')]
    줄 = []
    for 주소, 파일 in 쪽:
        if not os.path.exists(os.path.join(HERE, 파일)):
            print('  ⚠️ sitemap 건너뜀 — 파일이 없다: %s' % 파일)
            continue
        try:
            날 = subprocess.run(['git', 'log', '-1', '--format=%cs', '--', 파일],
                               cwd=HERE, capture_output=True, text=True, timeout=10).stdout.strip()
        except Exception:
            날 = ''
        날 = 날 or datetime.date.today().isoformat()
        줄.append('  <url>\n    <loc>https://yesterdigest.com%s</loc>\n    <lastmod>%s</lastmod>\n  </url>'
                  % (주소, 날))
    out = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s\n</urlset>\n' % '\n'.join(줄))
    open(os.path.join(HERE, 'sitemap.xml'), 'w', encoding='utf-8').write(out)
    print('  sitemap.xml — 주소 %d개' % len(줄))


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
        # 🔴 서랍 줄에만 쓰는 «영어 이름». 없으면 제목 그대로 (2026-09-12 유진님 16:07)
        menu.append('        <a class="menu-item%s" href="#%s" data-view="%s"%s>%s</a>'
                    % (' is-en' if c.get('메뉴이름') else '', e(c['id']), e(c['id']),
                       ' aria-current="page"' if c['id'] == 기본 else '',
                       e(c.get('메뉴이름') or c['제목'])))
        views.append('    <section class="view%s" id="view-%s" data-view="%s">\n%s\n    </section>'
                     % (' is-active' if c['id'] == 기본 else '', e(c['id']), e(c['id']), fn(c, data)))

    자리 = ['  <!-- 자리: %s (%s) — data/sections.json 에서 "보임": true 로 켜면 메뉴와 화면에 자동으로 나온다 -->'
            % (c['id'], c['제목']) for c in sections['칸'] if not c.get('보임')]

    page = PAGE % dict(
        YT=YT_CHANNEL, IG=IG_ACCOUNT, CH=BRAND, LOGO=LOGO_MARK, 기본=기본,
        icsun=IC['sun'], icmoon=IC['moon'],
        icyt=IC['yt'], icig=IC['ig'], icmenu=IC['menu'], icx=IC['x'],
        menu='\n'.join(menu), views='\n\n'.join(views), 자리='\n'.join(자리),
        intro=intro_modal(), oauth=oauth_note())
    글자 = 제목글꼴_글자(page)
    page = page.replace('__DISPLAY_TEXT__', urllib.parse.quote(글자, safe=''))
    page = 자산판번호(page)
    open(os.path.join(HERE, 'index.html'), 'w', encoding='utf-8').write(page)
    print('index.html — 화면 %d개 · 메뉴 %d줄 · 자리만 %d개 (기본 화면: %s)'
          % (len(views), len(menu), len(자리), 기본))
    print('  제목 글꼴(주아 Jua)은 글자 %d자만 받는다 (text=)' % len(글자))
    sitemap()


PAGE = """<!doctype html>
<html lang="ko" data-theme="light">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <!-- 🔴 판(밝은 크림 / 어두운 먹)을 «그리기 전에» 박는다 — 다크를 고른 사람이 새로고침할 때 크림이 번쩍이지 않게.
       첫 방문은 OS 설정과 상관없이 «크림»이다 (유진님 2026-09-24 「웹색상은 밝은 크림시문지로 바꾸되 다크모드 기눙도 넣어줘」).
       저장소가 막혀 있으면(사생활 창 등) 조용히 크림으로 간다. 누르는 단추는 /assets/theme.js 가 맡는다. -->
  <script>(function(){var t='light';try{if(localStorage.getItem('yd-theme')==='dark')t='dark';}catch(e){}document.documentElement.setAttribute('data-theme',t);})();</script>
  <title>%(CH)s | YesterDigest</title>
  <meta name="description" content="어제의 뉴스를 한입 크기로. 매일 아침 6시와 8시, Instagram과 YouTube에 올라갑니다.">
  <meta name="theme-color" content="#F8F3E9">
  <link rel="canonical" href="https://yesterdigest.com/">

  <!-- 카톡·트위터·페북에 «주소를 붙였을 때» 뜨는 것.
       🔴 그림은 1200x630 이어야 «큰 카드»로 뜬다. 그림 원본은 tools/og-card.html · 다시 만들기는 `python3 tools/make-assets.py`.
       🔴 주소 뒤 ?v= 는 build.py 가 «파일 내용 해시»로 붙인다 (카카오·페북 캐시 대비).
       ⚠️ 2026-09-24 — 새 로고가 나온 뒤 팀장 지시로 그림을 바꾼다. 지금 그림은 옛 판이다. -->
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="YesterDigest">
  <meta property="og:locale" content="ko_KR">
  <meta property="og:title" content="%(CH)s | YesterDigest">
  <meta property="og:description" content="어제의 뉴스를 한입 크기로. 매일 아침 6시와 8시.">
  <meta property="og:url" content="https://yesterdigest.com/">
  <meta property="og:image" content="https://yesterdigest.com/assets/og/home.png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="어제의 뉴스를 한입 크기로 — 매일 아침 6시와 8시">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="%(CH)s | YesterDigest">
  <meta name="twitter:description" content="어제의 뉴스를 한입 크기로. 매일 아침 6시와 8시.">
  <meta name="twitter:image" content="https://yesterdigest.com/assets/og/home.png">

  <!-- 🔴 /favicon.ico 는 «선언과 상관없이» 받아 간다. 셋 다 tools/make-assets.py 가 같은 로고에서 만든다.
       (2026-09-24 — 새 로고가 오면 팀장 지시로 바꾼다. 지금 손대지 않는다) -->
  <link rel="icon" href="/favicon.ico" sizes="32x32">
  <link rel="icon" href="/assets/brand/icon.svg" type="image/svg+xml">
  <link rel="icon" href="/assets/brand/logo-256.png" type="image/png" sizes="256x256">
  <link rel="apple-touch-icon" href="/apple-touch-icon.png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>
  <!-- 글씨체 — 2026-09-24 에디토리얼 판 (유진님 「최대한 고급스럽게」)
       · 한글 제목  배달의민족 주아(Jua) 400 — 홈페이지-규칙 §3 정본 · SIL OFL 1.1 · Google Fonts 배포본 · «이 페이지가 쓰는 글자만» text= 로 받는다
                    (명조 Noto Serif KR 은 «제안» — data-font="serif" 로 바꿔 찍을 때만 붙인다. 이 페이지는 받지 않는다)
       · 한글 본문  Pretendard — SIL OFL 1.1 · jsDelivr(orioncactus/pretendard v1.3.9) «dynamic subset»: 화면에 나온 글자 조각만 받는다
       · 영문 꼬리표 Inter 500·600·700 — SIL OFL 1.1 · Google Fonts (라틴만)
       · 태그라인 한 곳 Cormorant Garamond 기울임 500 — SIL OFL 1.1 · Google Fonts · 「Yesterday, digested.」 글자만 받는다
       🔴 넷 다 font-display: swap — 글씨체가 늦어도 글은 먼저 보인다.
       🔴 Gothic A1 은 뺐다(본문은 Pretendard). 주아는 규칙 §3 이라 그대로 둔다 — 바꾸려면 유진님이 §3 을 바꾸셔야 한다.
       🔴 홈페이지에만 쓴다. 영상·카드뉴스 글씨체는 안 건드린다. -->
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@500;600;700&display=swap">
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Jua&display=swap&text=__DISPLAY_TEXT__">
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@1,500&display=swap&text=Yesterday%%2C%%20digested.">
  <link rel="stylesheet" href="/assets/styles.css">
  <link rel="stylesheet" href="/assets/home.css">

  <!-- 검색엔진에게 «우리가 누구이고 계정이 어디인지»를 그대로 알려준다 (schema.org).
       🔴 이 홈페이지의 뜻이 «인스타·유튜브로 보내는 대문»이라 sameAs 가 핵심이다 (유진님 07:54).
       🔴 화면에 없는 것을 지어내지 않는다. -->
  <script type="application/ld+json">
  {"@context":"https://schema.org","@graph":[
    {"@type":"Organization","@id":"https://yesterdigest.com/#org",
     "name":"YesterDigest","alternateName":"어제한입",
     "url":"https://yesterdigest.com/",
     "email":"yesterdigest@gmail.com",
     "logo":{"@type":"ImageObject","url":"https://yesterdigest.com/assets/brand/logo-256.png","width":256,"height":256},
     "description":"어제의 뉴스를 한입 크기로. 매일 아침 6시와 8시 Instagram과 YouTube에 올라갑니다.",
     "sameAs":["%(IG)s","%(YT)s"]},
    {"@type":"WebSite","@id":"https://yesterdigest.com/#site",
     "name":"%(CH)s | YesterDigest","url":"https://yesterdigest.com/",
     "inLanguage":"ko-KR","publisher":{"@id":"https://yesterdigest.com/#org"}}
  ]}
  </script>
</head>
<body data-default-view="%(기본)s">
  <a class="skip-link" href="#main">본문으로 건너뛰기</a>

  <header class="site-header">
    <nav class="nav" aria-label="주요 메뉴">
      <button class="menu-btn" type="button" id="menu-open"
              aria-label="메뉴 열기" aria-expanded="false" aria-controls="drawer">%(icmenu)s</button>
      <!-- 🔴 aria-label 을 «안» 붙인다 — 보이는 글씨가 이름이다 (WCAG 2.5.3 Label in Name).
           🔴 로고 자리(.logo-slot)는 크기가 정해진 틀이다. 새 로고는 build.py 의 LOGO_MARK 한 줄만 바꾼다. -->
      <a class="brand-link" href="#%(기본)s" data-view="%(기본)s">
        <span class="logo-slot"><img src="%(LOGO)s" alt="" width="36" height="36"></span>
        <span class="brand-name">%(CH)s<small>YESTERDIGEST</small></span>
      </a>
      <div class="nav-actions">
        <!-- 🔴 판 바꾸기 — 보이는 글씨(DARK/LIGHT)가 이름의 앞머리다. 44px 이상 · 초점 보임 · theme.js 가 글씨를 바꾼다 -->
        <button class="theme-btn" type="button" data-theme-toggle>%(icmoon)s%(icsun)s<span class="theme-label">DARK</span><span class="sr-only"> 모드로 바꾸기</span></button>
        <a class="icon-link ig" href="%(IG)s" target="_blank" rel="noopener" aria-label="Instagram 계정 열기">%(icig)s</a>
        <a class="icon-link yt" href="%(YT)s" target="_blank" rel="noopener" aria-label="YouTube 채널 열기">%(icyt)s</a>
      </div>
    </nav>
  </header>

  <!-- 목록 — data/sections.json 의 «보임: true» 인 칸만 나온다 -->
  <div class="drawer-backdrop" id="drawer-backdrop" hidden></div>
  <aside class="drawer" id="drawer" hidden aria-label="화면 목록">
    <div class="drawer-head">
      <span class="drawer-title">MENU</span>
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
      <p class="footer-brand"><span class="logo-slot logo-slot--sm"><img src="%(LOGO)s" alt="" width="24" height="24"></span>© 2026 YesterDigest</p>
      <div class="footer-links">
        <a href="%(IG)s" target="_blank" rel="noopener">Instagram</a>
        <a href="%(YT)s" target="_blank" rel="noopener">YouTube</a>
        <a href="/privacy/">개인정보처리방침</a>
        <a href="/terms/">이용약관</a>
        <a href="mailto:yesterdigest@gmail.com">문의</a>
      </div>
    </div>
  </footer>

  <script src="/assets/theme.js" defer></script>
  <script src="/assets/home.js" defer></script>
</body>
</html>
"""

if __name__ == '__main__':
    build()
