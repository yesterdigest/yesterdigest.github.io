#!/usr/bin/env python3
"""파비콘·홈화면 아이콘·공유 그림을 «한 번에» 다시 만든다.

    python3 tools/make-assets.py

만드는 것
    /favicon.ico            16·32·48 세 장이 든 한 파일 (주소창·탭·즐겨찾기·크롤러)
    /apple-touch-icon.png   180x180  (아이폰 «홈 화면에 추가»)
    /assets/og/home.png     1200x630 (카톡·트위터·페북에 붙였을 때 뜨는 그림 — tools/og-card.html 이 원본)

🔴 왜 하나로 묶었나 — 셋 다 «같은 로고»에서 나온다. 따로 만들면 로고를 바꿨을 때
   하나만 낡은 채 남는다. 로고나 og-card.html 을 고쳤으면 이 파일 하나만 돌린다.

🔴 왜 ffmpeg 이 아니라 크롬인가 — Remotion 이 번들한 ffmpeg 은 필터가 50개뿐이라
   `pad`(배경 깔기)도 `overlay` 도 «없다». 크롬은 이미 있고 셋을 다 한다.
   새로 깔지 않는다 (CLAUDE.md §2-1 «패키지 설치는 승인 사항»).
"""
import os, struct, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
# 🔴 2026-09-25 4차 — 새 로고(베어 문 원). 파비콘·홈화면 아이콘은 «먹 네모» 판(icon.svg)에서 만든다.
#    옛 값: assets/logo.png (캐릭터 얼굴 배지 460x460)
LOGO = os.path.join(ROOT, 'assets/brand/icon.svg')
BADGE = os.path.join(ROOT, 'assets/brand/badge.svg')
PAPER = '#12161c'   # 먹 — icon.svg 바탕과 같다. 🔴 아이폰은 투명을 «검정»으로 칠한다
CHROME = '/usr/bin/google-chrome'


def shot(html, w, h, out, transparent=False):
    """HTML 한 토막을 w x h 그림 한 장으로."""
    with tempfile.TemporaryDirectory() as td:
        page = os.path.join(td, 'p.html')
        open(page, 'w', encoding='utf-8').write(html)
        cmd = [CHROME, '--headless', '--disable-gpu', '--no-sandbox', '--hide-scrollbars',
               '--user-data-dir=' + os.path.join(td, 'profile'),
               '--window-size=%d,%d' % (w, h), '--screenshot=' + out,
               '--virtual-time-budget=8000']
        if transparent:
            cmd.append('--default-background-color=00000000')
        cmd.append('file://' + page)
        r = subprocess.run(cmd, capture_output=True, text=True)
        if not os.path.exists(out) or os.path.getsize(out) < 200:
            sys.exit('그림이 안 나왔다 (%dx%d)\n%s' % (w, h, r.stderr[-1200:]))


ICON = """<meta charset="utf-8"><style>
html,body{margin:0;height:100%%;background:%s}
img{width:%s;height:%s;margin:%s;display:block}
</style><img src="file://%s" alt="">"""


def icon(size, out, bg='transparent'):
    inset = '5%' if bg != 'transparent' else '0'        # 배경이 있을 때만 가장자리를 띄운다
    box = '90%' if bg != 'transparent' else '100%'
    shot(ICON % (bg, box, box, inset, LOGO), size, size, out, transparent=(bg == 'transparent'))


def ico(sizes, out):
    """ICO = 헤더 + 크기별 PNG 를 그대로 담은 통. 라이브러리가 필요 없다."""
    with tempfile.TemporaryDirectory() as td:
        blobs = []
        for s in sizes:
            p = os.path.join(td, '%d.png' % s)
            icon(s, p)
            blobs.append(open(p, 'rb').read())
    head = struct.pack('<HHH', 0, 1, len(sizes))         # reserved · type=icon · 장수
    off = len(head) + 16 * len(sizes)
    entries = b''
    for s, b in zip(sizes, blobs):
        # 폭·높이는 1바이트다 — 256 은 0 으로 적는 규칙이다 (여기선 48 까지라 그대로)
        entries += struct.pack('<BBBBHHII', s, s, 0, 0, 1, 32, len(b), off)
        off += len(b)
    open(out, 'wb').write(head + entries + b''.join(blobs))


def ico_읽어보기(path):
    """손으로 짠 통을 «되읽어» 확인한다 — 헤더 숫자가 한 칸만 어긋나도 조용히 깨진 아이콘이 나간다."""
    d = open(path, 'rb').read()
    res, typ, n = struct.unpack('<HHH', d[:6])
    assert (res, typ) == (0, 1), 'ICO 머리가 아니다'
    for i in range(n):
        w, h, _, _, _, _, size, off = struct.unpack('<BBBBHHII', d[6 + 16 * i:22 + 16 * i])
        blob = d[off:off + size]
        assert blob[:8] == b'\x89PNG\r\n\x1a\n', '%d번째가 PNG 가 아니다' % i
        assert struct.unpack('>II', blob[16:24]) == (w, h), '%d번째 크기가 머리와 다르다' % i
    return n


def main():
    for f, what in ((CHROME, '크롬'), (LOGO, '로고')):
        if not os.path.exists(f):
            sys.exit('%s 가 없다: %s' % (what, f))
    os.makedirs(os.path.join(ROOT, 'assets/og'), exist_ok=True)

    ico([16, 32, 48], os.path.join(ROOT, 'favicon.ico'))
    ico_읽어보기(os.path.join(ROOT, 'favicon.ico'))
    icon(180, os.path.join(ROOT, 'apple-touch-icon.png'), bg=PAPER)
    icon(256, os.path.join(ROOT, 'assets/brand/logo-256.png'))   # schema.org Organization.logo · 파비콘 PNG
    shot(open(os.path.join(HERE, 'og-card.html'), encoding='utf-8').read()
         .replace('../assets/', 'file://' + ROOT + '/assets/'),
         1200, 630, os.path.join(ROOT, 'assets/og/home.png'))

    for p in ('favicon.ico', 'apple-touch-icon.png', 'assets/brand/logo-256.png', 'assets/og/home.png'):
        f = os.path.join(ROOT, p)
        assert os.path.getsize(f) > 400, p + ' 가 비었다'   # 조용히 0바이트가 나오는 것을 막는다
        print('  %-26s %6.1f KB' % ('/' + p, os.path.getsize(f) / 1024))


if __name__ == '__main__':
    main()
