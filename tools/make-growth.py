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

🔴 수를 손으로 적지 않는다 — 기록 파일과 API 응답에서 «읽는다».
🔴 2026-10-02 — YouTube Analytics API(yt-analytics.readonly · 10-01 유진님 권한 추가)를 «읽기만» 부른다.
   인증은 작업 저장소 scripts/publish.py 의 _load_env + publishers.youtube.access_token 을 그대로 쓴다
   (metrics-accounts.py 와 같은 길). 토큰은 메모리에만 — 찍지도 파일에 쓰지도 않는다(§3.7).
   API 가 실패하면 직전 growth.json 의 «분석» 묶음을 그대로 두고(가져온 때도 옛 값 그대로) 경고만 찍는다.
   유진님 10-02 id 4674·4677 「추가할 수 있는 그래프 … 몇일 몇시 기준 … 언제부터 시작했는지」.
🔴 빠진 날(예: 2026-09-23)은 «빈 칸(null)»으로 둔다. 앞뒤를 이어 채우지(보간) 않는다.
   날짜 칸은 첫날~마지막 날을 «하루도 빼지 않고» 세운다. 기록이 없는 날은 점 없이 띠만 — 선은 home.js 가 앞뒤를 «이어» 그린다
   (유진님 2026-09-27 08:32 「그냥 지우지말고 선이라도 이어줘」). 값은 여전히 null — 채워 넣지 않는다.
🔴 유튜브 «총조회»는 채널 통계(channel.statistics.viewCount)다. 갱신이 늦고 쇼츠 조회를 다르게 세어
   09-19→09-21 에 «줄었다». 기록 파일 메모 그대로 — 화면에 한 줄 주의를 단다(판정에 쓰지 않는 값).

🔴 API 가 «안 주는» 값 — 노출수·노출 클릭률(videoThumbnailImpressions* 는 400 «query is not supported» · 10-02 실측),
   Shorts «본 비율(viewed vs swiped away)»(API 에 지표 없음). 화면에 «API 미제공»으로 적는다. 지어내지 않는다.
🔴 분석의 «날짜»는 유튜브 분석 기준 하루(미국 태평양 시간)다. 화면에 한 줄 적는다.

── 자동 갱신 (적어만 둔다 · 켜지 않았다) ──────────────────────────────
  이 스크립트는 «비공개 작업 저장소»의 기록 파일을 읽으므로 GitHub Actions(공개 사이트 저장소)에서는 못 돈다.
  돌 수 있는 자리는 기록 파일이 있는 이 노트북뿐이다. 붙인다면:
    ① 07:32 예약(T+24h 수치 · metrics-accounts.py 가 계정-추이.tsv 에 한 줄 더함) «바로 뒤»에
    ② python3 tools/make-growth.py && python3 build.py
    ③ 사이트 저장소 푸시 — 🔴 푸시는 게시다(유진님 확인 사항). 지금은 켜지 않았다.
"""
import datetime, importlib.util, json, os, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.expanduser('~/projects/yesterdigest')
TSV = os.path.join(WORK, 'docs/records/계정-추이.tsv')
OUT = os.path.join(HERE, 'data/growth.json')
LOG = os.path.join(WORK, 'docs/records/publish-log.jsonl')
AN = 'https://youtubeanalytics.googleapis.com/v2/reports'
KST = datetime.timezone(datetime.timedelta(hours=9))

# 분석 그래프 — 유진님 우선순위(팀장 지시 ①~④). 키는 API 지표 이름.
분석그래프 = [
    dict(키='views', 이름='일별 조회수', 단위='회', 소수=0),
    dict(키='estimatedMinutesWatched', 이름='일별 시청 시간', 단위='분', 소수=0),
    dict(키='averageViewDuration', 이름='평균 시청 지속 시간', 단위='초', 소수=0, 조회없으면=True),
    dict(키='averageViewPercentage', 이름='평균 시청 비율', 단위='%', 소수=1, 조회없으면=True),
]
유입이름 = {  # insightTrafficSourceType → 읽는 한글
    'SHORTS': 'Shorts 피드', 'YT_SEARCH': '유튜브 검색', 'YT_CHANNEL': '채널 페이지',
    'YT_OTHER_PAGE': '유튜브 다른 화면', 'SUBSCRIBER': '구독 피드', 'EXT_URL': '외부 링크',
    'NO_LINK_OTHER': '직접·알 수 없음', 'NOTIFICATION': '알림', 'SOUND_PAGE': '사운드 페이지',
    'PLAYLIST': '재생목록', 'RELATED_VIDEO': '추천 영상', 'HASHTAGS': '해시태그', 'YT_PLAYLIST_PAGE': '재생목록 페이지',
    'END_SCREEN': '최종 화면', 'ANNOTATION': '카드', 'CAMPAIGN_CARD': '캠페인 카드', 'ADVERTISING': '광고',
}
연령이름 = {'age13-17': '13–17', 'age18-24': '18–24', 'age25-34': '25–34', 'age35-44': '35–44',
          'age45-54': '45–54', 'age55-64': '55–64', 'age65-': '65+'}


def 첫게시():
    """publish-log 에서 «시험용이 아니고 · 올림 · 지우지 않은» 첫 줄 — 플랫폼별. 근거 id 도 함께."""
    첫 = {}
    for line in open(LOG, encoding='utf-8'):
        d = json.loads(line)
        if d.get('시험용') or d.get('종류') == 'dummy' or (d.get('결과') or {}).get('상태') != '올림' or d.get('삭제'):
            continue
        첫.setdefault(d['플랫폼'], dict(시각=d['시각'], 종류=d.get('종류'), id=d['id'],
                                     원격ID=d['결과'].get('원격ID')))
    return 첫


def 분석_가져오기():
    """YouTube Analytics — 채널 전체 · 하루 단위. 토큰은 이 함수 밖으로 안 나간다."""
    sys.path.insert(0, os.path.join(WORK, 'scripts'))
    spec = importlib.util.spec_from_file_location('pub', os.path.join(WORK, 'scripts/publish.py'))
    pub = importlib.util.module_from_spec(spec); spec.loader.exec_module(pub)
    pub._load_env()
    from publishers import common, youtube as yt
    from publishers.common import Step
    E = os.environ
    tok = yt.access_token(client_id=E['YD_YT_CLIENT_ID'], client_secret=E['YD_YT_CLIENT_SECRET'],
                          refresh_token=E['YD_YT_REFRESH_TOKEN'])

    def get(url, params, 이름):
        return json.loads(common.send(Step(이름, 'GET', common.form(url, params)), tok)[2])

    ch = get('https://www.googleapis.com/youtube/v3/channels', {'part': 'snippet', 'mine': 'true'}, '채널')
    개설 = ch['items'][0]['snippet']['publishedAt']
    가져온때 = datetime.datetime.now(KST)
    첫 = 첫게시()
    시작 = 첫['youtube']['시각'][:10]          # 첫 영상을 올린 날부터(그 앞은 시험 영상뿐)
    끝 = 가져온때.date().isoformat()
    base = {'ids': 'channel==MINE', 'startDate': 시작, 'endDate': 끝}

    def rep(**kw):
        d = get(AN, dict(base, **kw), '분석')
        h = [c['name'] for c in d.get('columnHeaders', [])]
        return [dict(zip(h, r)) for r in d.get('rows') or []]

    일 = rep(metrics=','.join([g['키'] for g in 분석그래프] + ['subscribersGained', 'subscribersLost']),
            dimensions='day', sort='day')
    if not 일:
        raise RuntimeError('분석 응답에 줄이 없다')
    날짜 = [r['day'] for r in 일]
    # 기간 전체 값 — 평균은 «평균의 평균»이 아니라 API 가 기간으로 낸 값을 쓴다
    전체 = rep(metrics=','.join([g['키'] for g in 분석그래프] + ['subscribersGained', 'subscribersLost']),
             endDate=날짜[-1])[0]
    그래프 = []
    for g in 분석그래프:
        vals = []
        for r in 일:
            v = r[g['키']]
            if g.get('조회없으면') and not r['views']:
                v = None                                # 조회 0 인 날의 «평균»은 0 이 아니라 «없음»
            elif v is not None:
                v = round(v, g['소수']) if g['소수'] else int(round(v))
            vals.append(v)
        t = 전체[g['키']]
        그래프.append(dict(이름=g['이름'], 단위=g['단위'], 키=g['키'], 값=vals,
                         기간값=round(t, g['소수']) if g['소수'] else int(round(t)),
                         기간말='합계' if g['키'] in ('views', 'estimatedMinutesWatched') else '기간 전체'))
    구독 = dict(이름='구독자 증감', 단위='명', 키='subscribers', 모양='증감',
               얻음=[int(r['subscribersGained']) for r in 일], 잃음=[int(r['subscribersLost']) for r in 일],
               기간얻음=int(전체['subscribersGained']), 기간잃음=int(전체['subscribersLost']))

    유입 = {}
    for r in rep(metrics='views', dimensions='insightTrafficSourceType', sort='-views'):
        유입[r['insightTrafficSourceType']] = int(r['views'])
    합 = sum(유입.values()) or 1
    유입표 = [dict(코드=k, 이름=유입이름.get(k, k), 조회=v, 비율=round(100 * v / 합, 1))
            for k, v in sorted(유입.items(), key=lambda x: -x[1]) if v > 0]

    인구 = rep(metrics='viewerPercentage', dimensions='ageGroup,gender')
    연령 = []
    for k, 이름 in 연령이름.items():
        f = sum(r['viewerPercentage'] for r in 인구 if r['ageGroup'] == k and r['gender'] == 'female')
        m = sum(r['viewerPercentage'] for r in 인구 if r['ageGroup'] == k and r['gender'] == 'male')
        if f or m:
            연령.append(dict(연령=이름, 여성=round(f, 1), 남성=round(m, 1)))
    성별 = {}
    for r in 인구:
        성별[r['gender']] = round(성별.get(r['gender'], 0) + r['viewerPercentage'], 1)

    return {
        '있음': True,
        '가져온때': 가져온때.strftime('%Y-%m-%d %H:%M KST'),
        '마지막집계일': 날짜[-1], '첫날': 날짜[0], '날짜': 날짜,
        '그래프': 그래프, '구독증감': 구독,
        '유입': 유입표, '유입_기간': [날짜[0], 날짜[-1]],
        '연령성별': 연령, '성별': 성별,
        '미제공': ['노출수·노출 클릭률 (videoThumbnailImpressions — API 가 400 «query is not supported»)',
                 'Shorts 본 비율(viewed vs swiped away) — API 에 지표 없음'],
        '채널': {'개설': datetime.datetime.fromisoformat(개설.replace('Z', '+00:00')).astimezone(KST).strftime('%Y-%m-%d %H:%M KST'),
               '첫게시': 첫},
    }

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
        # 공개 통계의 «잰 때» — 기록 파일이 마지막으로 쓰인 시각(07:32·17:31 예약이 한 줄씩 쓴다)
        '기록시각': datetime.datetime.fromtimestamp(os.path.getmtime(src), KST).strftime('%Y-%m-%d %H:%M KST'),
        '첫날': 날짜[0], '마지막날': 날짜[-1], '빠진날': 빠진날,
        '날짜': 날짜,
        '그래프': [],
    }
    try:
        out['분석'] = 분석_가져오기()
    except Exception as ex:                                  # 🔴 예외 문구엔 토큰이 없다(common.send 가 가린다)
        옛 = {}
        try:
            옛 = json.load(open(OUT, encoding='utf-8')).get('분석') or {}
        except Exception:
            pass
        print('  ⚠️ 분석 API 실패 — %s: %s' % (type(ex).__name__, str(ex)[:200]))
        out['분석'] = 옛 if 옛.get('있음') else {'있음': False, '이유': type(ex).__name__}
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
    a = out['분석']
    if a.get('있음'):
        print('분석 — %s 가져옴 · %s ~ %s(마지막 집계일) · 채널 개설 %s' % (a['가져온때'], a['첫날'], a['마지막집계일'], a['채널']['개설']))


if __name__ == '__main__':
    main()
