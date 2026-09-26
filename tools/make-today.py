# -*- coding: utf-8 -*-
"""1면(오늘 종합) + 분야 탭 셋 — 데이터 만들기.  (2026-09-26 업그레이드 시안)

  python3 tools/make-today.py [날짜]        # 날짜 생략 = 게시 기록에서 가장 최근 편

읽는 것 (작업 저장소 · 읽기만):
  ~/projects/yesterdigest/docs/records/publish-log.jsonl        — 편별 실제 주소 («올림»만 · 시험용 제외)
  ~/projects/yesterdigest/docs/reports/<날짜>[-<분야>]-cuts.json — 이슈 제목(head) · 표지 헤드라인
  ~/projects/yesterdigest/renders/thumb-<날짜>-<편>.jpg          — 게시한 표지(1080×1920)
쓰는 것 (이 사이트 저장소):
  data/today.json · assets/front/<날짜>-<편>.jpg (540×960 · 약 60KB)

🔴 주소를 손으로 적지 않는다 — 게시 기록에서 «읽는다».
🔴 scripts/build-site-editions.py(라이브용)는 파일 이름의 날짜로만 편을 묶어 «네 편이 한 날짜로 겹쳐»
   유튜브 주소가 마지막 편 것으로 덮인다. 여기서는 파일 이름의 «편 이름»(종합·정치사회·경제세계·연예스포츠)까지 읽는다.
"""
import json, os, re, sys, subprocess

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.expanduser('~/projects/yesterdigest')
LOG = os.path.join(WORK, 'docs/records/publish-log.jsonl')
PY_IMG = os.path.join(WORK, 'tts/CosyVoice/.venv/bin/python')   # PIL 이 있는 파이썬(새 설치 없음)

# 편 — 순서가 곧 탭 순서다. 이름은 화면에 나가는 한글(브랜드·분야 이름은 한글 — 규칙 §4)
편목록 = [
    ('종합', '종합', 'jonghap', '06:00'),
    ('정치사회', '정치·사회', 'jeongchi', '08:00'),
    ('경제세계', '경제·세계', 'gyeongje', '08:00'),
    ('연예스포츠', '연예·문화·스포츠', 'yeonye', '08:00'),
]
RE = re.compile(r'reel-(20\d\d-\d\d-\d\d)-(종합|정치사회|경제세계|연예스포츠)')
RE_CARD = re.compile(r'out-(\d\d)(\d\d)\b')


def main():
    기록 = []
    for line in open(LOG, encoding='utf-8'):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if r.get('시험용') or r.get('종류') == 'dummy' or r.get('결과', {}).get('상태') != '올림':
            continue
        기록.append(r)

    편주소 = {}   # (날짜, 편) → {youtube, instagram}
    카드 = {}     # 날짜 → 인스타 카드 주소
    for r in 기록:
        url = r['결과'].get('url')
        for f in r.get('파일') or []:
            m = RE.search(os.path.basename(f))
            if m and r.get('종류') == 'reels':
                편주소.setdefault(m.groups(), {})[r['플랫폼']] = url
            m2 = RE_CARD.search(f)
            if m2 and r.get('종류') == 'cardnews' and r['플랫폼'] == 'instagram':
                카드['2026-%s-%s' % m2.groups()] = url
            break

    날짜 = sys.argv[1] if len(sys.argv) > 1 else max(d for d, _ in 편주소)
    os.makedirs(os.path.join(HERE, 'assets/front'), exist_ok=True)
    out = {'_만든이': 'tools/make-today.py — 손으로 고치지 않는다', '날짜': 날짜, '편': []}
    for 키, 이름, slug, 시각 in 편목록:
        주소 = 편주소.get((날짜, 키), {})
        cuts = os.path.join(WORK, 'docs/reports', '%s-cuts.json' % 날짜 if 키 == '종합'
                            else '%s-%s-cuts.json' % (날짜, 키))
        c = json.load(open(cuts, encoding='utf-8'))
        표지원본 = os.path.join(WORK, 'renders', 'thumb-%s-%s.jpg' % (날짜, 키))
        표지 = 'assets/front/%s-%s.jpg' % (날짜, slug)
        subprocess.run([PY_IMG, '-c', (
            'from PIL import Image;im=Image.open(%r).convert("RGB");'
            'im.resize((540,960),Image.LANCZOS).save(%r,quality=82,optimize=True,progressive=True)')
            % (표지원본, os.path.join(HERE, 표지))], check=True)
        out['편'].append({
            '키': 키, '이름': 이름, 'slug': slug, '시각': 시각,
            '헤드라인': ' '.join(c.get('thumb_headline') or []) if 키 == '종합' else c['issues'][0]['head'],
            '이슈': [{'제목': i['head'], '분야': i.get('분야', '')} for i in c['issues']],
            '유튜브': 주소.get('youtube'), '인스타': 주소.get('instagram'),
            '표지': '/' + 표지,
        })
    out['인스타_카드'] = 카드.get(날짜)
    빠짐 = ['%s %s' % (p['키'], k) for p in out['편'] for k in ('유튜브', '인스타') if not p[k]]
    json.dump(out, open(os.path.join(HERE, 'data/today.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('data/today.json — %s · 편 %d · 카드 %s' % (날짜, len(out['편']), bool(out['인스타_카드'])))
    for p in out['편']:
        print('  %-6s YT %s · IG %s' % (p['키'], p['유튜브'], p['인스타']))
    if 빠짐:
        sys.exit('⚠ 주소 없음: ' + ', '.join(빠짐))


if __name__ == '__main__':
    main()
