# -*- coding: utf-8 -*-
"""채널 성장(GROWTH) 화면 — 데이터 만들기.  (2026-09-26 업그레이드 시안 7차)

  python3 tools/make-growth.py            # -> data/growth.json
  python3 build.py                        # -> index.html (숫자·표는 build.py 가 이 JSON 에서 넣는다)

읽는 것 (작업 저장소 · 읽기만):
  ~/projects/yesterdigest/docs/records/계정-추이.tsv
    — 하루 한 줄: 날짜 · 인스타_팔로워 · 인스타_게시물 · 유튜브_구독 · 유튜브_총조회 · 유튜브_영상수
    — scripts/metrics-accounts.py 가 쓴다(공개 통계 · 우리 계정). '#' 줄은 메모라 건너뛴다.
쓰는 것 (이 사이트 저장소):
  data/growth.json

🔴 수를 손으로 적지 않는다 — 기록 파일에서 «읽는다». 외부 API 를 부르지 않는다(.env·토큰 0).
🔴 빠진 날(예: 2026-09-23)은 «빈 칸(null)»으로 둔다. 앞뒤를 이어 채우지(보간) 않는다.
   날짜 칸은 첫날~마지막 날을 «하루도 빼지 않고» 세우므로, 기록이 없는 날은 그래프에 «끊김»으로 보인다.
🔴 유튜브 «총조회»는 채널 통계(channel.statistics.viewCount)다. 갱신이 늦고 쇼츠 조회를 다르게 세어
   09-19→09-21 에 «줄었다». 기록 파일 메모 그대로 — 화면에 한 줄 주의를 단다(판정에 쓰지 않는 값).

🔴 이탈율·평균 시청 시간(유지율)은 «없다». YouTube Analytics API(yt-analytics.readonly · OAuth)가 있어야 하고
   우리 기록 어디에도 그 값이 없다(2026-09-26 grep). 화면에는 «준비 중» 칸만 둔다.

── 자동 갱신 (적어만 둔다 · 켜지 않았다) ──────────────────────────────
  이 스크립트는 «비공개 작업 저장소»의 기록 파일을 읽으므로 GitHub Actions(공개 사이트 저장소)에서는 못 돈다.
  돌 수 있는 자리는 기록 파일이 있는 이 노트북뿐이다. 붙인다면:
    ① 07:32 예약(T+24h 수치 · metrics-accounts.py 가 계정-추이.tsv 에 한 줄 더함) «바로 뒤»에
    ② python3 tools/make-growth.py && python3 build.py
    ③ 사이트 저장소 푸시 — 🔴 푸시는 게시다(유진님 확인 사항). 지금은 켜지 않았다.
"""
import datetime, json, os, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.expanduser('~/projects/yesterdigest')
TSV = os.path.join(WORK, 'docs/records/계정-추이.tsv')
OUT = os.path.join(HERE, 'data/growth.json')

# 그래프 넷 — 순서가 곧 화면 순서. 이름은 읽는 한글(규칙 §4), 꼬리표(tag)는 영어.
그래프 = [
    dict(키='유튜브_구독', 이름='유튜브 구독자', tag='YouTube', 단위='명', 주의=None),
    dict(키='인스타_팔로워', 이름='인스타그램 팔로워', tag='Instagram', 단위='명', 주의=None),
    dict(키='유튜브_총조회', 이름='유튜브 누적 조회수', tag='YouTube', 단위='회',
         주의='채널 전체 조회수는 유튜브가 늦게 반영해, 하루 이틀 줄어 보일 때가 있습니다.'),
    dict(키='유튜브_영상수', 이름='올린 영상 수(누적)', tag='YouTube', 단위='편', 주의=None),
]


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else TSV
    머리, 줄 = None, {}
    for line in open(src, encoding='utf-8'):
        line = line.rstrip('\n')
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        칸 = line.split('\t')
        if 머리 is None:
            머리 = 칸
            continue
        r = dict(zip(머리, 칸))
        datetime.date.fromisoformat(r['날짜'])           # 날짜 꼴이 아니면 여기서 멈춘다
        줄[r['날짜']] = r
    if not 줄:
        raise SystemExit('기록 줄이 하나도 없다: ' + src)
    for g in 그래프:
        if g['키'] not in 머리:
            raise SystemExit('기록 파일에 칸이 없다: %s' % g['키'])

    첫 = datetime.date.fromisoformat(min(줄))
    끝 = datetime.date.fromisoformat(max(줄))
    날짜 = [(첫 + datetime.timedelta(days=i)).isoformat() for i in range((끝 - 첫).days + 1)]
    빠진날 = [d for d in 날짜 if d not in 줄]

    def 값(d, k):
        v = 줄.get(d, {}).get(k, '').strip()
        return int(v) if v else None

    out = {
        '_만든이': 'tools/make-growth.py — 손으로 고치지 않는다',
        '출처': '어제한입 계정 기록 — 하루 한 번 잰 공개 통계(구독자·팔로워·조회수·영상 수)',
        '만든때': datetime.datetime.now().strftime('%Y-%m-%d %H:%M KST'),
        '첫날': 날짜[0], '마지막날': 날짜[-1], '빠진날': 빠진날,
        '날짜': 날짜,
        '그래프': [],
        '유지율': {'있음': False,
                 '필요한것': 'YouTube Analytics API(yt-analytics.readonly) 동의 + 편별 averageViewDuration · '
                          'averageViewPercentage · audienceWatchRatio 를 날마다 기록하는 줄'},
    }
    for g in 그래프:
        vals = [값(d, g['키']) for d in 날짜]
        있는 = [(d, v) for d, v in zip(날짜, vals) if v is not None]
        out['그래프'].append(dict(g, 값=vals,
                                 처음=dict(날짜=있는[0][0], 값=있는[0][1]),
                                 최근=dict(날짜=있는[-1][0], 값=있는[-1][1])))
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    open(OUT, 'a', encoding='utf-8').write('\n')
    print('data/growth.json — %s ~ %s · %d일 · 빠진 날 %s' % (날짜[0], 날짜[-1], len(날짜), 빠진날 or '없음'))
    for g in out['그래프']:
        print('  %-8s %s → %s' % (g['키'], g['처음']['값'], g['최근']['값']))


if __name__ == '__main__':
    main()
