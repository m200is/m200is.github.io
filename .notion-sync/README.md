# Notion → GitHub Pages 동기화

개인 블로그용 Notion 콘텐츠 자동 변환 시스템

## 사용법

Claude에게 요청:
```
"Notion의 [페이지 제목] 글을 GitHub Pages로 옮겨줘"
```

## 파일 구조

```
.notion-sync/
  └── notion_to_github_pages.py  # 변환 스크립트
_posts/                            # Jekyll 포스트
```

## 변환 규칙

- Callout → Jekyll Prompt
- `{{URL}}` → `URL`
- `c++` → `cpp`
- 한글 파일명 → 영문 파일명
