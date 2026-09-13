import pandas as pd
import plotly.express as px
import streamlit as st


# [1. 데이터 불러오기]
# @st.cache_data 데코레이터를 사용하여 데이터를 매번 불러오지 않고 캐시에 저장해 재사용합니다.
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/keep-growing-park/data-science/refs/heads/main/dataset/kobis_1year_boxoffice.csv"
    df = pd.read_csv(url)

    # [2. 날짜 및 데이터 전처리]
    # 결측치가 포함된 행을 삭제합니다.
    df = df.dropna()

    # '기준일자' 컬럼을 datetime 형식으로 변환합니다.
    df["기준일자"] = pd.to_datetime(df["기준일자"])

    # 데이터를 기준일자 오름차순으로 정렬합니다.
    df = df.sort_values(by="기준일자", ascending=True)

    return df


# 페이지 기본 설정
st.set_page_config(page_title="박스오피스 데이터 분석", layout="wide")
st.title("🎬 영화 박스오피스 데이터 시각화")

# 데이터 로드
df = load_data()

# [3. 영화 선택 기능]
# 영화별 최대 누적관객수를 기준으로 내림차순 정렬하여 중복 없이 목록 생성
movie_order = (
    df.groupby("영화명")["누적관객수"]
    .max()
    .sort_values(ascending=False)
    .index.tolist()
)

# 사이드바에서 영화 선택
selected_movie = st.sidebar.selectbox("영화를 선택하세요", movie_order)

# 선택한 영화의 데이터만 필터링
filtered_df = df[df["영화명"] == selected_movie]


# ---------------------------------------------------------
# [구역 1] 일별 관객수 변화 (선 그래프)
# ---------------------------------------------------------
st.header(f"📌 '{selected_movie}' 일별 관객수 추이")

fig_line = px.line(
    filtered_df,
    x="기준일자",
    y="해당일관객수",
    title=f"{selected_movie} - 일별 관객수 변화",
    markers=True,
    labels={"기준일자": "날짜", "해당일관객수": "일별 관객수(명)"},
)

# 그래프 화면 출력
st.plotly_chart(fig_line, use_container_width=True)

# 그래프 설명 문구
st.info("💡 **이 그래프로 알 수 있는 것:** 영화 개봉 초기 관객수 폭발 지점과 이후 상영 기간에 따른 일별 관객 감소 추이를 한눈에 확인할 수 있습니다.")

st.divider()

# ---------------------------------------------------------
# [구역 2] 누적관객수 변화 (영역 차트)
# ---------------------------------------------------------
st.header(f"📌 '{selected_movie}' 누적 관객수 성장 추이")

# Plotly를 활용한 기준일자별 누적관객수 영역 차트(Area Chart) 작성
fig_area = px.area(
    filtered_df,
    x="기준일자",
    y="누적관객수",
    title=f"{selected_movie} - 누적 관객수 증가 추이",
    labels={"기준일자": "날짜", "누적관객수": "누적 관객수(명)"},
)

# 그래프 화면 출력
st.plotly_chart(fig_area, use_container_width=True)

# 그래프 설명 문구
st.info("💡 **이 그래프로 알 수 있는 것:** 시간이 경과함에 따라 관객수가 꾸준히 누적되는 전체적인 흥행 성장 곡선과 주요 고지(예: 100만, 500만 명 등) 달성 시점을 파악할 수 있습니다.")
