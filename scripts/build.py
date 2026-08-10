#!/usr/bin/env python3
"""콘텐츠·리스티클 사이트 빌드.

본문은 **자체 작성**이다. 네이버 API는 주제 발굴에만 쓴다(fetch_topics.py).
가격 데이터는 기존 실험 사이트의 sku-data.json을 재사용한다.

산출: content-site/docs/  (GitHub Pages 루트로 그대로 배포)
"""
import json, os, re, html, random, argparse, datetime as dt
from urllib.parse import quote, urlsplit, urlunsplit

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, 'docs')
CFG = json.load(open(os.path.join(ROOT, 'config.json')))
BASE = CFG['base_url'].rstrip('/')
GC = CFG.get('goatcounter_code', '')

CSS = """body{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo','Malgun Gothic',sans-serif;
max-width:760px;margin:0 auto;padding:24px 16px;line-height:1.7;color:#1a1a1a}
h1{font-size:1.6rem;line-height:1.35}h2{font-size:1.2rem;margin-top:2em}
table{border-collapse:collapse;width:100%;margin:1.2em 0}
th,td{border:1px solid #ddd;padding:9px 10px;text-align:left;font-size:.95rem}
th{background:#f6f6f6}
.meta{color:#666;font-size:.85rem;margin:.5em 0 1.5em}
.item{border:1px solid #e5e5e5;border-radius:8px;padding:14px 16px;margin:14px 0}
.rank{display:inline-block;background:#111;color:#fff;border-radius:4px;padding:1px 8px;font-size:.85rem;margin-right:6px}
.price{font-weight:700}
nav a{margin-right:12px}footer{margin-top:3em;color:#777;font-size:.85rem;border-top:1px solid #eee;padding-top:1em}
"""

TRACK = """<script>
(function(){
  // utm 유입 계측 — LLM 경유 유입을 분리해 기록
  try{
    var p=new URLSearchParams(location.search);
    var src=p.get('utm_source')||document.referrer||'direct';
    var key='inbound_'+location.pathname;
    window.goatcounter=window.goatcounter||{};
    window.goatcounter.path=function(pp){return pp+'?src='+encodeURIComponent(src.slice(0,60));};
  }catch(e){}
})();
</script>"""


def head(title, desc, canon, extra=''):
    gc = (f'<script data-goatcounter="https://{GC}.goatcounter.com/count" '
          f'async src="//gc.zgo.at/count.js"></script>') if GC else ''
    return f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{canon}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{canon}">
<meta property="og:type" content="article">
{extra}
<style>{CSS}</style>{TRACK}{gc}
</head><body>
<nav><a href="{BASE}/">홈</a><a href="{BASE}/list/">리스티클</a><a href="{BASE}/post/">글</a></nav>
"""


FOOT = f"""<footer>수집·작성 시각은 각 문서에 표기. 가격은 변동되므로 판매처에서 최종 확인 필요.<br>
<a href="{BASE}/about.html">사이트 소개</a></footer></body></html>"""


def slug(s):
    return re.sub(r'[^a-z0-9가-힣]+', '-', s.lower()).strip('-')[:60]


def jsonld_list(title, items, url):
    el = [{"@type": "ListItem", "position": i + 1, "name": it['name']}
          for i, it in enumerate(items)]
    return ('<script type="application/ld+json">' + json.dumps(
        {"@context": "https://schema.org", "@type": "ItemList",
         "name": title, "url": url, "numberOfItems": len(items),
         "itemListElement": el}, ensure_ascii=False) + '</script>')


def build_listicle(title, items, stamp, fname):
    url = f'{BASE}/list/{fname}'
    desc = f'{title} — {len(items)}개 항목, {stamp} 기준 정리.'
    h = head(title, desc, url, jsonld_list(title, items, url))
    b = [f'<h1>{html.escape(title)}</h1>',
         f'<p class="meta">작성 {stamp} · 항목 {len(items)}개 · 가격은 수집 시점 기준</p>']
    for i, it in enumerate(items, 1):
        price = f"{it['lowest_price']:,}원" if it.get('lowest_price') else '가격 정보 없음'
        sellers = f" · 판매처 {it['seller_count']}곳" if it.get('seller_count') else ''
        b.append(f'''<div class="item"><span class="rank">{i}</span>
<strong>{html.escape(it["name"])}</strong><br>
<span class="price">{price}</span>{sellers}<br>
<span class="meta">{html.escape(it.get("note",""))}</span></div>''')
    b.append('<h2>정리</h2><p>위 목록은 수집 시점의 최저가 기준이며, 카드 할인·쿠폰·배송비에 따라 실제 결제가는 달라진다. '
             '구매 전 판매처에서 최종가와 정품 여부를 확인하는 편이 안전하다.</p>')
    open(os.path.join(SITE, 'list', fname), 'w').write(h + '\n'.join(b) + FOOT)
    return url


def build_post(title, paras, stamp, fname):
    url = f'{BASE}/post/{fname}'
    desc = paras[0][:120]
    h = head(title, desc, url)
    b = [f'<h1>{html.escape(title)}</h1>', f'<p class="meta">작성 {stamp}</p>']
    b += [f'<p>{html.escape(p)}</p>' for p in paras]
    open(os.path.join(SITE, 'post', fname), 'w').write(h + '\n'.join(b) + FOOT)
    return url


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sku', default='data/sku-data.json')
    ap.add_argument('--topics', default='data/topics.json')
    ap.add_argument('--n-list', type=int, default=3)
    ap.add_argument('--n-post', type=int, default=3)
    ap.add_argument('--seed', type=int, default=None)
    a = ap.parse_args()

    stamp = dt.date.today().isoformat()
    rnd = random.Random(a.seed if a.seed is not None else int(stamp.replace('-', '')))

    for d in ('list', 'post'):
        os.makedirs(os.path.join(SITE, d), exist_ok=True)

    skus = json.load(open(a.sku)) if os.path.exists(a.sku) else []
    skus = [s for s in skus if s.get('lowest_price')]
    topics = []
    if os.path.exists(a.topics):
        topics = [t['kw'] for t in json.load(open(a.topics))['topics']]

    urls = []

    # 리스티클 — 자체 가격 데이터 기반
    ANGLES = [('가성비', lambda x: x['lowest_price']),
              ('판매처가 많은 순', lambda x: -x.get('seller_count', 0)),
              ('프리미엄', lambda x: -x['lowest_price']),
              ('10만원 아래', lambda x: (x['lowest_price'] > 100000, x['lowest_price'])),
              ('20만원대', lambda x: abs(x['lowest_price'] - 250000)),
              ('비교가 쉬운 순', lambda x: -(x.get('seller_count', 0) * (x['lowest_price'] < 200000)))]
    rnd.shuffle(ANGLES)
    for i in range(min(a.n_list, len(ANGLES))):
        angle, key = ANGLES[i]
        pick = sorted(skus, key=key)[:10]
        for p in pick:
            p['note'] = f"{p.get('seller_count',0)}개 판매처 비교 기준"
        t = f'{angle} 무선 이어폰 10선 ({stamp[:7].replace("-","년 ")}월 기준)'
        urls.append(build_listicle(t, pick, stamp, f'{slug(angle)}-earbuds-{stamp}.html'))

    # 아티클 — 자체 작성 본문. 형태 5종을 랜덤 선택, 주제는 네이버 키워드
    # 조각·일반명사 토큰 제거 — 주제로 쓸 수 없는 것들
    BAD = {'추천','후기','정리','비교','장단점','순위','가격','최저가','있다면','프로','신제품',
           '리뷰','사용기','총정리','모음','내돈내산','솔직','실사용','추천템','best','top',
           '이어폰','블루투스','무선','제품','종류','기능','사용','구매','선택','차이','방법'}
    def usable(t):
        if t.lower() in BAD or len(t) < 2: return False
        if any(t.endswith(x) for x in ('하는','다면','까지','부터','에서','보다','으로','이나')): return False
        return True
    def as_topic(t):
        # 제품군 단어가 없으면 붙여서 자연스러운 주제로 만든다
        return t if any(k in t for k in ('이어폰','버즈','헤드폰','이어버드')) else f'{t} 이어폰'
    pool = [as_topic(t) for t in dict.fromkeys(topics) if usable(t)]
    pool = pool or ['무선 이어폰', '노이즈캔슬링 이어폰', '가성비 이어폰']
    rnd.shuffle(pool)

    def shape_criteria(kw):
        return (f'{kw} 고를 때 실제로 보는 것', [
            f'{kw}를 찾을 때 먼저 부딪히는 건 가격이 아니라 기준이다. 스펙표는 길지만 구매 결과를 바꾸는 항목은 몇 개 안 된다.',
            '실사용 재생 시간이 첫 번째다. 표기 시간은 대개 노이즈캔슬링을 끈 조건이라 켜면 20~30% 줄어든다. 케이스 포함 총 시간과 본체 단독 시간을 나눠서 봐야 한다.',
            '착용감이 두 번째다. 같은 이어팁 크기라도 노즐 각도에 따라 체감이 다르다. 반품 조건을 미리 확인해두는 게 스펙 비교보다 실질적이다.',
            '가격 변동 폭이 세 번째다. 같은 모델이 판매처와 시점에 따라 수만 원씩 차이 난다. 카드 할인과 쿠폰까지 반영한 실결제가로 비교해야 한다.',
            f'{kw} 선택은 스펙 순위가 아니라 사용 조건에 맞추는 문제다. 하루 사용 시간, 착용 환경, 예산 상한 세 가지를 먼저 정하면 후보가 크게 줄어든다.'])

    def shape_mistakes(kw):
        return (f'{kw} 살 때 자주 하는 실수', [
            f'{kw}를 사고 나서 후회하는 이유는 대체로 비슷하다. 몇 가지는 사기 전에 걸러낼 수 있다.',
            '첫째, 표기 재생 시간을 그대로 믿는 것. 조건이 다르면 실사용은 짧아진다.',
            '둘째, 최저가만 보고 판매처를 확인하지 않는 것. 병행수입과 정품은 AS 조건이 다르다.',
            '셋째, 이어팁을 기본 상태로만 쓰는 것. 팁만 바꿔도 차음과 저음이 달라진다.',
            '넷째, 코덱 표기에 과하게 무게를 두는 것. 기기 조합이 맞지 않으면 무의미하다.',
            f'정리하면 {kw}는 스펙보다 구매 조건과 사용 환경에서 갈린다.'])

    def shape_price(kw):
        return (f'{kw} 가격대별로 무엇이 달라지나', [
            f'{kw}는 가격대마다 포기하는 항목이 다르다. 무엇을 버릴지 정하면 선택이 빨라진다.',
            '5만 원 아래에서는 연결 안정성과 통화 품질이 먼저 흔들린다. 음질보다 이쪽이 체감된다.',
            '5~15만 원 구간은 노이즈캔슬링이 들어오기 시작하는 지점이다. 다만 강도 차이가 크다.',
            '15만 원 위로는 착용감과 앱 기능, 멀티포인트 같은 편의 기능이 갈린다.',
            f'{kw}를 고를 때는 상한을 먼저 정하고 그 구간에서 무엇이 빠지는지 확인하는 순서가 낫다.'])

    def shape_faq(kw):
        return (f'{kw} 자주 묻는 것 정리', [
            f'{kw}에 대해 반복해서 나오는 질문을 정리했다.',
            '노이즈캔슬링을 켜면 배터리가 얼마나 줄어드나 — 제품마다 다르지만 대체로 20~30% 수준이다.',
            '병행수입과 정품 차이는 — 가격은 싸지만 국내 AS가 제한되는 경우가 많다. 보증 조건을 먼저 확인해야 한다.',
            '한쪽만 소리가 안 나면 — 대개 접점 오염이나 페어링 문제다. 초기화 후 재연결로 해결되는 경우가 많다.',
            '이어팁은 바꿀 필요가 있나 — 차음이 부족하면 저음이 빠진다. 팁 교체가 가장 저렴한 개선이다.',
            f'{kw} 관련 질문은 대부분 스펙이 아니라 사용 조건에서 나온다.'])

    def shape_terms(kw):
        return (f'{kw} 용어 정리', [
            f'{kw} 설명에 반복해서 나오는 용어를 짧게 정리했다.',
            'ANC는 액티브 노이즈 캔슬링이다. 마이크로 주변 소음을 측정해 반대 위상으로 상쇄한다. 저주파에 강하고 사람 목소리에는 약하다.',
            '멀티포인트는 두 기기에 동시 연결하는 기능이다. 노트북과 휴대폰을 오갈 때 체감이 크다.',
            '코덱은 무선으로 소리를 보내는 압축 방식이다. 송신 기기와 수신 기기가 같은 코덱을 지원해야 의미가 있다.',
            'IPX 등급은 방수 정도다. 숫자가 클수록 강하고, 운동용이면 IPX4 이상이 무난하다.',
            f'{kw}를 비교할 때 이 네 가지만 알아도 스펙표 대부분이 읽힌다.'])

    SHAPES = [shape_criteria, shape_mistakes, shape_price, shape_faq, shape_terms]
    n_post = a.n_post if a.n_post else rnd.randint(2, 5)
    for i in range(n_post):
        kw = pool[i % len(pool)]
        shape = SHAPES[rnd.randrange(len(SHAPES))]
        t, paras = shape(kw)
        rnd.shuffle(paras[1:-1])          # 본문 순서도 랜덤
        fn = f'{slug(kw)}-{stamp}-{i+1}.html'
        urls.append(build_post(t, paras, stamp, fn))

    # 인덱스
    def index(dirname, heading):
        files = sorted(os.listdir(os.path.join(SITE, dirname)), reverse=True)
        files = [f for f in files if f.endswith('.html') and f != 'index.html']
        u = f'{BASE}/{dirname}/'
        h = head(heading, heading, u)
        b = [f'<h1>{heading}</h1><ul>']
        for f in files:
            b.append(f'<li><a href="{BASE}/{dirname}/{f}">{html.escape(f[:-5])}</a></li>')
        b.append('</ul>')
        open(os.path.join(SITE, dirname, 'index.html'), 'w').write(h + '\n'.join(b) + FOOT)

    index('list', '리스티클')
    index('post', '글')

    # 홈
    h = head(CFG['site_name'], CFG['site_desc'], f'{BASE}/')
    open(os.path.join(SITE, 'index.html'), 'w').write(
        h + f'<h1>{html.escape(CFG["site_name"])}</h1><p>{html.escape(CFG["site_desc"])}</p>'
        f'<p><a href="{BASE}/list/">리스티클</a> · <a href="{BASE}/post/">글</a></p>' + FOOT)

    # about
    open(os.path.join(SITE, 'about.html'), 'w').write(
        head('사이트 소개', '사이트 소개', f'{BASE}/about.html')
        + '<h1>사이트 소개</h1><p>무선 이어폰 가격과 선택 기준을 정리하는 사이트다. '
          '가격 데이터는 공개 가격비교 정보를 수집해 정리하며, 본문은 직접 작성한다.</p>'
          '<p>수집 시점과 작성일을 각 문서에 표기한다. 가격은 변동되므로 판매처에서 최종 확인이 필요하다.</p>'
        + FOOT)

    # robots — AI 검색봇 명시 허용
    bots = ['OAI-SearchBot', 'ChatGPT-User', 'Claude-SearchBot', 'Claude-User',
            'PerplexityBot', 'Perplexity-User', 'Googlebot', 'Bingbot', 'Yeti', 'Daum']
    rb = '\n'.join(f'User-agent: {b}' for b in bots) + '\nAllow: /\n\nUser-agent: *\nAllow: /\n'
    rb += f'\nSitemap: {BASE}/sitemap.xml\n'
    open(os.path.join(SITE, 'robots.txt'), 'w').write(rb)

    # sitemap
    all_pages = [f'{BASE}/', f'{BASE}/about.html', f'{BASE}/list/', f'{BASE}/post/']
    for d in ('list', 'post'):
        for f in sorted(os.listdir(os.path.join(SITE, d))):
            if f.endswith('.html') and f != 'index.html':
                all_pages.append(f'{BASE}/{d}/{f}')
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    def _enc(u):
        """사이트맵 규격: URL은 퍼센트 인코딩해야 한다(한글 경로 그대로 두면 구글이 못 가져옴)"""
        p = urlsplit(u)
        return urlunsplit((p.scheme, p.netloc, quote(p.path, safe='/-._~'), p.query, p.fragment))
    sm += [f'  <url><loc>{_enc(u)}</loc><lastmod>{stamp}</lastmod></url>' for u in all_pages]
    sm.append('</urlset>')
    open(os.path.join(SITE, 'sitemap.xml'), 'w').write('\n'.join(sm))

    print(f'빌드 완료 {stamp}')
    print(f'  신규 {len(urls)}건 · 전체 {len(all_pages)}페이지')
    for u in urls:
        print(f'  {u}')


if __name__ == '__main__':
    main()
