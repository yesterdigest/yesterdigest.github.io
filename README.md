# YesterDigest — 공식 홈페이지

**어제한입(YesterDigest)** 의 공개 홈페이지. <https://yesterdigest.com>
GitHub Pages 가 이 저장소의 `main` 을 그대로 내보낸다 (`CNAME` = yesterdigest.com).

이 페이지는 **대문이지 목적지가 아니다.** 내용을 여기서 다 보여주지 않고
**Instagram·YouTube 로 보낸다.**

| 주소 | 무엇 |
|---|---|
| `/` | 첫 화면 + 지난 편 (한 파일 안에서 화면만 바뀐다 — `#해시`) |
| `/privacy/` | 개인정보처리방침 (Google OAuth 심사가 본다) |
| `/terms/` | 이용약관 |

## 고치는 법

🔴 **`index.html` 을 손으로 고치지 않는다.** 만들어지는 파일이다.

```bash
python3 build.py          # data/*.json + build.py  ->  index.html · sitemap.xml
```

| 고칠 것 | 어디 |
|---|---|
| 글·배치·화면 | `build.py` |
| 모양 | `assets/styles.css` (공통) · `assets/home.css` (첫 화면) |
| 움직임 | `assets/home.js` |
| 메뉴에 칸을 더하기 | `data/sections.json` 의 `"보임": true` |
| 첫 화면에서 넘어가는 장 | `data/showcase.json` |
| 지난 편 목록 | `data/editions.json` — **손으로 안 적는다** (아래) |

새 편이 올라간 뒤 (두 줄):

```bash
python3 ~/projects/yesterdigest/scripts/build-site-editions.py   # 게시 기록 -> editions.json
python3 build.py
```

## 아이콘과 공유 그림

`favicon.ico` · `apple-touch-icon.png` · `assets/og/home.png` 는 **전부 `assets/logo.png` 한 장에서 나온다.**
로고나 `tools/og-card.html` 을 고쳤으면:

```bash
python3 tools/make-assets.py
python3 build.py          # og 그림 주소 뒤의 ?v= 를 다시 붙인다
```

`assets/og/home.png` (1200×630) 가 **카톡·트위터·페북에 주소를 붙였을 때 뜨는 그림**이다.
크기를 줄이면 큰 카드가 안 뜬다.

## 🔴 한 번만 해둘 것

```bash
git config core.hooksPath tools/githooks
```

자산을 고치고 `build.py` 를 안 돌린 채 커밋하는 것을 막는다.
`index.html` 안의 `?v=` 가 낡으면 **브라우저가 옛 CSS 를 계속 써서, 고친 것이 폰에 안 간다.**
실제로 한 번 그랬다 (커밋 `8b238f6`).

## 🔴 여기에 절대 올리지 않는 것

공개 저장소다. 누구나 본다.

- API 키 · OAuth 토큰 · 비밀번호 · `.env`
- 내부 운영 문서 · 대본 · 음성 파일 · 아직 안 올린 제작물
- 권리를 확인하지 않은 남의 사진 · 글 · 글씨체
