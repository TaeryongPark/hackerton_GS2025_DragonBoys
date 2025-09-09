# app.py
import datetime as dt
from typing import List, Dict
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ---------------------------
# 페이지 기본 설정
# ---------------------------
st.set_page_config(
    page_title="금융 지표 대시보드",
    page_icon="📈",
    layout="wide",
)

# ---------------------------
# 간단한 스타일
# ---------------------------
st.markdown(
    """
    <style>
      .card { background:#fff; border:1px solid #e9ecef; border-radius:14px;
              padding:16px 18px; margin-bottom:14px; box-shadow:0 1px 2px rgba(0,0,0,0.04); }
      .section-title { font-weight:700; font-size:18px; margin-bottom:8px; }
      .muted { color:#868e96; }
      .badge { display:inline-block; padding:2px 8px; font-size:12px; border-radius:999px;
               background:#e7f5ff; color:#1971c2; margin-left:6px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------
# (1) 데이터 준비
#    → 이 부분만 여러분 결과로 교체해서 사용하면 됩니다.
# ---------------------------

# 예시 입력 (문자열 YYYYMMDD 5개)
dates_raw: List[str] = ["2025-08-25", "2025-08-26", "2025-08-27", "2025-08-28", "2025-08-29"]
# 만약 여러분이 '20250829' 형식이라면 아래처럼 변환:
# dates_raw = [pd.to_datetime(d).strftime("%Y-%m-%d") for d in ['20250825','20250826','20250827','20250828','20250829']]

# 금리 4종 (5개 값씩)
cd91  = [2.53, 2.53, 2.53, 2.53, 2.53]      # ← 여러분 결과로 교체
cp91  = [2.73, 2.73, 2.73, 2.73, 2.73]      # ← 여러분 결과로 교체
tb3y  = [2.434, 2.422, 2.402, 2.416, 2.426] # ← 여러분 결과로 교체
tb5y  = [2.602, 2.596, 2.569, 2.576, 2.583] # ← 여러분 결과로 교체

# 환율 4종 (5개 값씩)
usdkrw = [1395.6, 1386.3, 1391.2, 1395.7, 1388.6]  # ← 여러분 결과로 교체 (원/달러 매매기준율)
cnykrw = [194.46, 193.71, 194.35, 195.11, 194.14]  # ← 여러분 결과로 교체 (원/위안)
jpy100 = [948.65, 937.92, 943.51, 947.52, 944.79]  # ← 여러분 결과로 교체 (원/100엔)
eurkrw = [1634.60, 1610.67, 1619.57, 1625.08, 1621.61]  # ← 여러분 결과로 교체 (원/유로)

# 검증: 모두 5개인지
assert all(len(x) == 5 for x in [dates_raw, cd91, cp91, tb3y, tb5y, usdkrw, cnykrw, jpy100, eurkrw]), "데이터는 5개씩이어야 합니다."

# DataFrame 생성 (x축 날짜는 오름차순)
dates = pd.to_datetime(dates_raw)
df_rates = pd.DataFrame({
    "날짜": dates,
    "CD(91일)": cd91,
    "CP(91일)": cp91,
    "국고채(3년)": tb3y,
    "국고채(5년)": tb5y,
}).sort_values("날짜")

df_fx = pd.DataFrame({
    "날짜": dates,
    "USD/KRW": usdkrw,
    "CNY/KRW": cnykrw,
    "JPY(100)/KRW": jpy100,
    "EUR/KRW": eurkrw,
}).sort_values("날짜")

# 전일 대비 계산 (표시용)
def add_delta(df: pd.DataFrame, col: str) -> str:
    s = df[col].astype(float)
    delta = s.iloc[-1] - s.iloc[-2]
    arrow = "▲" if delta > 0 else ("▼" if delta < 0 else "—")
    return f"{arrow} {abs(delta):,.2f}"

kpi_rate = {
    "CD(91일)": (df_rates["CD(91일)"].iloc[-1], add_delta(df_rates, "CD(91일)")),
    "CP(91일)": (df_rates["CP(91일)"].iloc[-1], add_delta(df_rates, "CP(91일)")),
    "국고채(3년)": (df_rates["국고채(3년)"].iloc[-1], add_delta(df_rates, "국고채(3년)")),
    "국고채(5년)": (df_rates["국고채(5년)"].iloc[-1], add_delta(df_rates, "국고채(5년)")),
}
kpi_fx = {
    "USD/KRW": (df_fx["USD/KRW"].iloc[-1], add_delta(df_fx, "USD/KRW")),
    "CNY/KRW": (df_fx["CNY/KRW"].iloc[-1], add_delta(df_fx, "CNY/KRW")),
    "JPY(100)/KRW": (df_fx["JPY(100)/KRW"].iloc[-1], add_delta(df_fx, "JPY(100)/KRW")),
    "EUR/KRW": (df_fx["EUR/KRW"].iloc[-1], add_delta(df_fx, "EUR/KRW")),
}

# ---------------------------
# (2) 화면 헤더
# ---------------------------
left, mid, right = st.columns([3, 1.4, 1.2])
with left:
    st.title("금융 지표 대시보드")
    st.caption("5영업일 기준 금리/환율 추이")

with mid:
    st.write("")
    st.write("")
    st.markdown(f"**업데이트:** {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}")

with right:
    st.write("")
    st.write("")
    if st.button("🔄 새로고침"):
        st.experimental_rerun()

st.markdown("---")

# ---------------------------
# (3) 좌/우 2단 레이아웃
# ---------------------------
col_l, col_r = st.columns([1.2, 1.0])

# ---------- 왼쪽: 금리/환율 그래프 ----------
with col_l:
    # 금리 카드
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>금리 (5영업일)</div>", unsafe_allow_html=True)

    # 상단 KPI
    k1,k2,k3,k4 = st.columns(4)
    for (label, (val, d)), slot in zip(kpi_rate.items(), [k1,k2,k3,k4]):
        with slot:
            st.metric(label, f"{val:,.3f}%", d)

    # Plotly 라인차트 (금리 4종)
    fig_r = go.Figure()
    for col in ["CD(91일)", "CP(91일)", "국고채(3년)", "국고채(5년)"]:
        fig_r.add_trace(go.Scatter(
            x=df_rates["날짜"], y=df_rates[col], mode="lines+markers", name=col
        ))
    fig_r.update_layout(
        margin=dict(l=0,r=0,t=8,b=0),
        height=320,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis_title="", yaxis_title="(%)",
    )
    st.plotly_chart(fig_r, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

    # 환율 카드
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>환율 (5영업일)</div>", unsafe_allow_html=True)

    k1,k2,k3,k4 = st.columns(4)
    for (label, (val, d)), slot in zip(kpi_fx.items(), [k1,k2,k3,k4]):
        with slot:
            st.metric(label, f"{val:,.2f}", d)

    fig_fx = go.Figure()
    for col in ["USD/KRW", "CNY/KRW", "JPY(100)/KRW", "EUR/KRW"]:
        fig_fx.add_trace(go.Scatter(
            x=df_fx["날짜"], y=df_fx[col], mode="lines+markers", name=col
        ))
    fig_fx.update_layout(
        margin=dict(l=0,r=0,t=8,b=0),
        height=320,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis_title="", yaxis_title="(KRW)",
    )
    st.plotly_chart(fig_fx, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

# ---------- 오른쪽: 증권사 전망 카드 ----------
with col_r:
    st.subheader("환율 전망 (요약)")

    # 임의 값/문장 — 실제로는 여러분 요약 문자열로 교체
    outlooks: List[Dict] = [
        {"기관":"신한투자증권", "기간":"최근 1주", "내용":"연준의 정책 완화 기대와 수출 회복세를 근거로 원화 강세 가능성. 1,360~1,390 박스권 전망."},
        {"기관":"키움증권", "기간":"최근 2주", "내용":"달러 인덱스 반등에도 국내 외환수급 개선으로 하방 경직. 수입 결제 수요 구간에서 변동성 확대 유의."},
        {"기관":"하나증권", "기간":"최근 4주", "내용":"중국 부양책과 엔화 강세가 아시아 통화에 우호적. 분기말 레벨 체크 시 1,350대 테스트 가능성 언급."},
    ]

    for o in outlooks:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown(f"**{o['기관']}** <span class='badge'>{o['기간']}</span>", unsafe_allow_html=True)
        st.markdown(f"<div class='muted' style='margin-top:6px'>{o['내용']}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------
# (4) 하단: 원시데이터 표(옵션)
# ---------------------------
with st.expander("📄 원시 데이터 보기", expanded=False):
    st.write("금리")
    st.dataframe(df_rates.assign(날짜=df_rates["날짜"].dt.strftime("%Y-%m-%d")), hide_index=True, use_container_width=True)
    st.write("환율")
    st.dataframe(df_fx.assign(날짜=df_fx["날짜"].dt.strftime("%Y-%m-%d")), hide_index=True, use_container_width=True)
