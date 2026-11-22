
면목고등학교 채팅은 Gemini 모델을 개선하는 데 사용되지 않습니다. Gemini는 사람이 아니며, 인물 등에 관한 정보 제공 시 실수를 할 수 있으니 대답을 다시 한번 확인하세요. 개인 정보 보호 및 Gemini새 창에서 열기

PY 아이콘
main
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import scipy.stats as stats
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import KFold, cross_val_score
from sklearn.metrics import (
    mean_squared_error,
    mean_absolute_error,
    r2_score,
    mean_absolute_percentage_error,
)

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

    return model, feature_cols, metrics, coef_df, eval_df, len(train_df), len(test_df)


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
    model, feature_cols, metrics, coef_df, eval_df, n_train, n_test = load_and_train()
except FileNotFoundError:
    st.error(
        "데이터 파일(`diamonds_train-v2.csv`, `diamonds_test-v2.csv`)을 찾을 수 없습니다. "
        "GitHub 저장소 최상위 경로에 두 CSV 파일을 `main.py`와 함께 업로드해 주세요."
    )
    st.stop()

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
tab1, tab2, tab3, tab4 = st.tabs(
    [
        "1️⃣ 모델 성능 및 예측 시뮬레이터",
        "2️⃣ 회귀 계수 및 등급별 가격 배율",
        "3️⃣ 잔차 분석 및 가격대별 오차",
        "4️⃣ 데이터 정제 및 전처리 설계 요약",
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
        preview.columns = ["실제 가격 ($)", "예측 가격 ($)", "잔차 (실제-예측 $)"]
        preview["오차율 (%)"] = (preview["잔차 (실제-예측 $)"].abs() / preview["실제 가격 ($)"] * 100).round(2)
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

# === Tab 3: Residual Analysis ===
with tab3:
    st.subheader("잔차(Residual = 실제값 - 예측값) 진단 및 가격대별 오차 분석")

    # Price tier table
    eval_tier = eval_df.copy()
    eval_tier["abs_err"] = eval_tier["res_dollar"].abs()
    eval_tier["pct_err"] = eval_tier["abs_err"] / eval_tier["actual_dollar"] * 100
    eval_tier["tier"] = pd.cut(
        eval_tier["actual_dollar"],
        bins=[0, 1000, 3000, 6000, 10000, 20000],
        labels=["$1,000 미만", "$1,000 ~ $3,000", "$3,000 ~ $6,000", "$6,000 ~ $10,000", "$10,000 초과"],
    )
    tier_tbl = (
        eval_tier.groupby("tier", observed=False)
        .agg(
            표본수=("actual_dollar", "count"),
            평균실제가격=("actual_dollar", "mean"),
            MAE_달러=("abs_err", "mean"),
            RMSE_달러=("abs_err", lambda x: np.sqrt(np.mean(x**2))),
            MAPE_퍼센트=("pct_err", "mean"),
        )
        .reset_index()
    )
    tier_tbl.columns = ["실제 가격 구간", "표본 수", "구간 평균 가격 ($)", "MAE ($)", "RMSE ($)", "MAPE (%)"]
    st.dataframe(tier_tbl.round(2), use_container_width=True, hide_index=True)

    st.markdown("---")
    fig3, axes = plt.subplots(1, 3, figsize=(15, 4.5))

    # Plot 1: Residuals vs Fitted (Log)
    axes[0].scatter(eval_df["pred_log"], eval_df["res_log"], alpha=0.15, s=8, color="#2b5c8f")
    axes[0].axhline(0, color="#d62728", linestyle="--", linewidth=1.2)
    axes[0].set_title("Residuals vs. Fitted (Log Scale)")
    axes[0].set_xlabel("Predicted Log Price")
    axes[0].set_ylabel("Log Residual")

    # Plot 2: Residuals vs Fitted (Dollar)
    axes[1].scatter(eval_df["pred_dollar"], eval_df["res_dollar"], alpha=0.15, s=8, color="#2b5c8f")
    axes[1].axhline(0, color="#d62728", linestyle="--", linewidth=1.2)
    axes[1].set_title("Residuals vs. Fitted (Dollar Scale)")
    axes[1].set_xlabel("Predicted Price ($)")
    axes[1].set_ylabel("Dollar Residual ($)")

    # Plot 3: Normal Q-Q Plot
    stats.probplot(eval_df["res_log"], dist="norm", plot=axes[2])
    axes[2].get_lines()[0].set_markerfacecolor("#2b5c8f")
    axes[2].get_lines()[0].set_markeredgecolor("none")
    axes[2].get_lines()[0].set_alpha(0.3)
    axes[2].get_lines()[0].set_markersize(4)
    axes[2].get_lines()[1].set_color("#d62728")
    axes[2].set_title("Normal Q-Q Plot (Log Residuals)")

    plt.tight_layout()
    st.pyplot(fig3)

    st.warning(
        "**한계점 요약:** $6,000 미만 구간(전체의 78.5%)에서는 MAE가 $87~$402 수준으로 안정적이나, "
        "$10,000 초과 고가 구간에서는 캐럿과 등급 간 비선형 교호작용으로 인해 과대 예측(RMSE $2,159)이 발생합니다."
    )

# === Tab 4: Methodology Summary ===
with tab4:
    st.subheader("데이터 정제 및 전처리 파이프라인 요약")
    st.markdown(
        """
        1. **데이터 정제 (53,940행 → 53,767행, 총 173행 제거)**
           - 완전 중복 레코드 146행 제거 (1건 유지)
           - 치수(`x`, `y`, `z`) 중 하나라도 `0`인 물리적 불가능 데이터 19행 제거
           - 소수점 오기입(`y=58.90`, `z=31.80`, `y=31.80`) 및 `depth` 공식 불일치 극단 이상치 8행 제거
        2. **변수 선택 (B 조합: 다중공선성 제거)**
           - `carat` 및 `depth`와 극심한 다중공선성(`VIF > 880`)을 유발하는 `x, y, z` 제외
           - 최종 독립변수 6개(`carat`, `depth`, `table`, `cut`, `color`, `clarity`) 사용 시 잔여 수치형 변수 `VIF = 1.05 ~ 1.15` 확보
        3. **전처리 및 80:20 층화 분할**
           - `carat`, `price`: 지수적 곡선 관계를 직선으로 변환하고 음수 가격 예측(`$0` 미만)을 방지하기 위해 자연로그(`ln`) 변환
           - `log_carat`, `depth`, `table`: `Train` 세트 기준으로만 `StandardScaler` 적합 후 `Test` 세트 변환 (데이터 누수 방지)
           - `cut`, `color`, `clarity`: `OneHotEncoder(drop='first')` 적용 (기준 범주: `Fair`, `D`, `I1`)
        """
    )
