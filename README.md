# ad-opt

Google Ads / Meta 등 셀프서브 광고 계정 자동 감사·ROAS 최적화 도구.

## Google Ads 연동

```bash
pip install -r requirements.txt
cp .env.example .env   # 실제 값 입력
```

필수 환경 변수:

| 변수 | 설명 |
|------|------|
| `GOOGLE_ADS_DEVELOPER_TOKEN` | API 개발자 토큰 |
| `GOOGLE_ADS_CLIENT_ID` | OAuth 클라이언트 ID |
| `GOOGLE_ADS_CLIENT_SECRET` | OAuth 클라이언트 시크릿 |
| `GOOGLE_ADS_REFRESH_TOKEN` | OAuth 리프레시 토큰 (1회 발급) |
| `GOOGLE_ADS_CUSTOMER_ID` | 광고 계정 ID |
| `GOOGLE_ADS_LOGIN_CUSTOMER_ID` | MCC ID (있을 경우) |

### Refresh Token 발급

```bash
export GOOGLE_ADS_CLIENT_ID=...
export GOOGLE_ADS_CLIENT_SECRET=...
python3 scripts/oauth_setup.py
# 출력된 URL 접속 → 인증 코드 복사
OAUTH_CODE=<코드> python3 scripts/oauth_setup.py
```

### 계정 감사 실행

```bash
python3 scripts/audit_account.py
```
