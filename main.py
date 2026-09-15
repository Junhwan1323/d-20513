import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
# 전체 영화 목록 (누적관객수 내림차순)
movie_order = (
    df.groupby("영화명")["누적관객수"]
    .max()
    .sort_values(ascending=False)
    .index.tolist()
)

# 사이드바에서 개별 분석할 영화 선택
selected_movie = st.sidebar.selectbox("영화를 선택하세요", movie_order)

# 선택한 영화의 데이터만 필터링
filtered_df = df[df["영화명"] == selected_movie]


# ---------------------------------------------------------
# [구역 1] 선택한 영화 - 일별 관객수 변화 (선 그래프)
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
# [구역 2] 선택한 영화 - 누적 관객수 변화 (영역 차트)
# ---------------------------------------------------------
st.header(f"📌 '{selected_movie}' 누적 관객수 성장 추이")

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

st.divider()

# ---------------------------------------------------------
# [구역 3] TOP 10 20일 이상 차트인 영화 중 TOP 5 비교 (다중 선 그래프)
# ---------------------------------------------------------
st.header("🏆 롱런 흥행 TOP 5 영화 누적 관객수 비교")

# 1. 영화별 등장 일수(행 수) 및 최대 누적관객수 계산
movie_stats = df.groupby("영화명").agg(
    등장일수=("기준일자", "count"),
    최대누적관객수=("누적관객수", "max")
)

# 2. 20일 이상 등장 조건을 만족하는 영화 중 누적관객수 TOP 5 추출
long_run_top5 = (
    movie_stats[movie_stats["등장일수"] >= 20]
    .sort_values(by="최대누적관객수", ascending=False)
    .head(5)
    .index.tolist()
)

# 3. 조건에 맞는 상위 5개 영화 데이터 추출
top5_long_run_df = df[df["영화명"].isin(long_run_top5)]

# 4. Plotly 다중 선 그래프 생성
fig_multi_line = px.line(
    top5_long_run_df,
    x="기준일자",
    y="누적관객수",
    color="영화명",
    title="TOP 10 20일 이상 진입 영화 중 흥행 TOP 5 - 누적 관객수 비교",
    labels={"기준일자": "날짜", "누적관객수": "누적 관객수(명)", "영화명": "영화 제목"},
)

# 그래프 화면 출력
st.plotly_chart(fig_multi_line, use_container_width=True)

# 그래프 설명 문구
st.info("💡 **이 그래프로 알 수 있는 것:** 일시적 반짝 흥행이 아닌 최소 20일 이상 TOP 10에 머무르며 장기 흥행에 성공한 주요 영화 5편의 관객 누적 속도와 시기별 완만함을 한눈에 비교할 수 있습니다.")

st.divider()

# ---------------------------------------------------------
# [구역 4] 전체 박스오피스 일별 총 관객수 및 7일 이동평균 (이동평균선)
# ---------------------------------------------------------
st.header("📈 전체 박스오피스 관객수 추이 및 7일 이동평균")

# 1. 기준일자별 TOP10 영화 전체의 해당일관객수 합계 계산
daily_total = df.groupby("기준일자")["해당일관객수"].sum().reset_index()

# 2. 7일 이동평균(Rolling Mean) 컬럼 생성
daily_total["7일_이동평균"] = daily_total["해당일관객수"].rolling(window=7).mean()

# 3. plotly.graph_objects를 이용해 원본 선과 이동평균 선 함께 그리기
fig_ma = go.Figure()

# 원본 데이터 선 (연한 색상)
fig_ma.add_trace(
    go.Scatter(
        x=daily_total["기준일자"],
        y=daily_total["해당일관객수"],
        mode="lines",
        name="일별 총 관객수",
        line=dict(color="rgba(150, 150, 150, 0.4)", width=1.5),
    )
)

# 7일 이동평균 선 (진한 색상)
fig_ma.add_trace(
    go.Scatter(
        x=daily_total["기준일자"],
        y=daily_total["7일_이동평균"],
        mode="lines",
        name="7일 이동평균",
        line=dict(color="#FF4B4B", width=3),
    )
)

fig_ma.update_layout(
    title="기준일자별 박스오피스 총 관객수 및 7일 이동평균선",
    xaxis_title="날짜",
    yaxis_title="총 관객수(명)",
    legend_title="구분",
    hovermode="x unified",
)

# 그래프 화면 출력
st.plotly_chart(fig_ma, use_container_width=True)

# 그래프 설명 문구
st.info("💡 **이 그래프로 알 수 있는 것:** 주말과 평일 간 관객수 편차(노이즈)를 줄인 7일 이동평균선을 통해 극장가 전체의 전반적인 흥행 상승·하락 흐름과 성수기/비성수기 주기를 명확히 파악할 수 있습니다.")

st.divider()

# ---------------------------------------------------------
# [구역 5] 월별 전체 박스오피스 총 관객수 합계 (막대 그래프)
# ---------------------------------------------------------
st.header("📊 월별 전체 박스오피스 총 관객수")

# 1. 기준일자에서 '연-월(YYYY-MM)' 문자열 추출
daily_total["연월"] = daily_total["기준일자"].dt.strftime("%Y-%m")

# 2. 월 단위로 관객수 합계 재집계
monthly_total = daily_total.groupby("연월")["해당일관객수"].sum().reset_index()

# 3. Plotly 막대 그래프 생성
fig_bar = px.bar(
    monthly_total,
    x="연월",
    y="해당일관객수",
    title="월별 총 박스오피스 관객수 합계",
    text_auto=".2s",  # 막대 상단에 요약 수치 표시
    labels={"연월": "년-월", "해당일관객수": "월 총 관객수(명)"},
)

# 그래프 스타일 추가 설정
fig_bar.update_traces(marker_color="#29B5D8")
fig_bar.update_layout(xaxis_type="category")  # 월별 축을 범주형으로 지정하여 정렬 유지

# 그래프 화면 출력
st.plotly_chart(fig_bar, use_container_width=True)

# 그래프 설명 문구
st.info("💡 **이 그래프로 알 수 있는 것:** 연중 어떤 월에 극장 방문 관객수가 가장 많았는지(성수기)와 상대적으로 관객수가 적었던 월(비성수기)의 월별 총 관객 규모를 한눈에 비교할 수 있습니다.")

st.divider()

# ---------------------------------------------------------
# [구역 6] 주차/월별 × 요일별 관객수 분포 (캘린더 히트맵)
# ---------------------------------------------------------
st.header("🗓️ 주차 및 요일별 관객수 히트맵")

# 1. 히트맵 전용 파생 변수 생성
heatmap_df = daily_total.copy()

# 요일명 추출 및 월요일~일요일 순서 정렬 지정
day_names_kr = ["월", "화", "수", "목", "금", "토", "일"]
heatmap_df["요일"] = heatmap_df["기준일자"].dt.weekday.map(
    lambda x: day_names_kr[x]
)

# 주차(ISO Week / 연-주차) 및 날짜 문자열 변환
heatmap_df["연주차"] = heatmap_df["기준일자"].dt.strftime("%Y-%W주차")
heatmap_df["날짜문자열"] = heatmap_df["기준일자"].dt.strftime("%Y-%m-%d")

# 2. Plotly 히트맵 생성 (px.density_heatmap)
fig_heatmap = px.density_heatmap(
    heatmap_df,
    x="연주차",
    y="요일",
    z="해당일관객수",
    category_orders={"요일": day_names_kr},  # 요일을 월요일부터 일요일 순으로 정렬
    color_continuous_scale="Reds",  # 관객수가 많을수록 진한 빨간색
    title="주차별 × 요일별 전체 박스오피스 관객수 분포",
    labels={
        "연주차": "연도별 주차",
        "요일": "요일",
        "해당일관객수": "총 관객수(명)",
    },
    hover_data={"날짜문자열": True, "연주차": False},  # 마우스 오버 시 yyyy-mm-dd 표시
)

# 호버 툴팁(마우스 올렸을 때) 레이아웃 다듬기
fig_heatmap.update_traces(
    hovertemplate="<b>날짜: %{customdata[0]}</b><br>요일: %{y}<br>관객수: %{z:,.0f}명<extra></extra>"
)

fig_heatmap.update_layout(
    xaxis_title="연도-주차",
    yaxis_title="요일",
    coloraxis_colorbar=dict(title="관객수(명)"),
)

# 그래프 화면 출력
st.plotly_chart(fig_heatmap, use_container_width=True)

# 그래프 설명 문구
st.info("💡 **이 그래프로 알 수 있는 것:** 주말(토·일)과 평일 간의 명확한 관객수 격차뿐만 아니라 연휴나 명절 등 특수 시기에 관객수가 크게 증가한 특정 날짜(yyyy-mm-dd)를 한눈에 식별할 수 있습니다.")
