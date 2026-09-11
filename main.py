import streamlit as st
st.title("나의 데이터 과학 포트폴리오")
st.write("반갑습니다! 이제부터 여기에 제 작업을 기록합니다.")
from datetime import datetime, timedelta
import pandas as pd
import pytz
import requests
import streamlit as st

# 페이지 제목 및 레이아웃 설정
st.set_page_config(page_title="어제 박스오피스 순위", layout="wide")


# -------------------------------------------------------------------
# 1. API 데이터 조회 함수 (캐싱 적용)
# -------------------------------------------------------------------
# st.cache_data를 사용하여 1시간(3600초) 동안 동일 요청에 대한 결과를 저장합니다.
@st.cache_data(ttl=3600)
def fetch_box_office_data(target_dt_str, api_key):
    """KOBIS API를 호출하여 dailyBoxOfficeList 데이터를 반환하는 함수"""
    url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    params = {"key": api_key, "targetDt": target_dt_str}

    try:
        response = requests.get(url, params=params, timeout=10)
        # HTTP 요청 성공 확인 (200 OK)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        # 네트워크 오류 등 요청 실패 시 None 반환
        return None


# -------------------------------------------------------------------
# 2. 날짜 계산 (한국 시간 KST 기준)
# -------------------------------------------------------------------
# 배포 서버의 기본 시계가 해외 기준일 수 있으므로 pytz로 한국 시간을 명시합니다.
kst = pytz.timezone("Asia/Seoul")
now_kst = datetime.now(kst)
yesterday_kst = now_kst - timedelta(days=1)
target_dt = yesterday_kst.strftime("%Y%m%d")  # API 요청용 (YYYYMMDD)
formatted_date = yesterday_kst.strftime("%Y년 %m월 %d일")  # 화면 표시용

st.title("🎬 어제 일별 박스오피스")
st.caption(f"기준일자: {formatted_date} (한국 시간 기준 어제)")


# -------------------------------------------------------------------
# 3. 비밀 금고(Secrets)에서 API 키 불러오기 및 예외 처리
# -------------------------------------------------------------------
if "KOBIS_KEY" not in st.secrets:
    st.error("🔑 API 인증키가 설정되지 않았습니다.")
    st.info(
        "Streamlit Cloud의 App Settings > Secrets 메뉴에서 아래와 같이 KOBIS_KEY를 추가했는지 확인해 주세요.\n\n"
        '```toml\nKOBIS_KEY = "발급받은_인증키"\n```'
    )
    st.stop()

api_key = st.secrets["KOBIS_KEY"]


# -------------------------------------------------------------------
# 4. 데이터 요청 및 검증
# -------------------------------------------------------------------
raw_data = fetch_box_office_data(target_dt, api_key)

# (1) 요청 실패 예외 처리
if raw_data is None:
    st.error("⚠️ 서버 통신에 실패했습니다.")
    st.warning(
        "확인 사항:\n"
        "- 인터넷 연결 상태를 확인해 주세요.\n"
        "- KOBIS API 서버가 점검 중인지 확인해 주세요."
    )
    st.stop()

# (2) API 인증 실패/오류 상자(faultInfo) 예외 처리
if "faultInfo" in raw_data:
    st.error("⚠️ API 호출 오류가 발생했습니다 (faultInfo).")
    st.warning(
        "확인 사항:\n"
        "- Secrets에 등록한 KOBIS_KEY 인증키가 올바른지 확인해 주세요.\n"
        f"- KOBIS 오류 메시지: {raw_data['faultInfo'].get('message', '알 수 없는 오류')}"
    )
    st.stop()

# (3) 영화 목록(dailyBoxOfficeList) 데이터 존재 여부 확인
box_office_result = raw_data.get("boxOfficeResult", {})
movie_list = box_office_result.get("dailyBoxOfficeList", [])

if not movie_list:
    st.warning("⚠️ 조회할 수 있는 영화 목록이 비어 있습니다.")
    st.info(
        "확인 사항:\n"
        "- 아직 KOBIS 서버에서 어제 날짜 집계가 완료되지 않았을 수 있습니다.\n"
        "- 나중에 다시 시도하거나 KOBIS 서비스 상태를 확인해 주세요."
    )
    st.stop()


# -------------------------------------------------------------------
# 5. 데이터 가공 (문자열 -> 숫자 변환 및 정제)
# -------------------------------------------------------------------
df = pd.DataFrame(movie_list)

# 숫자로 된 문자열 컬럼을 실제 정수형(int) 데이터로 변환
numeric_columns = ["rank", "audiCnt", "audiAcc", "scrnCnt"]
for col in numeric_columns:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

# 순위(rank) 기준 오름차순 정렬
df = df.sort_values(by="rank", ascending=True)


# -------------------------------------------------------------------
# 6. 대시보드 화면 구성
# -------------------------------------------------------------------

# [A] 1위 영화 하이라이트 지표 카드
top_1_movie = df.iloc[0]

st.subheader(f"🏆 1위 영화: {top_1_movie['movieNm']}")

metric_col1, metric_col2, metric_col3 = st.columns(3)

with metric_col1:
    st.metric(
        label="일일 관객수", value=f"{top_1_movie['audiCnt']:,} 명"
    )

with metric_col2:
    st.metric(
        label="누적 관객수", value=f"{top_1_movie['audiAcc']:,} 명"
    )

with metric_col3:
    st.metric(
        label="상영 스크린수", value=f"{top_1_movie['scrnCnt']:,} 개"
    )

st.divider()

# [B] 관객수 상위 5편 막대그래프
st.subheader("📊 관객수 상위 5개 영화")

# 상위 5개 데이터 추출
top5_df = df.head(5)

# Altair 그래프를 활용한 일일 관객수 시각화
st.bar_chart(data=top5_df, x="movieNm", y="audiCnt", color="#FF4B4B")

st.divider()

# [C] 전체 순위표 (표)
st.subheader("📋 전체 박스오피스 순위표")

# 표에 표시할 컬럼 정리 및 이름 변경
display_df = df[
    ["rank", "movieNm", "openDt", "audiCnt", "audiAcc", "scrnCnt"]
].copy()
display_df.columns = [
    "순위",
    "영화명",
    "개봉일",
    "관객수",
    "누적관객",
    "스크린수",
]

# 화면 출력 (천 단위 쉼표 서식 적용)
st.dataframe(
    display_df,
    hide_index=True,
    use_container_width=True,
    column_config={
        "순위": st.column_config.NumberColumn(format="%d위"),
        "관객수": st.column_config.NumberColumn(format="%'d 명"),
        "누적관객": st.column_config.NumberColumn(format="%'d 명"),
        "스크린수": st.column_config.NumberColumn(format="%'d 개"),
    },
)
