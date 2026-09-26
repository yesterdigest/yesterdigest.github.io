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
# 🔴 2026-09-24 — 대표 이름은 «어제한입 / YesterDigest» 하나다. 캐릭터 이름은 버렸다
#    (유진님 2026-09-24 16:3x 팀장 전달 — 원문은 .review/진행.md 1차 절). 뺀 자리 목록 → .review/뺀것.md
BRAND = '어제한입'
# 🔴 2026-09-25 5차 — 로고는 «D4 v2 한글 레터링»(인장 + 워드마크)이다. 방향 교체표: tools/brand-map.json
#    파일은 전부 assets/brand/ 의 «정식 이름»이다. 유진님이 다른 방향을 고르시면 brand-map.json 한 줄을 바꾸고
#    그 방향의 파일을 같은 이름으로 복사한 뒤 python3 tools/make-assets.py · python3 build.py 를 다시 돌린다.
#    머리줄 = 가로 짜임(인장 + 작은 판 워드마크) 두 장을 판([data-theme])에 따라 번갈아 보인다.
LOCKUP = ('/assets/brand/lockup-h.svg', '/assets/brand/lockup-h-dark.svg')
SEAL = ('/assets/brand/seal.svg', '/assets/brand/seal-dark.svg')
# 폰 목업 안의 계정 사진 — 채널 프로필과 같은 인장(먹 타일)
LOGO_ICON = '/assets/brand/icon.svg'


def 캐릭터(cls='', alt='', 파일='character.svg'):
    """캐릭터 «편집자» — assets/brand/character.svg(신문 읽기 판)를 «페이지 안»에 넣는다.

    2026-09-25 5차: D4 v2 획 체계로 새로 그린 어른 한 사람 (머리 = ㅎ 의 ㅇ · 모자 = ㅎ 가로획 · 꼭지 = 머스터드 점).
    색은 파일 밖에서 칠한다 — home.css 의 --ch-line · --ch-face · --ch-coat · --ch-dot (판마다 다름).
    파일 안 <style>(대체값)과 <title> 은 떼고, 부위 id(head·hat·arm-l·arm-r·body…)에는 cls 를 앞에 붙여 겹치지 않게 한다.
    🔴 실존 인물 얼굴이 아니다 — 브랜드 캐릭터 그림이다. 원본·닮음 확인: .review/brand5/D4v2/README.md
    """
    svg = open(os.path.join(HERE, 'assets/brand', 파일), encoding='utf-8').read()
    svg = re.sub(r'<style>.*?</style>', '', svg, flags=re.S)
    svg = re.sub(r'<title>.*?</title>', '', svg, flags=re.S)
    svg = re.sub(r' role="img" aria-label="[^"]*"', '', svg, count=1)
    svg = re.sub(r' width="\d+" height="\d+"', '', svg, count=1)
    svg = re.sub(r' id="([a-z-]+)"', lambda m: ' id="%s-%s"' % (cls, m.group(1)), svg)
    if alt:
        svg = svg.replace('<svg ', '<svg role="img" aria-label="%s" class="ch %s" ' % (e(alt), cls), 1)
    else:
        svg = svg.replace('<svg ', '<svg aria-hidden="true" focusable="false" class="ch %s" ' % cls, 1)
    return svg.strip()


def 레터링(파일, cls):
    """D4 v2 워드마크를 «페이지 안»에 넣는다 — 제안 스위치(?masthead=lettering)에서만 보인다.

    글자 획은 currentColor(판의 먹/크림을 따른다) · ㅎ 꼭지 점만 .np-letter-dot(머스터드) 로 칠한다.
    🔴 장식이다(aria-hidden) — 이름은 h1 의 글자(sr-only)가 말한다.
    """
    svg = open(os.path.join(HERE, 'assets/brand', 파일), encoding='utf-8').read()
    svg = re.sub(r'<title>.*?</title>', '', svg, flags=re.S)
    svg = re.sub(r' role="img" aria-label="[^"]*"', '', svg, count=1)
    svg = re.sub(r' width="[\d.]+" height="[\d.]+"', '', svg, count=1)
    paths = re.findall(r'<path d="([^"]+)" fill="[^"]+"/>', svg)
    assert len(paths) == 2, 파일
    vb = re.search(r'viewBox="([^"]+)"', svg).group(1)
    return ('<svg class="np-letter %s" viewBox="%s" aria-hidden="true" focusable="false">'
            '<path d="%s" fill="currentColor"/><path class="np-letter-dot" d="%s"/></svg>' % (cls, vb, paths[0], paths[1]))

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
    🔴 2026-09-25 5차 — 링크 «안에» 단추를 넣지 않는다(a 안의 button 은 HTML 위반 · 누름이 엉킨다).
       .device 안에 «투명한 덮개 링크»(.dv-cover, 전면)와 재생 단추(.dv-play)를 «형제»로 두고 단추를 위에 겹친다.
    """
    덮개 = ('<a class="dv-cover" href="%s" target="_blank" rel="noopener" aria-label="%s"></a>'
            % (e(주소), e(설명 or alt))) if 주소 else ''

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
                    </div>""" % dict(
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

    재생단추 = ("""
                  <button class="dv-play" type="button" id="intro-open" aria-haspopup="dialog"
                          aria-label="어제한입 소개 영상 보기">
                    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg>
                  </button>""" if 재생 else '')
    return """<div class="device-link">
                <div class="device%(릴)s">
                  <span class="device-slit" aria-hidden="true"></span>
                  <div class="device-screen">
                    %(속)s
                  </div>
                  %(덮개)s%(재생단추)s
                </div>
              </div>""" % dict(릴=' device--reel' if 재생 else '', 속=속.replace('__LOGO__', LOGO_ICON),
                               덮개=덮개, 재생단추=재생단추)


def nameplate(editions, sc, 날짜=None):
    """첫 화면 맨 위 — «신문 제호(nameplate)».

    🔴 2026-09-24 유진님 16:3x (팀장 전달)
       「웹색상은 밝은 크림시문지로 바꾸되 다크모드 기눙도 넣어줘」 · 「응 촤대한 고급스럽게, 지금은 너무 유치하니까 고급화하는쪽으로가자」
    짜임 (위에서 아래로) — 신문 1면 머리 그대로:
       날짜줄(호수 · «뉴스 날짜» · 게시 시각) → 귀(왼: 모토 · 오른: 두 판) + 제호 → 태그라인 → (폰) 계정 단추 둘 → 이중 괘선
    🔴 2026-09-25 5차 — 사진 띠를 지웠다(옛 AI 배너 조각 · 가짜 제호 · 권리 기록 없음). 제호 끝 마침표 도형도 지웠다.
    🔴 제호 기본값은 규칙 §3 대로 «주아 활자» h1 이다. D4 v2 레터링 제호는 «제안»이라
       주소에 ?masthead=lettering 을 붙였을 때만 보인다(기억하지 않는다 · <html data-masthead="lettering">).
       그 판에서도 h1 글자는 남는다(sr-only) — 읽는 기계에는 늘 「어제한입」이다.
    🔴 글은 전부 «있던 말»이다: 모토 두 줄 = data/showcase.json 장 main(유진님 2026-09-06 「"시간은 금이다" 이게 내 모토야」),
       태그라인 = 배너 안 글자, 호수 = data/editions.json 의 편 수, 날짜 = 최신 편 «뉴스 날짜». 지어낸 말 없음.
    🔴 게시 시각은 여기(날짜줄) · 소개 문단 · 메타 설명 «세 곳»에만 적는다 (5차 8번).
    """
    편 = editions.get('편', [])
    최신 = 편[0] if 편 else {}
    d = 날짜 or 최신.get('날짜') or datetime.date.today().isoformat()
    y, m, day = [int(x) for x in d.split('-')]
    요일 = EN_WD[datetime.date(y, m, day).weekday()]
    main = next((c for c in sc['장'] if c['id'] == 'main'), {})
    모토 = (main.get('제목줄') or ['시간은 금이다'])[0]
    받침 = main.get('받침', '')
    return """      <section class="nameplate" aria-labelledby="np-title">
        <div class="np-inner">
          <p class="np-dateline">
            <span>No. %(호)d</span>
            <span class="np-date">News of <time datetime="%(d)s">%(점날짜)s</time> %(요일)s</span>
            <span>06:00 Daily &#183; 08:00 By section</span>
          </p>
          <div class="np-head">
            <div class="np-ear np-ear-l">
              <p class="np-ear-k">Motto</p>
              <p class="np-ear-t">%(모토)s</p>
              <p class="np-ear-s">%(받침)s</p>
            </div>
            <div class="np-mast">
              <h1 id="np-title" class="np-title"><span class="np-title-t">어제한입</span>%(글자판)s%(두줄판)s</h1>
              <p class="np-tag" lang="en">Yesterday, digested.</p>
              <p class="np-cta">
                <a class="np-btn np-btn-solid" href="%(IG)s" target="_blank" rel="noopener">Instagram</a>
                <a class="np-btn" href="%(YT)s" target="_blank" rel="noopener">YouTube</a>
              </p>
            </div>
            <div class="np-ear np-ear-r">
              <p class="np-ear-k">Four editions</p>
              <p class="np-ear-t">종합 하나, 분야별 셋</p>
              <p class="np-ear-s">Instagram &#183; YouTube</p>
            </div>
          </div>
          <hr class="np-rule">
        </div>
      </section>
""" % dict(호=len(편), d=e(d), 점날짜='%d.%02d.%02d' % (y, m, day), 요일=요일,
           모토=e(모토), 받침=e(받침), IG=IG_ACCOUNT, YT=YT_CHANNEL,
           글자판=레터링('wordmark.svg', 'np-letter-wide'), 두줄판=레터링('wordmark-stack.svg', 'np-letter-stack'))


def formats(editions, sc):
    """두 판 — 카드뉴스(Instagram) · 세로 영상(YouTube)을 «나란히» 펼친다.

    🔴 2026-09-24 — 3장이 4초마다 넘어가던 쇼케이스를 «고정된 두 판»으로 바꿨다.
       스스로 움직이는 첫 화면은 «통통 튀는» 인상의 한 몫이었고(팀장 유치함 목록),
       main 장은 모토만 제호 «귀»로 옮기고 뺐다 (.review/뺀것.md).
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
                          아랫줄=첫이슈 + 나머지, 캡션='%s.%s.%s' % (_y, _m, _d))
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
              <p class="fmt-k"><span>No. %(no)02d</span><span>%(눈금)s</span>%(시각)s</p>
              <h2 id="fmt-%(key)s-title">%(제목)s</h2>
              <p class="fmt-lead">%(설명)s</p>
              <a class="btn %(cls)s" href="%(주소)s" target="_blank" rel="noopener">%(icon)s <span>%(글)s</span> %(go)s</a>
            </div>
          </article>""" % dict(key=key, 그림=그림, no=n + 1, 눈금=e(c.get('눈금', '')),
                                시각=('<span>%s</span>' % e(c['시각칩'])) if c.get('시각칩') else '',
                                제목='<br>'.join(줄),
                                설명=e(c['설명']), cls=cls, 주소=주소, icon=icon, 글=e(글), go=IC['go']))

    return """      <section class="formats" aria-label="어제한입 두 판">
        <div class="fmt-inner">
          <!-- 🔴 5차 — 모든 절은 .sec-k 하나로 연다: 2px 먹 괘선 + 왼쪽 꼬리표 + 오른쪽 꼬리표/링크.
               지난 편으로 가는 링크(옛 .hero-sub)는 이 줄 오른쪽 칸으로 옮겼다. -->
          <p class="sec-k"><span>The daily edition</span><a href="#editions" data-view="editions">Past editions <span aria-hidden="true">&#8594;</span></a></p>
          <div class="fmt-grid">
%(판)s
          </div>
          <!-- 🔴 2026-09-12 유진님 15:17 — 소개 영상으로 들어가는 문은 «유튜브 판 폰 안의 재생 단추» 하나뿐이다.
               INTRO 단추는 없앤 그대로다. 창(.intro-modal)은 그대로 둔다. -->
        </div>
      </section>
""" % dict(판='\n'.join(판))


def 편집자(slug, alt='', cls='', 자세=''):
    """캐릭터 «편집자» 네 벌(2026-09-25 브랜드 시안 · docs/drafts/redesign-0925/character/) — 분야마다 의상·소품·옷 색이 다르다.

    🔴 색이 파일 안에 박혀 있다(분야 색 = 옷 색). 그래서 판(크림/먹)에 따라 칠하지 않고
       «그 분야의 종이»(.plate--<slug>) 위에 올린다 — 종합 크림 · 정치·사회 먹 · 경제·세계 연어빛 · 연예·스포츠 먹.
       어느 판에서도 캐릭터가 바탕에 묻히지 않는다(먹 옷이 먹 바탕에 사라지는 일이 없다).
    🔴 실존 인물이 아니다 — 브랜드 캐릭터 그림이다. 장식이면 alt 를 비운다.
    """
    파일 = '/assets/brand/editor-%s%s.svg' % (slug, 자세)
    return ('<span class="plate plate--%s %s"><img src="%s" alt="%s" width="200" height="400" decoding="async"></span>'
            % (slug, cls, 파일, e(alt)))


def 칩(p, tag='span'):
    """분야 칩 — 점 + 한글 분야 이름(분야 이름은 «이름»이라 한글 · 규칙 §4)."""
    return '<%s class="chip chip--%s"><i aria-hidden="true"></i>%s</%s>' % (tag, p['slug'], e(p['이름']), tag)


def front_page(today):
    """1면 = 오늘 종합 · 그 아래 분야 탭 셋 (전면 개편 계획 §3 「홈페이지 1면 = 오늘 종합 · 섹션 탭 셋」).

    🔴 규칙 §1 «다 보여주지 않는 대문» — 이슈는 «제목 한 줄»만. 더 보려면 유튜브·인스타로 간다.
    🔴 규칙 §5 — 재생 단추는 1면 폰 «안»에 하나. 누르면 이 웹에서 소개 영상 창(id=intro-open).
       폰의 다른 곳(.dv-cover)은 그날 종합 유튜브로 간다.
    🔴 규칙 §4 — 누르는 것·꼬리표는 영어(WATCH · INSTAGRAM · FRONT PAGE), 분야·브랜드 이름은 한글.
    🔴 주소는 data/today.json(tools/make-today.py 가 게시 기록에서 읽음)에서만 온다.
    """
    편 = today['편']
    종합, 분야 = 편[0], 편[1:]
    y, m, d = [int(x) for x in today['날짜'].split('-')]
    날짜말 = '%d월 %d일' % (m, d)
    점날짜 = '%d.%02d.%02d' % (y, m, d)

    def 목록(p, cls):
        return '<ol class="%s">%s</ol>' % (cls, ''.join(
            '<li><span>%02d</span>%s</li>' % (n + 1, e(i['제목'])) for n, i in enumerate(p['이슈'])))

    def 단추(p, 카드=None):
        줄 = ['<a class="btn btn-yt" href="%s" target="_blank" rel="noopener" aria-label="%s %s 영상 YouTube에서 보기">%s <span>WATCH</span> %s</a>'
             % (e(p['유튜브']), e(날짜말), e(p['이름']), IC['yt'], IC['go']),
             '<a class="btn btn-line" href="%s" target="_blank" rel="noopener" aria-label="%s %s 릴스 Instagram에서 보기">%s <span>INSTAGRAM</span></a>'
             % (e(p['인스타']), e(날짜말), e(p['이름']), IC['ig'])]
        if 카드:
            줄.append('<a class="lk-cards" href="%s" target="_blank" rel="noopener" aria-label="%s 카드뉴스 Instagram에서 보기">CARD NEWS <span aria-hidden="true">&#8594;</span></a>'
                      % (e(카드), e(날짜말)))
        return '<div class="fp-cta">%s</div>' % ''.join(줄)

    폰 = 기기목업(종합['표지'], '%s 종합편 표지' % 날짜말, 재생=True, 주소=종합['유튜브'],
                설명='%s 종합편 영상을 YouTube에서 보기' % 날짜말,
                윗줄='%s 어제 이슈 %d개' % (날짜말, len(종합['이슈'])),
                아랫줄='%s 외 %d건' % (종합['이슈'][0]['제목'], len(종합['이슈']) - 1))

    탭, 판 = [], []
    for k, p in enumerate(분야):
        첫 = k == 0
        탭.append('<button class="tab tab--%(s)s" type="button" role="tab" id="tab-%(s)s" aria-controls="panel-%(s)s" '
                  'aria-selected="%(sel)s" tabindex="%(ti)s"><i aria-hidden="true"></i>%(이름)s</button>'
                  % dict(s=p['slug'], sel='true' if 첫 else 'false', ti='0' if 첫 else '-1', 이름=e(p['이름'])))
        판.append("""            <div class="sp sp--%(s)s" role="tabpanel" id="panel-%(s)s" aria-labelledby="tab-%(s)s" tabindex="0"%(hid)s>
              <a class="sp-cover" href="%(yt)s" target="_blank" rel="noopener" aria-label="%(날)s %(이름)s 영상 YouTube에서 보기">
                <img data-src="%(표지)s" width="540" height="960" alt="%(날)s %(이름)s 표지" decoding="async">
              </a>
              <div class="sp-text">
                <p class="fp-k">%(칩)s<span>08:00</span></p>
                <h3>%(헤드)s</h3>
                %(목록)s
                %(단추)s
              </div>
              %(캐릭터)s
            </div>""" % dict(s=p['slug'], hid='' if 첫 else ' data-hidden', yt=e(p['유튜브']), 날=e(날짜말),
                             이름=e(p['이름']), 표지=e(p['표지']), 칩=칩(p), 헤드=e(p['헤드라인']),
                             목록=목록(p, 'sp-list'), 단추=단추(p),
                             캐릭터=편집자(p['slug'], cls='sp-ch')))

    return """      <section class="front" aria-labelledby="fp-title">
        <div class="fp-inner">
          <p class="sec-k"><span>Front page &#183; %(점날짜)s</span><span class="sec-links"><a href="#editions" data-view="editions">지난 편 <span aria-hidden="true">&#8594;</span></a><a href="#growth" data-view="growth">채널 성장 <span aria-hidden="true">&#8594;</span></a></span></p>
          <article class="fp-lead">
            <div class="fp-art">%(폰)s</div>
            <div class="fp-text">
              <p class="fp-k">%(칩)s<span>06:00 Daily</span></p>
              <h2 id="fp-title">%(헤드)s</h2>
              %(목록)s
              %(단추)s
            </div>
            %(캐릭터)s
          </article>
        </div>
      </section>
      <section class="sections" aria-labelledby="sec-title">
        <div class="fp-inner">
          <p class="sec-k"><span id="sec-title">By section</span><span>08:00 Daily</span></p>
          <div class="tabs" role="tablist" aria-label="분야별 편">
            %(탭)s
          </div>
%(판)s
        </div>
      </section>
""" % dict(점날짜=점날짜, 폰=폰, 칩=칩(종합), 헤드=e(종합['헤드라인']), 목록=목록(종합, 'fp-list'),
           단추=단추(종합, today.get('인스타_카드')), 캐릭터=편집자('jonghap', cls='fp-ch', 자세='-point'),
           탭='\n            '.join(탭), 판='\n'.join(판))


# ── 화면(칸) ───────────────────────────────────────────────────────
def view_yesterdigest(cfg, data):
    """들어오면 처음 보이는 화면 — 제호 + 두 판 + 하는 일. (문의는 맨 아래 oauth_note)"""
    sc = json.load(open(os.path.join(HERE, 'data/showcase.json'), encoding='utf-8'))
    today = json.load(open(os.path.join(HERE, 'data/today.json'), encoding='utf-8'))
    # 🔴 2026-09-26 업그레이드 — 옛 «두 판»(formats: 카드뉴스 폰 · 세로 영상 폰)을 «1면 + 분야 탭»으로 바꿨다.
    #    formats() 는 되돌릴 때를 위해 지우지 않고 남긴다(부르지 않는다).
    return nameplate(data['editions'], sc, today['날짜']) + front_page(today) + """
      <section class="section section--about" aria-labelledby="about-title">
        <div class="section-inner">
          <p class="sec-k"><span>What we do</span><span>Three steps</span></p>
          <div class="section-heading reveal">
            <h2 id="about-title">고르고, 확인하고,<br>한입 크기로.</h2>
            <!-- 🔴 여기 있던 구글 OAuth 두 문장은 «맨 아래» oauth_note() 로 옮겼다
                 (유진님 2026-09-12 08:53 · 09:48). 지운 것이 아니라 «옮긴» 것이다 — 되돌리지 마라. -->
            <div class="about-side">
              <p>어제 하루를 한입 크기로 잘라, 아침 6시 종합, 8시 분야별로 놓아둡니다.
                 무엇을 골랐는지와 어떻게 확인했는지를 먼저 챙기고요.</p>
            </div>
            <figure class="about-figure">""" + 편집자('jonghap', '신문을 든 어제한입 캐릭터 «편집자»', 'about-ch') + """</figure>
          </div>
          <div class="steps reveal">
            <article class="card">
              <span class="step-number" aria-hidden="true">01 &#8212;</span>
              <h3>주요 이슈 선별</h3>
              <p>공식 자료와 복수의 보도를 바탕으로 전날의 핵심 이슈를 선별하고 사실관계를 확인합니다.</p>
            </article>
            <article class="card">
              <span class="step-number" aria-hidden="true">02 &#8212;</span>
              <h3>콘텐츠 제작</h3>
              <p>선별한 이슈를 세로형 영상과 카드뉴스에 맞춰 간결하고 이해하기 쉬운 형식으로 제작합니다.</p>
            </article>
            <article class="card">
              <span class="step-number" aria-hidden="true">03 &#8212;</span>
              <h3>검토 후 게시</h3>
              <p>정확성·저작권·표현 검사를 통과한 편만 공식 API로 게시하고, 오류가 확인되면 정정·삭제하고 기록을 남깁니다.</p>
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
        # 🔴 5차 — 편 수·장 수를 적지 않는다(날마다 달라 틀리기 쉽고, 세는 말이 «유치함»의 한 몫이었다)
        더보기 = '카드와 영상 전체는 계정에서 봅니다.'

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
          <p class="sec-k"><span>Past editions</span><span>Newest first</span></p>
          <div class="section-heading reveal">
            <h2>%(제목)s</h2>
            <p>어제를 카드뉴스와 세로 영상으로 정리합니다. 전체는 Instagram과 YouTube에서.</p>
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
            <!-- 🔴 5차 — 안내 글은 «손에 맞게»: 마우스(pointer: fine)는 끌기·화살표, 손가락(pointer: coarse)은 쓸기. home.js 가 고른다 -->
            <p class="ed-hint" data-fine="DRAG &#183; &#8592; &#8594;" data-coarse="SWIPE" data-on="SCROLL TO BROWSE &#183; ESC">DRAG &#183; &#8592; &#8594;</p>
            <div class="ed-nav">
              <button type="button" class="ed-prev" aria-label="이전 편">%(icp)s</button>
              <button type="button" class="ed-next" aria-label="다음 편">%(icn)s</button>
            </div>
            <div class="ed-progress" aria-hidden="true"><i></i></div>
          </div>
        </div>
      </section>""" % dict(제목=e(cfg['제목']), panels='\n'.join(panels), n=len(panels),
                            icp=IC['prev'], icn=IC['next'])


def view_growth(cfg, data):
    """채널 성장 — 유튜브·인스타가 «날마다» 얼마나 자랐는지 (2026-09-26 7차 · 시안).

    🔴 유진님 2026-09-26 15:54 「탭을 하나 추가해서 채널 성장 추이(시청률, 구독자수 변화, 등등을 그래프로) 그래프탭을 넣어서
       우리 채(유튜브,인스타)의 성장과정을 누구나 쉽게볼 수있도록 추가하자.」
    🔴 수는 data/growth.json(tools/make-growth.py 가 계정-추이.tsv 에서 읽음)에서만 온다. 손으로 적지 않는다.
    🔴 그래프는 home.js 가 같은 JSON(아래 <script type=application/json>)으로 SVG 를 그린다.
       JS 가 없으면 그래프 자리에 한 줄 안내 + 맨 아래 표(같은 수)가 보인다.
    🔴 빠진 날은 표에 「—」, 그래프는 «끊는다»(이어 그리지 않는다).
    """
    g = json.load(open(os.path.join(HERE, 'data/growth.json'), encoding='utf-8'))
    날짜 = g['날짜']

    def 짧은날(d):
        return '%d.%d' % (int(d[5:7]), int(d[8:10]))

    def 수(v):
        return '—' if v is None else '{:,}'.format(v)

    칸 = []
    for i, c in enumerate(g['그래프']):
        차 = c['최근']['값'] - c['처음']['값']
        부호 = '+' if 차 > 0 else ('−' if 차 < 0 else '±')
        주의 = ('<p class="gr-note">%s</p>' % e(c['주의'])) if c.get('주의') else ''
        칸.append("""            <article class="gr-card" aria-labelledby="gr-h-%(i)d">
              <p class="gr-k"><span>%(tag)s</span><span>%(끝)s</span></p>
              <h3 id="gr-h-%(i)d">%(이름)s</h3>
              <p class="gr-big"><b>%(최근)s</b><span>%(단위)s</span></p>
              <p class="gr-delta">%(첫)s보다 <b>%(부호)s%(차)s</b></p>
              <figure class="gr-fig" data-series="%(i)d" role="img" aria-label="%(이름)s — %(첫)s %(처음값)s%(단위)s에서 %(끝)s %(최근)s%(단위)s">
                <p class="gr-nojs">그래프는 스크립트가 켜져 있을 때 그려집니다. 같은 수가 아래 표에 있습니다.</p>
              </figure>
              %(주의)s
            </article>""" % dict(i=i, tag=e(c['tag']), 이름=e(c['이름']), 단위=e(c['단위']),
                                 최근=수(c['최근']['값']), 끝=짧은날(c['최근']['날짜']),
                                 첫=짧은날(c['처음']['날짜']), 처음값=수(c['처음']['값']),
                                 부호=부호, 차='{:,}'.format(abs(차)), 주의=주의))

    머리 = ''.join('<th scope="col">%s</th>' % e(c['이름']) for c in g['그래프'])
    줄 = ''.join('<tr><th scope="row"><time datetime="%s">%s</time></th>%s</tr>'
                % (d, 짧은날(d), ''.join('<td>%s</td>' % 수(c['값'][k]) for c in g['그래프']))
                for k, d in enumerate(날짜))
    빠진 = ', '.join(짧은날(d) for d in g['빠진날'])
    빠진말 = ('<p class="gr-gap">%s 은 기록이 없어 비워 두었습니다. 앞뒤를 이어 채우지 않았습니다.</p>' % e(빠진)) if 빠진 else ''
    # 🔴 JSON 을 그대로 싣는다 — «</» 만 막는다(스크립트 태그가 끊기지 않게)
    실을것 = json.dumps({'날짜': 날짜, '빠진날': g['빠진날'],
                       '그래프': [{'이름': c['이름'], '단위': c['단위'], '값': c['값']} for c in g['그래프']]},
                      ensure_ascii=False).replace('</', '<\\/')

    return """      <section class="section section--growth" aria-labelledby="growth-title">
        <div class="section-inner">
          <p class="sec-k"><span>Channel growth</span><span>Since %(첫영)s</span></p>
          <div class="section-heading">
            <h2 id="growth-title">%(제목)s</h2>
            <div class="about-side">
              <p>유튜브와 인스타그램이 날마다 얼마나 자랐는지 그대로 보여 드립니다. 하루 한 번 잰 공개 수치이고, 빠진 날은 비워 둡니다.</p>
            </div>
          </div>
          <div class="gr-grid">
%(칸)s
            <article class="gr-card gr-card--soon" aria-labelledby="gr-h-soon">
              <p class="gr-k"><span>YouTube</span><span class="gr-tag">SOON</span></p>
              <h3 id="gr-h-soon">평균 시청 시간 · 이탈 구간</h3>
              <p class="gr-soon">준비 중입니다. 영상마다 어디까지 보고 넘기는지는 유튜브 분석 데이터를 연결한 뒤에 보여 드립니다.</p>
            </article>
          </div>
          %(빠진말)s
          <div class="gr-table-wrap">
            <table class="gr-table">
              <caption>날짜별 수치 · %(첫)s–%(끝)s</caption>
              <thead><tr><th scope="col">날짜</th>%(머리)s</tr></thead>
              <tbody>%(줄)s</tbody>
            </table>
          </div>
          <script type="application/json" id="growth-data">%(json)s</script>
        </div>
      </section>""" % dict(제목=e(cfg['제목']), 칸='\n'.join(칸), 빠진말=빠진말, 머리=머리, 줄=줄,
                            첫=짧은날(날짜[0]), 끝=짧은날(날짜[-1]), json=실을것,
                            첫영=datetime.date.fromisoformat(날짜[0]).strftime('%b %-d'))


SECTION_BUILDERS = {
    'yesterdigest': view_yesterdigest,
    'editions': view_editions,
    'growth': view_growth,
    # 'stocks': view_stocks,   ← 주식 동향 칸을 열 때 여기에 등록한다
    # 'cv':     view_cv,       ← 연구 이력 칸을 열 때 여기에 등록한다
}


# 🔴 한글 «제목» 글씨 = 배달의민족 주아 — 홈페이지-규칙 §3 (유진님 2026-09-12 09:01 「배달의 민족 주아로 가자」).
#    2026-09-24 3차에 명조를 시험했으나 팀장 정리: «정본은 §3 이고 명조는 제안이다» → 기본을 주아로 되돌렸다.
#    제목 글꼴은 CSS 변수 하나(--font-display · assets/styles.css)가 정한다. 명조 판은 주소 끝 ?font=serif 로만 켜지는
#    «제안»이다 — 그때만 assets/theme.js 가 Noto Serif KR 링크를 붙인다. 기본 페이지는 명조를 받지 않는다.
#    🔴 2026-09-25 5차 — 주아는 «제목 자리(h1·h2·h3)»에만 쓴다. 숫자·날짜·꼬리표·귀 글씨는 Inter/Pretendard 다.
#    «이 페이지가 실제로 제목 글꼴로 그리는 글자»만 받는다 (Google Fonts text=).
#    아래 자리는 assets/home.css 의 --font-display 선택자와 «짝»이다. 거기에 선택자를 더하면 여기도 더한다 —
#    안 그러면 그 글자만 대체 글꼴로 튄다.
제목글꼴_자리 = [r'<h1[^>]*>(.*?)</h1>', r'<h2[^>]*>(.*?)</h2>', r'<h3[^>]*>(.*?)</h3>']

# 제목에 들어올 수 있는 것 — 오늘 페이지에 없어도 넣는다. 🔴 5차: 숫자·날짜 글자는 뺐다(날짜는 Inter 로 그린다)
제목글꼴_바탕 = ('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz' + ' .,·-~!?:')


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
    🔴 2026-09-25 5차 — 캐릭터 «편집자»(신문 읽기 판)를 120px 로 둔다. 크림 종이 한 장 · 위 3px 이중 괘선.
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
""" % 편집자('jonghap', cls='intro-chr', 자세='-point')


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


def 곁쪽_판번호():
    """법문 두 쪽 · 404 의 «머리»에도 홈과 같은 ?v= 판번호를 붙인다 (5차 · 변경 9).

    🔴 <main> 은 한 글자도 안 건드린다 — 앞(머리)과 뒤(바닥)만 고치고, 쓰기 전후 <main> md5 가 같은지 본다.
       다르면 쓰지 않고 멈춘다. (privacy 26d86d5c… · terms 48abde64… 는 .review/진행.md 에 적어 두었다)
    🔴 이 쪽들은 손으로 쓴 HTML 이다. 여기서는 «판번호만» 바꾼다 — 다시 돌려도 내용이 같으면 파일도 같다.
    """
    import hashlib
    해시 = {}
    for 주소 in ('/assets/styles.css', '/assets/theme.js', '/assets/og/home.png'):
        f = os.path.join(HERE, 주소.lstrip('/'))
        if os.path.exists(f):
            해시[주소] = hashlib.md5(open(f, 'rb').read()).hexdigest()[:8]

    def 찍기(조각):
        for 주소, h in 해시.items():
            조각 = re.sub(re.escape(주소) + r'(\?v=[0-9a-f]{8})?"', '%s?v=%s"' % (주소, h), 조각)
        return 조각

    for 파일 in ('privacy/index.html', 'terms/index.html', '404.html'):
        f = os.path.join(HERE, 파일)
        if not os.path.exists(f):
            continue
        t = open(f, encoding='utf-8').read()
        m = re.search(r'<main.*?</main>', t, re.S)
        if not m:
            raise SystemExit('%s 에 <main> 이 없다 — 판번호를 붙이지 않고 멈춘다' % 파일)
        새 = 찍기(t[:m.start()]) + m.group(0) + 찍기(t[m.end():])
        m2 = re.search(r'<main.*?</main>', 새, re.S)
        if hashlib.md5(m.group(0).encode()).hexdigest() != hashlib.md5(m2.group(0).encode()).hexdigest():
            raise SystemExit('%s <main> 이 바뀌려 한다 — 쓰지 않고 멈춘다' % 파일)
        if 새 != t:
            open(f, 'w', encoding='utf-8').write(새)
    print('  곁쪽 판번호 — privacy · terms · 404 머리 (%s)' % ' · '.join(
        '%s?v=%s' % (k.rsplit('/', 1)[-1], v) for k, v in 해시.items()))


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
        YT=YT_CHANNEL, IG=IG_ACCOUNT, CH=BRAND, 기본=기본,
        LOCKUP_L=LOCKUP[0], LOCKUP_D=LOCKUP[1], SEAL_L=SEAL[0], SEAL_D=SEAL[1],
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
    곁쪽_판번호()
    sitemap()


PAGE = """<!doctype html>
<html lang="ko" data-theme="light" data-masthead="lettering">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <!-- 🔴 주소창 색을 «스크립트보다 먼저» 둔다 — 아래 한 줄이 먹 판이면 곧바로 #12161C 로 바꾼다(주소창 번쩍임 방지 · 5차). -->
  <meta name="theme-color" content="#F3EEE3">
  <!-- 🔴 판(밝은 크림 / 어두운 먹)을 «그리기 전에» 박는다 — 다크를 고른 사람이 새로고침할 때 크림이 번쩍이지 않게.
       첫 방문은 OS 설정과 상관없이 «크림»이다 (유진님 2026-09-24 「웹색상은 밝은 크림시문지로 바꾸되 다크모드 기눙도 넣어줘」).
       저장소가 막혀 있으면(사생활 창 등) 조용히 크림으로 간다. 누르는 단추는 /assets/theme.js 가 맡는다.
       🔴 2026-09-26 — 레터링 제호가 «기본»이 됐다(<html data-masthead="lettering"> · JS 없어도 보인다).
          근거: 유진님 16:09 「A안, 스레드 프로필 내가 바꿀게 그 외는 너가 전부 추천하는대로 바꿔」 → 팀장 추천 ① 레터링. 제목 글씨는 주아 그대로(②). -->
  <script>(function(){var d=document.documentElement,t='light';try{if(localStorage.getItem('yd-theme')==='dark')t='dark';}catch(e){}d.setAttribute('data-theme',t);if(t==='dark'){var m=document.querySelector('meta[name="theme-color"]');if(m)m.setAttribute('content','#14171C');}try{if(/[?&]masthead=lettering(&|$)/.test(location.search))d.setAttribute('data-masthead','lettering');}catch(e){}})();</script>
  <title>%(CH)s | YesterDigest</title>
  <meta name="description" content="어제의 뉴스를 한입 크기로. 매일 아침 6시 종합, 8시 분야별로 Instagram과 YouTube에 올라갑니다.">
  <link rel="canonical" href="https://yesterdigest.com/">

  <!-- 카톡·트위터·페북에 «주소를 붙였을 때» 뜨는 것.
       🔴 그림은 1200x630 이어야 «큰 카드»로 뜬다. 그림 원본은 tools/og-card.html(5차 — 레터링 윤곽 인라인 SVG · 웹폰트 없음)
          · 다시 만들기는 `python3 tools/make-assets.py`.
       🔴 주소 뒤 ?v= 는 build.py 가 «파일 내용 해시»로 붙인다 (카카오·페북 캐시 대비).
       🔴 공유 미리보기는 판을 모르므로 먹 판 og 는 두지 않는다. -->
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="YesterDigest">
  <meta property="og:locale" content="ko_KR">
  <meta property="og:title" content="%(CH)s | YesterDigest">
  <meta property="og:description" content="어제의 뉴스를 한입 크기로.">
  <meta property="og:url" content="https://yesterdigest.com/">
  <meta property="og:image" content="https://yesterdigest.com/assets/og/home.png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="어제한입 — 어제의 뉴스를 한입 크기로">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="%(CH)s | YesterDigest">
  <meta name="twitter:description" content="어제의 뉴스를 한입 크기로.">
  <meta name="twitter:image" content="https://yesterdigest.com/assets/og/home.png">

  <!-- 🔴 /favicon.ico 는 «선언과 상관없이» 받아 간다 — 16(「ㅎ·점」 한 글자 판) · 32 · 48(네 글자 인장) 세 장. tools/make-assets.py 가 만든다.
       🔴 SVG 파비콘은 icon.svg(네 글자 인장)가 아니라 icon-16.svg(ㅎ 한 글자 · 화소 맞춤)다 —
          브라우저 탭은 SVG 하나를 16px 로 그리므로 네 글자 판을 주면 16px 에서 잡음이 된다(5차 변경 2 「16~24px 는 ㅎ 한 글자」).
          32px 이상 자리(홈 화면·북마크 큰 칸)는 192·180 PNG 가 맡는다. -->
  <link rel="icon" href="/favicon.ico" sizes="16x16 32x32 48x48">
  <link rel="icon" href="/assets/brand/icon-16.svg" type="image/svg+xml">
  <link rel="icon" href="/assets/brand/icon-192.png" type="image/png" sizes="192x192">
  <link rel="apple-touch-icon" href="/apple-touch-icon.png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>
  <!-- 글씨체 — 2026-09-25 5차 (유진님 「최대한 고급스럽게」)
       · 한글 제목  배달의민족 주아(Jua) 400 — 홈페이지-규칙 §3 정본 · SIL OFL 1.1 · Google Fonts 배포본 · «h1·h2·h3 제목 글자만» text= 로 받는다
                    (명조 Noto Serif KR 은 «제안» — 주소 끝 ?font=serif 일 때만 theme.js 가 붙인다. 기본 페이지는 받지 않는다)
       · 한글 본문  Pretendard — SIL OFL 1.1 · jsDelivr(orioncactus/pretendard v1.3.9) «dynamic subset»: 화면에 나온 글자 조각만 받는다
       · 영문 꼬리표·숫자 Inter 500·600·700 — SIL OFL 1.1 · Google Fonts (라틴만)
       🔴 Pretendard·Inter 는 «렌더를 막지 않게» 받는다 — preload + media="print" → 받으면 all. 스크립트가 꺼진 곳은 <noscript> 가 받는다.
          주아는 제호(h1)라 막는 채로 둔다 — 제호가 대체 글꼴로 번쩍이지 않게. 바깥 스크립트는 0 이다(onload 는 인라인 속성 한 줄).
       🔴 옛 태그라인용 영문 명조(4차)는 뺐다(5차 — 태그라인은 Inter 대문자, 규칙 §3 영문 = Inter).
       🔴 홈페이지에만 쓴다. 영상·카드뉴스 글씨체는 안 건드린다. -->
  <link rel="preload" as="style" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
  <link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=Inter:wght@500;600;700&display=swap">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css" media="print" onload="this.media='all'">
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@500;600;700&display=swap" media="print" onload="this.media='all'">
  <noscript>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@500;600;700&display=swap">
  </noscript>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Jua&display=swap&text=__DISPLAY_TEXT__">
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
     "description":"어제의 뉴스를 한입 크기로. Instagram과 YouTube에 올라갑니다.",
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
      <!-- 🔴 aria-label 을 «안» 붙인다 — 그림의 alt 가 이름이다 (WCAG 2.5.3 Label in Name: 보이는 글자 「어제한입」이 이름에 들어 있다).
           🔴 5차 — 인장 + 작은 판 워드마크 한 벌(lockup). 크림·먹 두 장을 [data-theme] 로 번갈아 보인다(먹 판에서 로고가 사라지던 문제).
              숨은 쪽은 display:none 이라 읽기 도구에도 한 번만 읽힌다. 파일은 build.py 의 LOCKUP 한 줄이 정한다. -->
      <a class="brand-link" href="#%(기본)s" data-view="%(기본)s">
        <img class="brand-lockup on-light" src="%(LOCKUP_L)s" alt="어제한입 YesterDigest" width="133" height="42">
        <img class="brand-lockup on-dark" src="%(LOCKUP_D)s" alt="어제한입 YesterDigest" width="133" height="42">
      </a>
      <div class="nav-actions">
        <!-- 🔴 판 바꾸기 — 보이는 글씨(DARK/LIGHT)가 이름의 앞머리다(aria-label 도 그 글씨로 시작한다). 44px 이상 · 초점 보임 · theme.js 가 글씨와 이름을 바꾼다 -->
        <button class="theme-btn" type="button" data-theme-toggle aria-label="DARK · 다크 모드로 바꾸기">%(icmoon)s%(icsun)s<span class="theme-label">DARK</span></button>
        <a class="icon-link ig" href="%(IG)s" target="_blank" rel="noopener" aria-label="Instagram 계정 열기">%(icig)s</a>
        <a class="icon-link yt" href="%(YT)s" target="_blank" rel="noopener" aria-label="YouTube 채널 열기">%(icyt)s</a>
      </div>
    </nav>
  </header>

  <!-- 목록 — data/sections.json 의 «보임: true» 인 칸만 나온다.
       🔴 5차 — 진짜 «창»이다: role=dialog · aria-modal · 열린 동안 머리줄·본문·바닥에 inert (home.js) -->
  <div class="drawer-backdrop" id="drawer-backdrop" hidden></div>
  <div class="drawer" id="drawer" hidden role="dialog" aria-modal="true" aria-labelledby="drawer-title">
    <div class="drawer-head">
      <span class="drawer-title" id="drawer-title">MENU</span>
      <button class="menu-btn" type="button" id="menu-close" aria-label="메뉴 닫기">%(icx)s</button>
    </div>
    <nav class="drawer-nav" aria-label="화면 목록">
%(menu)s
    </nav>
    <div class="drawer-foot">
      <a class="btn btn-ig" href="%(IG)s" target="_blank" rel="noopener">%(icig)s Instagram</a>
      <a class="btn btn-yt" href="%(YT)s" target="_blank" rel="noopener">%(icyt)s YouTube</a>
    </div>
  </div>

  <main id="main">
%(views)s
  </main>

%(자리)s

%(intro)s
%(oauth)s
  <footer class="site-footer">
    <div class="footer-inner">
      <p class="footer-brand"><img class="brand-seal on-light" src="%(SEAL_L)s" alt="" width="24" height="24"><img class="brand-seal on-dark" src="%(SEAL_D)s" alt="" width="24" height="24">© 2026 YesterDigest</p>
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
