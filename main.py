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
st.subheader("📌 1. 장르별 영화 편수 비율")

genre_counts = df['genre'].value_counts().reset_index()
genre_counts.columns = ['genre', 'count']

fig_donut = px.pie(
    genre_counts, 
    values='count', 
    names='genre',
    title='장르별 개봉 영화 편수 분포',
    hole=0.4,
    color_discrete_sequence=px.colors.qualitative.Pastel
)

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

st.divider()
st.info("💡 **이 그래프로 알 수 있는 것**\n\n- 박스오피스 10위권 내 영화 중 가장 비중이 높은 주력 장르가 무엇인지 한눈에 파악할 수 있으며, 특정 장르로의 쏠림 현상이나 다양한 장르의 분포 상태를 명확하게 관찰할 수 있습니다.")

st.markdown("---")

# 5. 두 번째 그래프: 장르 및 영화별 총 관객수 (트리맵)
st.subheader("📌 2. 장르 및 영화별 총 관객수 (트리맵)")

fig_treemap = px.treemap(
    df,
    path=[px.Constant("전체 영화"), 'genre', 'movieNm'],
    values='total_audi',
    color='genre',
    color_discrete_sequence=px.colors.qualitative.Pastel,
    title='장르 및 영화별 총 관객수 기여도'
)

fig_treemap.update_traces(
    hovertemplate="<b>영화명:</b> %{label}<br><b>총 관객수:</b> %{value:,}명<extra></extra>"
)

fig_treemap.update_layout(
    title_font_size=18,
    margin=dict(t=50, b=20, l=20, r=20)
)

st.plotly_chart(fig_treemap, use_container_width=True)

st.divider()
st.info("💡 **이 그래프로 알 수 있는 것**\n\n- 장르 전체의 관객 규모뿐만 아니라, 특정 장르 안에서 어떤 영화가 전체 관객수의 흥행을 주도했는지(타일의 크기)를 직관적으로 비교할 수 있습니다.")

st.markdown("---")

# 6. 세 번째 그래프: 총 관객수 분포 (히스토그램)
st.subheader("📌 3. 영화별 총 관객수 분포 (히스토그램)")

fig_hist = px.histogram(
    df,
    x='total_audi',
    nbins=20,
    title='총 관객수 구간별 영화 편수 분포',
    labels={'total_audi': '총 관객수(명)', 'count': '영화 수'},
    color_discrete_sequence=['#4A90E2']
)

fig_hist.update_traces(
    hovertemplate="<b>관객수 구간:</b> %{x}명<br><b>영화 수:</b> %{y}편<extra></extra>"
)

fig_hist.update_layout(
    title_font_size=18,
    xaxis_title="총 관객수 (명)",
    yaxis_title="영화 수 (편)",
    bargap=0.1,
    margin=dict(t=50, b=20, l=20, r=20)
)

st.plotly_chart(fig_hist, use_container_width=True)

# 최다 관객 영화 찾기
top_movie = df.loc[df['total_audi'].idxmax()]
top_movie_name = top_movie['movieNm']
top_movie_audi = top_movie['total_audi']

# 구간 밀집도 계산
most_dense_count = df[df['total_audi'] <= 1000000].shape[0]
total_movies_count = len(df)
dense_percent = round((most_dense_count / total_movies_count) * 100, 1)

st.markdown(f"""
- 🏆 **가장 관객이 많은 영화:** **{top_movie_name}** ({top_movie_audi:,.0f}명)
- 📊 **영화 밀집 구간:** 전체 영화의 **{dense_percent}%**({most_dense_count}편)가 **총 관객수 100만 명 이하** 구간에 몰려 있으며, 극소수의 대형 흥행작(천만 관객 이상 등)이 전체 데이터를 오른쪽으로 길게 늘어뜨리는 불균형한 분포 형태를 보입니다.
""")

st.divider()
st.info("💡 **이 그래프로 알 수 있는 것**\n\n- 흥행에 성공하는 상위 대형 영화의 수에 비해 대부분의 개봉작들이 형성하는 현실적인 관객수 규모 구간이 어디인지를 명확하게 파악할 수 있습니다.")

st.markdown("---")

# 7. 네 번째 그래프: 개봉일 스크린수 vs 총 관객수 (산점도)
st.subheader("📌 4. 개봉일 스크린수와 총 관객수의 관계 (산점도)")

fig_scatter = px.scatter(
    df,
    x='first_scrn',
    y='total_audi',
    color='genre',
    hover_name='movieNm',
    title='개봉일 스크린수 대비 최종 총 관객수',
    labels={
        'first_scrn': '개봉일 스크린수 (개)',
        'total_audi': '총 관객수 (명)',
        'genre': '장르'
    },
    color_discrete_sequence=px.colors.qualitative.Dark24
)

fig_scatter.update_traces(
    marker=dict(size=10, opacity=0.8),
    hovertemplate="<b>영화명:</b> %{hovertext}<br><b>장르:</b> %{fullData.name}<br><b>개봉일 스크린수:</b> %{x:,}개<br><b>총 관객수:</b> %{y:,}명<extra></extra>"
)

fig_scatter.update_layout(
    title_font_size=18,
    xaxis_title="개봉일 스크린수 (개)",
    yaxis_title="총 관객수 (명)",
    legend_title_text="장르",
    margin=dict(t=50, b=20, l=20, r=20)
)

st.plotly_chart(fig_scatter, use_container_width=True)

st.divider()
st.info("💡 **이 그래프로 알 수 있는 것**\n\n- 초기 스크린 확보 수(개봉일 스크린수)가 최종 관객 수 흥행에 결정적인 양의 영향을 미치는지, 스크린 수가 적어도 입소문을 통해 대역전에 성공한 영화가 존재하는지 등의 상관관계를 시각적으로 분석할 수 있습니다.")

st.markdown("---")

# 8. 다섯 번째 그래프: 영화 10편 이상인 장르별 총 관객수 상자 그림 (박스플롯)
st.subheader("📌 5. 주요 장르별 총 관객수 분포 (박스플롯)")

# 영화가 10편 이상인 장르 필터링
genre_counts_series = df['genre'].value_counts()
major_genres = genre_counts_series[genre_counts_series >= 10].index
df_major_genres = df[df['genre'].isin(major_genres)].copy()

fig_box = px.box(
    df_major_genres,
    x='genre',
    y='total_audi',
    color='genre',
    points='outliers',  # 이상치 점만 표시
    hover_name='movieNm',
    title='영화 10편 이상 장르의 관객수 분포 및 이상치(대박작)',
    labels={
        'genre': '장르',
        'total_audi': '총 관객수 (명)'
    },
    color_discrete_sequence=px.colors.qualitative.Set2
)

fig_box.update_traces(
    hovertemplate="<b>영화명:</b> %{hovertext}<br><b>장르:</b> %{x}<br><b>총 관객수:</b> %{y:,}명<extra></extra>"
)

fig_box.update_layout(
    title_font_size=18,
    xaxis_title="장르 (영화 10편 이상)",
    yaxis_title="총 관객수 (명)",
    showlegend=False,
    margin=dict(t=50, b=20, l=20, r=20)
)

st.plotly_chart(fig_box, use_container_width=True)

st.divider()
st.info("💡 **이 그래프로 알 수 있는 것**\n\n- 주요 장르별 흥행의 중간값과 안정적인 흥행 범위(박스의 높이)를 파악할 수 있으며, 박스 위로 멀리 떨어진 이상치(Outlier) 점에 마우스를 올려 동일 장르 내에서 독보적인 흥행 성적을 거둔 초대형 대박 영화가 무엇인지 확인할 수 있습니다.")
