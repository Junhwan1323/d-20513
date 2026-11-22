import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import KFold, cross_val_score
import streamlit as st

# ---------------------------------------------------------
# 1. Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="다이아몬드 가격 예측 분석 대시보드",
    page_icon="💎",
    layout="wide",
)

# Train 세트 기준 StandardScaler 통계량 (데이터 누수 방지용 고정 기준값)
# 순서: [ln(carat), depth, table]
TRAIN_SCALER_MEAN = np.array([-0.39589578, 61.74957338, 57.45633646])
TRAIN_SCALER_SCALE = np.array([0.58550174, 1.42942702, 2.23149751])

CUT_LEVELS = ["Fair", "Good", "Very Good", "Premium", "Ideal"]
COLOR_LEVELS = ["D", "E", "F", "G", "H", "I", "J"]
CLARITY_LEVELS = ["I1", "SI2", "SI1", "VS2", "VS1", "VVS2", "VVS1", "IF"]


# ---------------------------------------------------------
# 2. Data Loading & Model Training (Cached)
# ---------------------------------------------------------
@st.cache_resource
def load_and_train():
    train_df = pd.read_csv("diamonds_train-v2.csv")
    test_df = pd.read_csv("diamonds_test-v2.csv")

    feature_cols = [c for c in train_df.columns if c not in ["log_price", "price"]]

    X_train = train_df[feature_cols]
    y_train_log = train_df["log_price"]
    y_train_dollar = train_df["price"]

    X_test = test_df[feature_cols]
    y_test_log = test_df["log_price"]
    y_test_dollar = test_df["price"]

    model = LinearRegression()
    model.fit(X_train, y_train_log)

    # 5-Fold Cross Validation
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    cv_r2_log = cross_val_score(model, X_train, y_train_log, cv=kf, scoring="r2")

    # Predictions
    pred_train_log = model.predict(X_train)
    pred_train_dollar = np.exp(pred_train_log)

    pred_test_log = model.predict(X_test)
    pred_test_dollar = np.exp(pred_test_log)

    metrics = {
        "cv_r2_mean": cv_r2_log.mean(),
        "cv_r2_std": cv_r2_log.std(),
        "train_r2_log": r2_score(y_train_log, pred_train_log),
        "test_r2_log": r2_score(y_test_log, pred_test_log),
        "test_rmse_log": np.sqrt(mean_squared_error(y_test_log, pred_test_log)),
        "train_rmse_dollar": np.sqrt(mean_squared_error(y_train_dollar, pred_train_dollar)),
        "test_rmse_dollar": np.sqrt(mean_squared_error(y_test_dollar, pred_test_dollar)),
        "train_mae_dollar": mean_absolute_error(y_train_dollar, pred_train_dollar),
        "test_mae_dollar": mean_absolute_error(y_test_dollar, pred_test_dollar),
        "test_mape": mean_absolute_percentage_error(y_test_dollar, pred_test_dollar) * 100,
        "test_r2_dollar": r2_score(y_test_dollar, pred_test_dollar),
        "neg_count": int((pred_test_dollar < 0).sum()),
    }

    coef_df = pd.DataFrame(
        {
            "Feature": feature_cols,
            "Coefficient (Log)": model.coef_,
            "Price Multiplier (exp)": np.exp(model.coef_),
            "Pct Change (%)": (np.exp(model.coef_) - 1) * 100,
        }
    )

    eval_df = pd.DataFrame(
        {
            "actual_log": y_test_log.values,
            "pred_log": pred_test_log,
            "res_log": y_test_log.values - pred_test_log,
            "actual_dollar": y_test_dollar.values,
            "pred_dollar": pred_test_dollar,
            "res_dollar": y_test_dollar.values - pred_test_dollar,
        }
    )

    return model, feature_cols, metrics, coef_df, eval_df, train_df, test_df


def encode_user_input(carat, depth, table, cut, color, clarity, feature_cols):
    raw_num = np.array([np.log(carat), depth, table])
    scaled_num = (raw_num - TRAIN_SCALER_MEAN) / TRAIN_SCALER_SCALE

    row = {col: 0.0 for col in feature_cols}
    row["log_carat_scaled"] = scaled_num[0]
    row["depth_scaled"] = scaled_num[1]
    row["table_scaled"] = scaled_num[2]

    # OneHotEncoder(drop='first') 규칙 반영 (기준 범주: Fair, D, I1 -> 모두 0)
    if f"cut_{cut}" in row:
        row[f"cut_{cut}"] = 1.0
    if f"color_{color}" in row:
        row[f"color_{color}"] = 1.0
    if f"clarity_{clarity}" in row:
        row[f"clarity_{clarity}"] = 1.0

    return pd.DataFrame([row])[feature_cols]


# ---------------------------------------------------------
# 3. Main Application
# ---------------------------------------------------------
try:
    model, feature_cols, metrics, coef_df, eval_df, train_df, test_df = load_and_train()
except FileNotFoundError:
    st.error(
        "데이터 파일(`diamonds_train-v2.csv`, `diamonds_test-v2.csv`)을 찾을 수 없습니다. "
        "GitHub 저장소 최상위 경로에 두 CSV 파일을 `main.py`와 함께 업로드해 주세요."
    )
    st.stop()

n_train, n_test = len(train_df), len(test_df)

st.title("💎 다이아몬드 가격 예측 및 회귀 분석 대시보드")
st.caption(
    f"정제 데이터 53,767행 (80:20 가격 층화 분할 — Train {n_train:,}행 / Test {n_test:,}행) | "
    "Log-Log 다중 선형 회귀 모델"
)

# ---------------------------------------------------------
# Sidebar: Real-time Price Simulator
# ---------------------------------------------------------
st.sidebar.header("🔍 다이아몬드 스펙 입력")
st.sidebar.markdown("원하는 조건을 입력하면 학습된 선형 회귀 모델이 실시간으로 달러($) 가격을 예측합니다.")

in_carat = st.sidebar.slider("캐럿 (Carat)", min_value=0.20, max_value=3.50, value=1.00, step=0.01)
in_cut = st.sidebar.selectbox("커팅 등급 (Cut)", options=CUT_LEVELS, index=4)
in_color = st.sidebar.selectbox("색상 등급 (Color, D=최상 ~ J=최하)", options=COLOR_LEVELS, index=3)
in_clarity = st.sidebar.selectbox("투명도 등급 (Clarity, I1=최하 ~ IF=최상)", options=CLARITY_LEVELS, index=3)
in_depth = st.sidebar.slider("깊이 비율 (Depth %)", min_value=50.0, max_value=72.0, value=61.8, step=0.1)
in_table = st.sidebar.slider("테이블 비율 (Table %)", min_value=50.0, max_value=70.0, value=57.0, step=0.1)

input_X = encode_user_input(in_carat, in_depth, in_table, in_cut, in_color, in_clarity, feature_cols)
pred_log_val = model.predict(input_X)[0]
pred_dollar_val = float(np.exp(pred_log_val))

st.sidebar.markdown("---")
st.sidebar.subheader("💰 실시간 예측 결과")
st.sidebar.metric(label="예상 가격 (USD)", value=f"${pred_dollar_val:,.2f}")
st.sidebar.caption(f"로그 예측값 ln(price): `{pred_log_val:.4f}` | MAE 오차 범위: ±`${metrics['test_mae_dollar']:,.0f}`")

# ---------------------------------------------------------
# Tabs: Detailed Analytical Report
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs(
    [
        "1️⃣ 모델 성능 및 예측 시뮬레이터",
        "2️⃣ 회귀 계수 및 등급별 가격 배율",
        "3️⃣ 데이터 정제 및 전처리 상세 파이프라인",
    ]
)

# === Tab 1: Performance & Simulator ===
with tab1:
    st.subheader("테스트 세트(Test Set, n = 10,754) 일반화 성능 지표")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("결정계수 R² (로그 단위)", f"{metrics['test_r2_log']:.4f}", f"CV 평균 {metrics['cv_r2_mean']:.4f}")
    c2.metric("결정계수 R² (달러 복원)", f"{metrics['test_r2_dollar']:.4f}")
    c3.metric("평균 절대 오차 (MAE)", f"${metrics['test_mae_dollar']:,.2f}", f"MAPE {metrics['test_mape']:.2f}%")
    c4.metric("제곱근 오차 (RMSE)", f"${metrics['test_rmse_dollar']:,.2f}", f"음수 예측 {metrics['neg_count']}건")

    st.markdown("---")
    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        st.markdown("#### 실제 가격 vs 모델 예측 가격 (테스트 세트 샘플 2,000건)")
        sample_eval = eval_df.sample(n=2000, random_state=42)
        fig1, ax1 = plt.subplots(figsize=(7, 5))
        ax1.scatter(sample_eval["actual_dollar"], sample_eval["pred_dollar"], alpha=0.25, s=12, color="#2b5c8f")
        max_val = max(sample_eval["actual_dollar"].max(), sample_eval["pred_dollar"].max())
        ax1.plot([0, max_val], [0, max_val], color="#d62728", linestyle="--", linewidth=1.5, label="Perfect Prediction (y = x)")
        ax1.scatter([pred_dollar_val], [pred_dollar_val], color="#ff7f0e", s=120, zorder=5, label=f"Current Input (${pred_dollar_val:,.0f})")
        ax1.set_xlabel("Actual Price ($)")
        ax1.set_ylabel("Predicted Price ($)")
        ax1.set_title("Actual vs. Predicted Price (USD)")
        ax1.legend()
        st.pyplot(fig1)

    with col_right:
        st.markdown("#### 테스트 세트 실제 예측 비교 샘플 (상위 10건)")
        preview = eval_df[["actual_dollar", "pred_dollar", "res_dollar"]].head(10).copy()
        preview.columns = ["실제 가격 ($)", "예측 가격 ($)", "오차 (실제-예측 $)"]
        preview["오차율 (%)"] = (preview["오차 (실제-예측 $)"].abs() / preview["실제 가격 ($)"] * 100).round(2)
        st.dataframe(preview.round(2), use_container_width=True, hide_index=True)

# === Tab 2: Regression Coefficients ===
with tab2:
    st.subheader("회귀 계수(가중치) 및 기준 범주 대비 가격 변화율")
    st.info(
        "타깃 변수에 자연로그(ln)를 적용했으므로, 각 회귀 계수 w에 지수 함수 exp(w)를 취한 값은 "
        "**다른 조건이 동일할 때 해당 변수가 가격에 곱해지는 배율**을 나타냅니다."
    )

    col_c1, col_c2 = st.columns([1.1, 1])

    with col_c1:
        cat_coef = coef_df[~coef_df["Feature"].str.contains("scaled")].copy()
        cat_coef = cat_coef.sort_values("Pct Change (%)", ascending=True)
        colors = ["#d62728" if v < 0 else "#2b5c8f" for v in cat_coef["Pct Change (%)"]]

        fig2, ax2 = plt.subplots(figsize=(7, 6))
        ax2.barh(cat_coef["Feature"], cat_coef["Pct Change (%)"], color=colors)
        ax2.axvline(0, color="black", linewidth=1)
        ax2.set_xlabel("Price Change vs. Baseline Category (%)")
        ax2.set_title("Grade Impact on Price (Cut: Fair, Color: D, Clarity: I1)")
        st.pyplot(fig2)

    with col_c2:
        st.markdown("#### 전체 회귀 계수 상세 표")
        display_coef = coef_df.copy()
        display_coef.columns = ["변수명", "회귀 계수 (Log)", "가격 배율 exp(w)", "기준 대비 변화율 (%)"]
        st.dataframe(display_coef.round(4), use_container_width=True, hide_index=True, height=450)

# === Tab 3: Detailed Preprocessing Documentation ===
with tab3:
    st.subheader("1단계. 원본 데이터 정제(Data Cleaning) 상세 이력")
    st.markdown("원본 `diamonds.csv` **53,940행**에서 물리적·통계적 오류 데이터 총 **173행(0.32%)**을 제거하여 **53,767행**을 확보했습니다.")

    cleaning_tbl = pd.DataFrame(
        [
            ["원본 데이터", "초기 데이터 로드 (결측치 Null 0건 확인)", "-", "53,940행"],
            ["정제 1단계", "완전 중복 행 제거 (`drop_duplicates()`, 동일 스펙·가격 레코드 중 1건 유지)", "-146행", "53,794행"],
            ["정제 2단계", "치수 `0` 이상치 제거 (`x == 0` 또는 `y == 0` 또는 `z == 0`인 물리적 불가 데이터)", "-19행", "53,775행"],
            ["정제 3단계", "극단적 입력 오류 제거 (소수점 밀림 `y=58.90, z=31.80, y=31.80` 및 `depth` 계산식 불일치)", "-8행", "53,767행"],
        ],
        columns=["단계", "처리 내용 및 기준", "제거 행 수", "잔여 행 수"],
    )
    st.dataframe(cleaning_tbl, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("2단계. 변수 선택 (B 조합) 및 다중공선성(VIF) 해결")
    st.markdown(
        """
        - **제외 변수 (`x`, `y`, `z` — 3개 삭제):** 다이아몬드의 가로·세로·높이 치수는 무게(`carat`) 및 깊이 비율(`depth`)과 강한 수학적 종속 관계를 가지며, 포함 시 **VIF > 880**의 극심한 다중공선성을 유발하여 회귀 계수를 왜곡하므로 제외했습니다.
        - **최종 선택 변수 (독립변수 6개 + 타깃 1개):** `carat`, `depth`, `table`, `cut`, `color`, `clarity` $\\rightarrow$ 타깃 `price`
        - **다중공선성 안정화 검증:** `x, y, z` 제거 후 잔여 수치형 독립변수(`log_carat`, `depth`, `table`)의 **VIF는 모두 1.05 ~ 1.15** 범위로 낮아져 개별 회귀 계수의 통계적 신뢰성을 확보했습니다.
        """
    )

    st.markdown("---")
    st.subheader("3단계. 변수 유형별 수학적 변환 및 인코딩 규칙")

    prep_tbl = pd.DataFrame(
        [
            [
                "수치형 독립변수",
                "carat",
                "1) 자연로그 변환 ln(carat)\n2) 표준화 (StandardScaler)",
                "우측 편향 분포와 가격과의 지수적 곡선 관계를 선형(직선) 관계로 변환 후 단위 통일",
            ],
            [
                "수치형 독립변수",
                "depth, table",
                "표준화 (StandardScaler)",
                "이미 좌우 대칭에 가까운 비율(%) 데이터이므로 로그 변환 없이 스케일링만 수행",
            ],
            [
                "범주형 독립변수",
                "cut, color, clarity",
                "원-핫 인코딩\nOneHotEncoder(drop='first')",
                "등급 간 가격 상승폭의 비균등성을 반영하며, 더미 변수 함정(다중공선성) 방지를 위해 기준 범주(Fair, D, I1) 1개씩 제거 (총 17개 더미 열 생성)",
            ],
            [
                "타깃 변수 (종속)",
                "price",
                "학습: 자연로그 변환 ln(price)\n예측: 지수 역변환 exp(y_pred)",
                "소형 다이아몬드의 음수($0 미만) 가격 예측 원천 차단 및 비율(%) 단위 가격 변동 반영",
            ],
        ],
        columns=["변수 구분", "대상 변수", "적용 기법", "적용 근거 및 세부 규칙"],
    )
    st.dataframe(prep_tbl, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("4단계. 데이터 분할(80:20 층화 분할) 및 데이터 누수 방지")
    col_s1, col_s2 = st.columns([1.1, 1])

    with col_s1:
        st.markdown(
            """
            - **분할 비율 및 방식:** 전체 53,767행을 타깃 `price`의 **10분위수(Decile) 기준 층화 추출(`stratify`)**로 **80% 학습 세트(43,013행)**와 **20% 테스트 세트(10,754행)**로 분할했습니다.
            - **데이터 누수(Data Leakage) 차단:** `StandardScaler`의 평균($\\mu$)과 표준편차($\\sigma$) 및 `OneHotEncoder`의 범주 매핑은 **오직 학습 세트(`Train`)에서만 `fit()`** 하여 산출했으며, 테스트 세트(`Test`)와 웹앱 사용자 입력값에는 학습 세트의 기준값을 그대로 `transform()` 적용합니다.
            - **학습 세트 표준화 기준값 (`Train` 43,013행 산출):**
              - `ln(carat)`: 평균 = `-0.39589578`, 표준편차 = `0.58550174`
              - `depth`: 평균 = `61.74957338`, 표준편차 = `1.42942702`
              - `table`: 평균 = `57.45633646`, 표준편차 = `2.23149751`
            """
        )

    with col_s2:
        split_comp = pd.DataFrame(
            {
                "통계량": ["데이터 행 수", "평균 가격 ($)", "중앙값 가격 ($)", "표준편차 ($)", "최솟값 ($)", "최댓값 ($)"],
                "Train 세트 (80%)": [
                    f"{len(train_df):,}행",
                    f"${train_df['price'].mean():,.2f}",
                    f"${train_df['price'].median():,.2f}",
                    f"${train_df['price'].std():,.2f}",
                    f"${train_df['price'].min():,.2f}",
                    f"${train_df['price'].max():,.2f}",
                ],
                "Test 세트 (20%)": [
                    f"{len(test_df):,}행",
                    f"${test_df['price'].mean():,.2f}",
                    f"${test_df['price'].median():,.2f}",
                    f"${test_df['price'].std():,.2f}",
                    f"${test_df['price'].min():,.2f}",
                    f"${test_df['price'].max():,.2f}",
                ],
            }
        )
        st.markdown("**층화 분할 전후 가격 분포 검증표**")
        st.dataframe(split_comp, use_container_width=True, hide_index=True)

    with st.expander("🔎 전처리 완료된 학습 데이터(`diamonds_train-v2.csv`) 실제 피처 구조 미리보기 (상위 5행)"):
        st.dataframe(train_df.head(5).round(4), use_container_width=True)
