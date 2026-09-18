import streamlit as st
import pandas as pd
import plotly.express as px

# 페이지 기본 설정
st.set_page_config(
    page_title="영화 데이터 그래프 도감 2 - 분포와 관계",
    page_icon="🎬",
    layout="wide"
)

# 데이터 로드 및 전처리
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_movies.csv"
    df = pd.read_csv(url)
    
    # 장르 열 전처리: 세로막대 기호(|)로 분리되어 있을 경우 첫 번째 장르만 추출
    if 'genre' in df.columns:
        df['genre'] = df['genre'].astype(str).apply(lambda x: x.split('|')[0] if x else x)
        
    return df

df = load_data()

# 타이틀 및 설명
st.title("🎬 영화 데이터 그래프 도감 2 - 분포와 관계")
st.markdown("KOBIS 영화 데이터를 활용하여 영화 수, 관객 수, 스크린 수 등의 분포와 관계를 시각화합니다.")
st.divider()

# --- Section 1: 장르별 영화 편수 (도넛 그래프) ---
st.header("1. 장르별 영화 편수 비율")

# 장르별 편수 집계
genre_counts = df['genre'].value_counts().reset_index()
genre_counts.columns = ['장르', '영화 편수']

# Plotly 도넛 차트 생성
fig1 = px.pie(
    genre_counts,
    names='장르',
    values='영화 편수',
    hole=0.4,
    title="장르별 영화 편수 분포"
)

# 호버 툴팁 설정: 편수와 비율이 명확하게 나타나도록 지정
fig1.update_traces(
    hovertemplate="<b>장르: %{label}</b><br>영화 편수: %{value}편<br>비율: %{percent}<extra></extra>",
    textinfo='label+percent'
)

st.plotly_chart(fig1, use_container_width=True)

# 그래프 해석/인사이트 영역
st.subheader("💡 이 그래프로 알 수 있는 것")
st.info("박스오피스 상위권 영화 중 특정 장르(예: 드라마다 액션 등)가 차지하는 비중을 직관적으로 파악할 수 있으며, 선호 장르의 쏠림 현상을 확인해 볼 수 있습니다.")

st.divider()

# 데이터 미리보기 (선택 사항)
with st.expander("📄 데이터 원본 보기"):
    st.dataframe(df)
