# 이어폰 가격 노트

무선 이어폰 최저가와 선택 기준을 정리하는 사이트.

- 사이트: https://donginkim.github.io/earbuds-note/
- 가격 데이터는 공개 가격비교 정보를 수집해 정리하며, 본문은 직접 작성한다.
- 수집 시각과 작성일을 각 문서에 표기한다.

## 빌드

```bash
python3 scripts/build.py --sku data/sku-data.json
```

발행은 GitHub Actions가 매일 07:00 KST에 수행한다. 변경이 없으면 커밋하지 않는다.
