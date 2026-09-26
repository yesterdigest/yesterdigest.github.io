#!/usr/bin/env python3
"""파비콘·홈화면 아이콘·공유 그림을 «한 번에» 다시 만든다.

    python3 tools/make-assets.py

만드는 것 (2026-09-25 5차 — D4 v2 로고 · 원본은 assets/brand/*.svg)
    /favicon.ico                 16 · 32 · 48 세 장이 든 한 파일 (주소창·탭·즐겨찾기·크롤러)
                                 16 = icon-16.svg(「ㅎ·점」 한 글자 · 화소 맞춤) · 32/48 = icon.svg(네 글자 인장)
    /apple-touch-icon.png        180x180 (아이폰 «홈 화면에 추가») — icon.svg
    /assets/brand/icon-192.png   192x192 (안드로이드·<link rel=icon> PNG) — icon.svg
    /assets/brand/logo-256.png   256x256 (schema.org Organization.logo) — icon.svg
    /assets/og/home.png          1200x630 (카톡·트위터·페북 — tools/og-card.html 이 원본 · 웹폰트 없음)

🔴 방향을 바꿀 때 — tools/brand-map.json 의 표를 보고 assets/brand/ 의 정식 이름 파일을 갈아 끼운 뒤
   이 파일과 `python3 build.py` 를 다시 돌린다. 여기는 «정식 이름»만 부른다.
🔴 왜 하나로 묶었나 — 셋 다 «같은 로고»에서 나온다. 따로 만들면 로고를 바꿨을 때 하나만 낡은 채 남는다.
🔴 왜 ffmpeg 이 아니라 크롬인가 — Remotion 이 번들한 ffmpeg 은 필터가 50개뿐이라
   `pad`(배경 깔기)도 `overlay` 도 «없다». 크롬은 이미 있고 셋을 다 한다.
   새로 깔지 않는다 (CLAUDE.md §2-1 «패키지 설치는 승인 사항»).
🔴 돌리기 «전»에 자원 확인(free -m · 음성 작업 · 게시 시각)을 «따로» 한다 — 크롬을 띄우는 무거운 일이다.
   끝나면 크롬이 남지 않았는지 본다 (이 스크립트는 임시 프로필로 띄우고 끝나면 스스로 닫힌다).
"""
import os, struct, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ICON16 = os.path.join(ROOT, 'assets/brand/icon-16.svg')   # 16~24px 판 — ㅎ 한 글자
ICON = os.path.join(ROOT, 'assets/brand/icon.svg')        # 32px 이상 — 네 글자 인장(먹 타일 · 가장자리까지 채움)
CHROME = '/usr/bin/google-chrome'


def shot(html, w, h, out, transparent=False):
    """HTML 한 토막을 w x h 그림 한 장으로."""
    with tempfile.TemporaryDirectory() as td:
        page = os.path.join(td, 'p.html')
        open(page, 'w', encoding='utf-8').write(html)
        cmd = [CHROME, '--headless', '--disable-gpu', '--no-sandbox', '--hide-scrollbars',
               '--user-data-dir=' + os.path.join(td, 'profile'),
               '--force-device-scale-factor=1',
               '--window-size=%d,%d' % (w, h), '--screenshot=' + out,
               '--virtual-time-budget=4000']
        if transparent:
            cmd.append('--default-background-color=00000000')
        cmd.append('file://' + page)
        r = subprocess.run(cmd, capture_output=True, text=True)
        if not os.path.exists(out) or os.path.getsize(out) < 60:
            sys.exit('그림이 안 나왔다 (%dx%d)\n%s' % (w, h, r.stderr[-1200:]))


ICON_HTML = """<meta charset="utf-8"><style>
html,body{margin:0;width:%dpx;height:%dpx;overflow:hidden;background:transparent}
img{width:100%%;height:100%%;display:block;image-rendering:%s}
</style><img src="file://%s" alt="">"""


def icon(size, out, src=ICON):
    crisp = 'pixelated' if src == ICON16 else 'auto'
    shot(ICON_HTML % (size, size, crisp, src), size, size, out, transparent=True)


def ico(items, out):
    """ICO = 헤더 + 크기별 PNG 를 그대로 담은 통. 라이브러리가 필요 없다. items = [(크기, 원본 svg)]"""
    with tempfile.TemporaryDirectory() as td:
        blobs = []
        for s, src in items:
            p = os.path.join(td, '%d.png' % s)
            icon(s, p, src)
            blobs.append(open(p, 'rb').read())
    head = struct.pack('<HHH', 0, 1, len(items))          # reserved · type=icon · 장수
    off = len(head) + 16 * len(items)
    entries = b''
    for (s, _), b in zip(items, blobs):
        # 폭·높이는 1바이트다 — 256 은 0 으로 적는 규칙이다 (여기선 48 까지라 그대로)
        entries += struct.pack('<BBBBHHII', s, s, 0, 0, 1, 32, len(b), off)
        off += len(b)
    open(out, 'wb').write(head + entries + b''.join(blobs))


def ico_읽어보기(path):
    """손으로 짠 통을 «되읽어» 확인한다 — 헤더 숫자가 한 칸만 어긋나도 조용히 깨진 아이콘이 나간다."""
    d = open(path, 'rb').read()
    res, typ, n = struct.unpack('<HHH', d[:6])
    assert (res, typ) == (0, 1), 'ICO 머리가 아니다'
    크기 = []
    for i in range(n):
        w, h, _, _, _, _, size, off = struct.unpack('<BBBBHHII', d[6 + 16 * i:22 + 16 * i])
        blob = d[off:off + size]
        assert blob[:8] == b'\x89PNG\r\n\x1a\n', '%d번째가 PNG 가 아니다' % i
        assert struct.unpack('>II', blob[16:24]) == (w, h), '%d번째 크기가 머리와 다르다' % i
        크기.append(w)
    return 크기


def main():
    for f, what in ((CHROME, '크롬'), (ICON, '아이콘'), (ICON16, '16px 아이콘')):
        if not os.path.exists(f):
            sys.exit('%s 가 없다: %s' % (what, f))
    os.makedirs(os.path.join(ROOT, 'assets/og'), exist_ok=True)

    ico([(16, ICON16), (32, ICON), (48, ICON)], os.path.join(ROOT, 'favicon.ico'))
    print('  favicon.ico 안의 크기 —', ico_읽어보기(os.path.join(ROOT, 'favicon.ico')))
    icon(180, os.path.join(ROOT, 'apple-touch-icon.png'))
    icon(192, os.path.join(ROOT, 'assets/brand/icon-192.png'))
    icon(256, os.path.join(ROOT, 'assets/brand/logo-256.png'))
    shot(open(os.path.join(HERE, 'og-card.html'), encoding='utf-8').read(),
         1200, 630, os.path.join(ROOT, 'assets/og/home.png'))

    for p in ('favicon.ico', 'apple-touch-icon.png', 'assets/brand/icon-192.png',
              'assets/brand/logo-256.png', 'assets/og/home.png'):
        f = os.path.join(ROOT, p)
        assert os.path.getsize(f) > 200, p + ' 가 비었다'   # 조용히 0바이트가 나오는 것을 막는다
        print('  %-28s %6.1f KB' % ('/' + p, os.path.getsize(f) / 1024))


if __name__ == '__main__':
    main()
