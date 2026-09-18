import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 기본 설정 및 스타일 정의
st.set_page_config(
    page_title="영화 데이터 그래프 도감 2 - 분포와 관계",
    page_icon="🎬",
    layout="wide"
)

# 2. 데이터 로드 및 전처리 (캐싱 처리)
DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_movies.csv"

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL)
    
    # genre 열 전처리: 세로막대 기호(|)로 여러 개 적힌 영화는 첫 번째 장르만 사용
    df['genre'] = df['genre'].astype(str).apply(
        lambda x: x.split('|')[0].strip() if pd.notna(x) and x != 'nan' else '기타'
    )
    
    # 개봉일(openDt) 날짜 데이터 타입 변환 (8자리 숫자 -> datetime 포맷 %Y%m%d)
    df['openDt'] = pd.to_datetime(df['openDt'].astype(str), format='%Y%m%d', errors='coerce')
    
    return df

# 데이터 로딩
try:
    df = load_data()
except Exception as e:
    st.error(f"데이터를 불러오는 데 실패했습니다: {e}")
    st.stop()

# 3. 앱 타이틀 및 소개
st.title("🎬 영화 데이터 그래프 도감 2 - 분포와 관계")
st.write("1년간 박스오피스 10위권에 든 개봉 영화 216편의 흥행 및 분포 데이터를 시각화합니다.")

st.markdown("---")

# 4. 첫 번째 그래프: 장르별 영화 편수 (도넛 그래프)
st.subheader("📌 장르별 영화 편수 비율")

# 장르별 영화 수 집계
genre_counts = df['genre'].value_counts().reset_index()
genre_counts.columns = ['genre', 'count']

# Plotly 도넛 그래프 생성
fig_donut = px.pie(
    genre_counts, 
    values='count', 
    names='genre',
    title='장르별 개봉 영화 편수 분포',
    hole=0.4,
    color_discrete_sequence=px.colors.qualitative.Pastel
)

# 마우스오버 툴팁 포맷 설정
fig_donut.update_traces(
    textposition='inside',
    textinfo='percent+label',
    hovertemplate="<b>장르:</b> %{label}<br><b>영화 편수:</b> %{value}편<br><b>비율:</b> %{percent}<extra></extra>"
)

fig_donut.update_layout(
    title_font_size=18,
    legend_title_text="장르",
    margin=dict(t=50, b=20, l=20, r=20)
)

st.plotly_chart(fig_donut, use_container_width=True)

# 인사이트 구역 1
st.divider()
st.info("💡 **이 그래프로 알 수 있는 것**\n\n- 박스오피스 10위권 내 영화 중 가장 비중이 높은 주력 장르가 무엇인지 한눈에 파악할 수 있으며, 특정 장르로의 쏠림 현상이나 다양한 장르의 분포 상태를 명확하게 관찰할 수 있습니다.")

st.markdown("---")

# 5. 두 번째 그래프: 장르-영화 트리맵 (총 관객수 기준)
st.subheader("📌 장르 및 영화별 총 관객수 분포 (트리맵)")

# 트리맵 생성: 장르 > 영화명 계층 구조, 타일 크기는 total_audi
fig_treemap = px.treemap(
    df,
    path=[px.Constant("전체 영화"), 'genre', 'movieNm'],
    values='total_audi',
    color='genre',
    title='장르별 및 영화별 총 관객수(total_audi) 분포',
    color_discrete_sequence=px.colors.qualitative.Set3
)

# 호버 툴팁 설정: 영화명 및 총 관객수(천단위 콤마 포맷) 표시
fig_treemap.update_traces(
    hovertemplate="<b>영화명:</b> %{label}<br><b>총 관객수:</b> %{value:,.0f}명<extra></extra>"
)

fig_treemap.update_layout(
    title_font_size=18,
    margin=dict(t=50, b=20, l=20, r=20)
)

st.plotly_chart(fig_treemap, use_container_width=True)

# 인사이트 구역 2
st.divider()
st.info("💡 **이 그래프로 알 수 있는 것**\n\n- 편수가 많은 장르라 하더라도 특정 대작 영화 한 두 편이 해당 장르 전체 관객수의 대부분을 차지하는지, 혹은 장르 내 여러 영화가 고르게 관객을 모았는지 흥행 집중도를 파악할 수 있습니다.")
