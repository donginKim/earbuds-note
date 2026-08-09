#!/usr/bin/env python3
"""네이버 블로그 검색 API로 **주제·키워드만** 수집한다.

⚠️ 원문 본문은 저장하지 않는다. 제목·링크·게시일만 쓴다.
   본문 재게시는 저작권 위반이고, 스크랩 사이트로 분류되면 색인에서 빠져
   실험 자체가 성립하지 않는다.

필요: 네이버 개발자센터 애플리케이션 등록 후
      NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 환경변수 설정
"""
import json, os, sys, time, re, argparse, datetime as dt
from urllib.parse import quote
import urllib.request

API = 'https://openapi.naver.com/v1/search/blog.json'
CID = os.environ.get('NAVER_CLIENT_ID')
SEC = os.environ.get('NAVER_CLIENT_SECRET')

STOP = set('그리고 그러나 하지만 이런 저런 정말 진짜 오늘 어제 내일 요즘 최근 사람 생각 시간 정도 경우 때문 이후 이전 부분 관련 하나 다시 그냥'.split())


def search(query, display=100, start=1, sort='date'):
    if not (CID and SEC):
        sys.exit('NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 환경변수가 없다.')
    url = f'{API}?query={quote(query)}&display={display}&start={start}&sort={sort}'
    req = urllib.request.Request(url, headers={
        'X-Naver-Client-Id': CID, 'X-Naver-Client-Secret': SEC})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


def strip_tags(s):
    return re.sub(r'<[^>]+>', '', s or '').replace('&quot;', '"').replace('&amp;', '&').strip()


def harvest(seeds, per=100):
    """제목에서 키워드를 뽑아 주제 후보를 만든다. 본문·요약은 저장하지 않는다."""
    topics = {}
    for seed in seeds:
        try:
            d = search(seed, display=per)
        except Exception as e:
            print(f'  ! {seed}: {e}')
            continue
        for it in d.get('items', []):
            title = strip_tags(it.get('title'))
            # 제목에서 명사성 토큰만 추출 (2~12자, 스톱워드 제외)
            for tok in re.findall(r'[가-힣A-Za-z0-9]{2,12}', title):
                if tok in STOP or tok.isdigit():
                    continue
                topics.setdefault(tok, {'kw': tok, 'seed': seed, 'n': 0})
                topics[tok]['n'] += 1
        print(f'  {seed}: {len(d.get("items", []))}건')
        time.sleep(0.3)
    return sorted(topics.values(), key=lambda x: -x['n'])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', nargs='+',
                    default=['무선 이어폰 추천', '가성비 이어폰', '노이즈캔슬링 이어폰',
                             '이어폰 비교', '블루투스 이어폰 후기'])
    ap.add_argument('--out', default='content-site/data/topics.json')
    ap.add_argument('--top', type=int, default=200)
    a = ap.parse_args()

    print(f'시드 {len(a.seeds)}개 수집')
    topics = harvest(a.seeds)[:a.top]
    out = {'collected_at': dt.datetime.now().isoformat(timespec='seconds'),
           'seeds': a.seeds, 'n': len(topics), 'topics': topics,
           'note': '제목 기반 키워드만. 본문·요약 미저장.'}
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(out, open(a.out, 'w'), ensure_ascii=False, indent=1)
    print(f'\n키워드 {len(topics)}개 → {a.out}')
    for t in topics[:20]:
        print(f'  {t["kw"]:<16}{t["n"]}')


if __name__ == '__main__':
    main()
