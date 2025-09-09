from Finance_data import fetch_interest_rates, fetch_exchange_rates
from datetime import date
from KB_download import download_kb_file
from Hana_download import download_hana_market_daily
import time
from Gemini import summarize_pdf

user_prompt = """해당 환율전망보고서를 자세히 분석해줘.
다음 항목을 반드시 포함해서 요약해:

1. Daily 환율 전망
   - 원/달러 환율을 "원/달러 ○○○○~○○○○원" 형태로 제시하고, 예상 방향성(상승/하락/보합)을 한 문장으로 설명해.

2. 주요 환율 전망
   - 달러/원, 유로/원, 엔/원, 위안/원 각각에 대해 ‘달러 강세 / 보합 / 약세’ 관점으로 정리해.
   - 각 통화쌍별 핵심 근거(경제지표, 통화·재정정책, 수급, 지정학·정치 요인 등)를 구체적으로 적어줘.

3. 종합 결론
   - 전체 환율 흐름을 3~5줄로 종합 정리하고, 단기 요인과 중기 요인을 구분해 서술해.

요약은 가능한 한 구체적이고 전문적인 표현을 사용하되, 표나 목록 없이 일반 텍스트로 작성해.
특히 화면 표시를 위해 Markdown 기호(##, #, *, **, -, >, ` 등)는 사용하지 말아줘.
필요시 문단을 빈 줄로만 구분해줘."""

# 오늘 날짜를 YYYYMMDD로 전달
today = date.today().strftime("%Y%m%d")
today_str = date.today().strftime("%Y년 %m월 %d일")

df_ir = fetch_interest_rates(today)
df_fx = fetch_exchange_rates(today)

print("📊 금리 데이터")
print(df_ir)

print("\n💱 환율 데이터")
print(df_fx)

# 함수 호출만 하면 자동으로 같은 폴더에 파일 저장됨
path_KB, fname_KB = download_kb_file()
path_HANA, fname_HANA = download_hana_market_daily()

print("다운로드 완료:", fname_KB)
print("다운로드 완료:", fname_HANA)

time.sleep(3)  # 5초 동안 멈춤

# main에서 input 값 넣기
file_name_KB = fname_KB
file_name_HANA = fname_HANA
# user_prompt = "해당 파일을 분석해줘. daily 환율 전망 - 원달러 0000원 형태로 한문장 알려줘. 그리고 주요 환율전망 각 소제목 내용을 달러 강세,보합,약세로 구분 후 종합 결론을 세줄로 작성해줘."

result_KB = summarize_pdf(file_name_KB, user_prompt)
result_HANA = summarize_pdf(file_name_HANA, user_prompt)

print("\n===== 요약 결과 =====\n")
print(result_KB)
print(result_HANA)


import datetime as dt
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from typing import List, Dict

# ========================================
# (1) Streamlit 페이지 기본 설정
# ========================================
st.set_page_config(
    page_title=f"Daily({today_str}) 금융시장 동향",
    page_icon="📈",
    layout="wide",
)

# 간단한 CSS
st.markdown(
    """
    <style>
      .card { background:#fff; border:1px solid #e9ecef; border-radius:14px;
              padding:16px 18px; margin-bottom:14px; box-shadow:0 1px 2px rgba(0,0,0,0.04); }
      .section-title { font-weight:700; font-size:18px; margin-bottom:8px; }
      .muted { color:#868e96; }
      .badge { display:inline-block; padding:2px 8px; font-size:12px; border-radius:999px;
               background:#e7f5ff; color:#1971c2; margin-left:6px; }
      pre { white-space:pre-wrap; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ========================================
# (2) 공통: 인덱스 → 날짜 파싱 유틸
# ========================================
def _parse_index_to_datetime(idx) -> pd.DatetimeIndex:
    # 'YYYYMMDD' 또는 'YYYY-MM-DD' 모두 허용
    s = pd.Series(idx.astype(str))
    s = s.str.replace("-", "", regex=False)
    return pd.to_datetime(s, format="%Y%m%d", errors="coerce")

# ========================================
# (3) 데이터 전처리 (최근 5영업일)
# ========================================
# ----- 금리 -----
_ir = df_ir.copy()
_ir.index = _parse_index_to_datetime(_ir.index)

rate_cols = ["CD(91일)", "CP(91일)", "국고채(3년)", "국고채(5년)"]
missing_rate = [c for c in rate_cols if c not in _ir.columns]
if missing_rate:
    st.error(f"df_ir에 필요한 컬럼이 없습니다: {missing_rate}")
    st.stop()

_ir = _ir[rate_cols].sort_index().tail(5)
for c in rate_cols:
    _ir[c] = pd.to_numeric(
        _ir[c].astype(str).str.replace(",", "", regex=False).str.replace("%", "", regex=False),
        errors="coerce"
    )
df_rates = (
    _ir.reset_index()
       .rename(columns={"index": "날짜"})
       .sort_values("날짜")
)
# 표용(YYYY-MM-DD), 그래프용(MM-DD) 라벨 분리
df_rates["날짜_tbl"] = df_rates["날짜"].dt.strftime("%Y-%m-%d")
df_rates["날짜_str"] = df_rates["날짜"].dt.strftime("%m-%d")  # ✅ 그래프는 월-일만

# ----- 환율 -----
_fx = df_fx.copy()
_fx.index = _parse_index_to_datetime(_fx.index)

fx_rename = {
    "원/미국달러(매매기준율)": "USD/KRW",
    "원/위안(매매기준율)": "CNY/KRW",
    "원/일본엔(100엔)": "JPY(100)/KRW",
    "원/유로": "EUR/KRW",
}
_fx.columns = [str(c).strip() for c in _fx.columns]
_fx = _fx.rename(columns=fx_rename)

fx_cols = ["USD/KRW", "CNY/KRW", "JPY(100)/KRW", "EUR/KRW"]
missing_fx = [c for c in fx_cols if c not in _fx.columns]
if missing_fx:
    st.error(f"df_fx에 필요한 컬럼이 없습니다: {missing_fx}")
    st.stop()

_fx = _fx[fx_cols].sort_index().tail(5)
for c in fx_cols:
    _fx[c] = pd.to_numeric(_fx[c].astype(str).str.replace(",", "", regex=False), errors="coerce")
df_fx = (
    _fx.reset_index()
       .rename(columns={"index": "날짜"})
       .sort_values("날짜")
)
df_fx["날짜_tbl"] = df_fx["날짜"].dt.strftime("%Y-%m-%d")
df_fx["날짜_str"] = df_fx["날짜"].dt.strftime("%m-%d")       # ✅ 그래프는 월-일만

# ---------- 전일 대비 계산 ----------
def add_delta(df: pd.DataFrame, col: str) -> str:
    s = pd.to_numeric(df[col], errors="coerce")
    if len(s) < 2 or pd.isna(s.iloc[-1]) or pd.isna(s.iloc[-2]):
        return "— 0.00"
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

# ========================================
# (4) 화면 헤더
# ========================================
left, mid, right = st.columns([3, 1.4, 1.2])
with left:
    st.title(f"Daily({today_str}) 금융시장 동향")
    st.caption("최근 5영업일 기준 금리/환율 추이")
with mid:
    st.write(""); st.write("")
    st.markdown(f"**업데이트:** {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}")
with right:
    st.write(""); st.write("")
    if st.button("🔄 새로고침"):
        st.experimental_rerun()

st.markdown("---")

# ========================================
# (5) 그래프 (KPI + 금리/환율 2×2 그래프)
# ========================================
col_l, col_r = st.columns([1.2, 1.0])

def line_fig(df, col, ytitle, x_col="날짜_str"):
    """x축은 카테고리(MM-DD)로 고정."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df[x_col], y=df[col], mode="lines+markers", name=col))
    fig.update_layout(
        margin=dict(l=0, r=0, t=28, b=0),
        height=280,
        title=col,
        xaxis_title="", yaxis_title=ytitle,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(type="category")  # ✅ 표의 라벨과 동일한 순서/표기 유지
    )
    if "(%)" in ytitle:   # 금리 그래프만 범위 고정 (원하면 조정)
        fig.update_yaxes(range=[2.0, 3.0])
    return fig

with col_l:
    # ===== 금리 섹션 =====
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>금리 (최근 5영업일)</div>", unsafe_allow_html=True)

    k1, k2, k3, k4 = st.columns(4)
    for (label, (val, d)), slot in zip(kpi_rate.items(), [k1, k2, k3, k4]):
        with slot:
            st.metric(label, f"{val:,.3f}%", d)

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(line_fig(df_rates, "CD(91일)", "(%)"),
                        use_container_width=True, config={"displayModeBar": False})
    with c2:
        st.plotly_chart(line_fig(df_rates, "CP(91일)", "(%)"),
                        use_container_width=True, config={"displayModeBar": False})
    c3, c4 = st.columns(2)
    with c3:
        st.plotly_chart(line_fig(df_rates, "국고채(3년)", "(%)"),
                        use_container_width=True, config={"displayModeBar": False})
    with c4:
        st.plotly_chart(line_fig(df_rates, "국고채(5년)", "(%)"),
                        use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

    # ===== 환율 섹션 =====
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>환율 (최근 5영업일)</div>", unsafe_allow_html=True)

    k1, k2, k3, k4 = st.columns(4)
    for (label, (val, d)), slot in zip(kpi_fx.items(), [k1, k2, k3, k4]):
        with slot:
            st.metric(label, f"{val:,.2f}", d)

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(line_fig(df_fx, "USD/KRW", "(KRW)"),
                        use_container_width=True, config={"displayModeBar": False})
    with c2:
        st.plotly_chart(line_fig(df_fx, "CNY/KRW", "(KRW)"),
                        use_container_width=True, config={"displayModeBar": False})
    c3, c4 = st.columns(2)
    with c3:
        st.plotly_chart(line_fig(df_fx, "JPY(100)/KRW", "(KRW)"),
                        use_container_width=True, config={"displayModeBar": False})
    with c4:
        st.plotly_chart(line_fig(df_fx, "EUR/KRW", "(KRW)"),
                        use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

# ========================================
# (6) 오른쪽 카드 (LLM 전망)
# ========================================
with col_r:
    st.subheader("일일 환율 전망 by LLM")
    outlooks: List[Dict] = [
        {"기관": "KB국민은행", "기간": "일일 전망보고서", "내용": result_KB},
        {"기관": "하나은행", "기간": "일일 전망보고서", "내용": result_HANA},
        {"기관": "키움은행", "기간": "일일 전망보고서", "내용": "T.B.D"},
    ]

    for o in outlooks:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown(
            f"**{o['기관']}** <span class='badge'>{o['기간']}</span>",
            unsafe_allow_html=True,
        )

        # ✅ Markdown 완전 차단: st.text 사용 (헤더/리스트 전혀 파싱 안 됨)
        st.text(o["내용"])

        st.markdown("</div>", unsafe_allow_html=True)


# ========================================
# (7) 하단: 원시데이터 표
# ========================================
with st.expander("📄 원시 데이터 보기", expanded=False):
    st.write("금리")
    st.dataframe(
        df_rates[["날짜_tbl", *rate_cols]].rename(columns={"날짜_tbl": "날짜"}),
        hide_index=True, use_container_width=True
    )
    st.write("환율")
    st.dataframe(
        df_fx[["날짜_tbl", *fx_cols]].rename(columns={"날짜_tbl": "날짜"}),
        hide_index=True, use_container_width=True
    )
# ========================= end of file =========================

# =========================== main.py ===========================

import datetime as dt
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from typing import List, Dict

#
# # ========================================
# # (1) Streamlit 페이지 기본 설정
# # ========================================
# st.set_page_config(
#     page_title="Daily(" + today_str + ") 금융시장 동향",
#     page_icon="📈",
#     layout="wide",
# )
#
# # 간단한 CSS
# st.markdown(
#     """
#     <style>
#       .card { background:#fff; border:1px solid #e9ecef; border-radius:14px;
#               padding:16px 18px; margin-bottom:14px; box-shadow:0 1px 2px rgba(0,0,0,0.04); }
#       .section-title { font-weight:700; font-size:18px; margin-bottom:8px; }
#       .muted { color:#868e96; }
#       .badge { display:inline-block; padding:2px 8px; font-size:12px; border-radius:999px;
#                background:#e7f5ff; color:#1971c2; margin-left:6px; }
#     </style>
#     """,
#     unsafe_allow_html=True,
# )
#
# # ========================================
# # (2) 데이터 전처리 (최근 5영업일)
# # ========================================
# # 금리
# _ir = df_ir.copy()
# _ir.index = pd.to_datetime(_ir.index.astype(str), format="%Y%m%d", errors="coerce")
#
# rate_cols = ["CD(91일)", "CP(91일)", "국고채(3년)", "국고채(5년)"]
# missing_rate = [c for c in rate_cols if c not in _ir.columns]
# if missing_rate:
#     st.error(f"df_ir에 필요한 컬럼이 없습니다: {missing_rate}")
#     st.stop()
#
# _ir = _ir[rate_cols].sort_index().tail(5)
# for c in rate_cols:
#     _ir[c] = pd.to_numeric(
#         _ir[c].astype(str).str.replace(",", "", regex=False).str.replace("%", "", regex=False),
#         errors="coerce"
#     )
# df_rates = _ir.reset_index().rename(columns={"index": "날짜"}).sort_values("날짜")
#
# # 환율
# _fx = df_fx.copy()
# _fx.index = pd.to_datetime(_fx.index.astype(str), format="%Y%m%d", errors="coerce")
# fx_rename = {
#     "원/미국달러(매매기준율)": "USD/KRW",
#     "원/위안(매매기준율)": "CNY/KRW",
#     "원/일본엔(100엔)": "JPY(100)/KRW",
#     "원/유로": "EUR/KRW",
# }
# _fx.columns = [str(c).strip() for c in _fx.columns]
# _fx = _fx.rename(columns=fx_rename)
#
# fx_cols = ["USD/KRW", "CNY/KRW", "JPY(100)/KRW", "EUR/KRW"]
# missing_fx = [c for c in fx_cols if c not in _fx.columns]
# if missing_fx:
#     st.error(f"df_fx에 필요한 컬럼이 없습니다: {missing_fx}")
#     st.stop()
#
# _fx = _fx[fx_cols].sort_index().tail(5)
# for c in fx_cols:
#     _fx[c] = pd.to_numeric(_fx[c].astype(str).str.replace(",", "", regex=False), errors="coerce")
# df_fx = _fx.reset_index().rename(columns={"index": "날짜"}).sort_values("날짜")
#
# # ---------- 전일 대비 계산 ----------
# def add_delta(df: pd.DataFrame, col: str) -> str:
#     s = pd.to_numeric(df[col], errors="coerce")
#     if len(s) < 2 or pd.isna(s.iloc[-1]) or pd.isna(s.iloc[-2]):
#         return "— 0.00"
#     delta = s.iloc[-1] - s.iloc[-2]
#     arrow = "▲" if delta > 0 else ("▼" if delta < 0 else "—")
#     return f"{arrow} {abs(delta):,.2f}"
#
# kpi_rate = {
#     "CD(91일)": (df_rates["CD(91일)"].iloc[-1], add_delta(df_rates, "CD(91일)")),
#     "CP(91일)": (df_rates["CP(91일)"].iloc[-1], add_delta(df_rates, "CP(91일)")),
#     "국고채(3년)": (df_rates["국고채(3년)"].iloc[-1], add_delta(df_rates, "국고채(3년)")),
#     "국고채(5년)": (df_rates["국고채(5년)"].iloc[-1], add_delta(df_rates, "국고채(5년)")),
# }
# kpi_fx = {
#     "USD/KRW": (df_fx["USD/KRW"].iloc[-1], add_delta(df_fx, "USD/KRW")),
#     "CNY/KRW": (df_fx["CNY/KRW"].iloc[-1], add_delta(df_fx, "CNY/KRW")),
#     "JPY(100)/KRW": (df_fx["JPY(100)/KRW"].iloc[-1], add_delta(df_fx, "JPY(100)/KRW")),
#     "EUR/KRW": (df_fx["EUR/KRW"].iloc[-1], add_delta(df_fx, "EUR/KRW")),
# }
#
# # ========================================
# # (3) 화면 헤더
# # ========================================
# left, mid, right = st.columns([3, 1.4, 1.2])
# with left:
#     st.title("Daily(" + today_str + ") 금융시장 동향")
#     st.caption("최근 5영업일 기준 금리/환율")
# with mid:
#     st.write("")
#     st.write("")
#     st.markdown(f"**업데이트:** {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}")
# with right:
#     st.write("")
#     st.write("")
#     if st.button("🔄 새로고침"):
#         st.experimental_rerun()
#
# st.markdown("---")
#
# # ========================================
# # (4) 그래프 (KPI 유지 + 금리/환율 2×2 그래프)
# # ========================================
# col_l, col_r = st.columns([1.2, 1.0])
#
# def line_fig(df, col, ytitle):
#     fig = go.Figure()
#     fig.add_trace(go.Scatter(x=df["날짜"], y=df[col], mode="lines+markers", name=col))
#     fig.update_layout(
#         margin=dict(l=0, r=0, t=28, b=0),
#         height=280,
#         title=col,
#         xaxis_title="", yaxis_title=ytitle,
#         legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
#     )
#     fig.update_xaxes(tickformat="%Y-%m-%d", hoverformat="%Y-%m-%d", dtick="D1")
#
#     # 👉 금리 데이터인 경우에만 y축 고정
#     if "(%)" in ytitle:   # 금리 그래프
#         fig.update_yaxes(range=[2.0, 3.0])   # 2% ~ 3%
#     return fig
#
# with col_l:
#     # ===== 금리 섹션 (KPI 유지 + 2×2 그래프) =====
#     st.markdown("<div class='card'>", unsafe_allow_html=True)
#     st.markdown("<div class='section-title'>금리 (최근 5영업일)</div>", unsafe_allow_html=True)
#
#     k1, k2, k3, k4 = st.columns(4)
#     for (label, (val, d)), slot in zip(kpi_rate.items(), [k1, k2, k3, k4]):
#         with slot:
#             st.metric(label, f"{val:,.3f}%", d)
#
#     c1, c2 = st.columns(2)
#     with c1:
#         st.plotly_chart(line_fig(df_rates, "CD(91일)", "(%)"),
#                         use_container_width=True, config={"displayModeBar": False})
#     with c2:
#         st.plotly_chart(line_fig(df_rates, "CP(91일)", "(%)"),
#                         use_container_width=True, config={"displayModeBar": False})
#     c3, c4 = st.columns(2)
#     with c3:
#         st.plotly_chart(line_fig(df_rates, "국고채(3년)", "(%)"),
#                         use_container_width=True, config={"displayModeBar": False})
#     with c4:
#         st.plotly_chart(line_fig(df_rates, "국고채(5년)", "(%)"),
#                         use_container_width=True, config={"displayModeBar": False})
#     st.markdown("</div>", unsafe_allow_html=True)
#
#     # ===== 환율 섹션 (KPI 유지 + 2×2 그래프) =====
#     st.markdown("<div class='card'>", unsafe_allow_html=True)
#     st.markdown("<div class='section-title'>환율 (최근 5영업일)</div>", unsafe_allow_html=True)
#
#     k1, k2, k3, k4 = st.columns(4)
#     for (label, (val, d)), slot in zip(kpi_fx.items(), [k1, k2, k3, k4]):
#         with slot:
#             st.metric(label, f"{val:,.2f}", d)
#
#     c1, c2 = st.columns(2)
#     with c1:
#         st.plotly_chart(line_fig(df_fx, "USD/KRW", "(KRW)"),
#                         use_container_width=True, config={"displayModeBar": False})
#     with c2:
#         st.plotly_chart(line_fig(df_fx, "CNY/KRW", "(KRW)"),
#                         use_container_width=True, config={"displayModeBar": False})
#     c3, c4 = st.columns(2)
#     with c3:
#         st.plotly_chart(line_fig(df_fx, "JPY(100)/KRW", "(KRW)"),
#                         use_container_width=True, config={"displayModeBar": False})
#     with c4:
#         st.plotly_chart(line_fig(df_fx, "EUR/KRW", "(KRW)"),
#                         use_container_width=True, config={"displayModeBar": False})
#     st.markdown("</div>", unsafe_allow_html=True)
#
# # # ========================================
# # # (5) 오른쪽 카드 (임의 전망)
# # # ========================================
# # with col_r:
# #     st.subheader("일일 환율 전망 by LLM")
# #     outlooks: List[Dict] = [
# #         {"기관": "KB국민은행", "기간": "일일 전망보고서", "내용": result_KB},
# #         {"기관": "하나은행", "기간": "일일 전망보고서", "내용": result_HANA},
# #         {"기관": "키움은행", "기간": "일일 전망보고서", "내용": "T.B.D"},
# #         ]
# #
# #     for o in outlooks:
# #         st.markdown("<div class='card'>", unsafe_allow_html=True)
# #         st.markdown(f"**{o['기관']}** <span class='badge'>{o['기간']}</span>", unsafe_allow_html=True)
# #         st.markdown(f"<div class='muted' style='margin-top:6px'>{o['내용']}</div>", unsafe_allow_html=True)
# #         st.markdown("</div>", unsafe_allow_html=True)
#
# # ========================================
# # (5) 오른쪽 카드 (임의 전망)
# # ========================================
# with col_r:
#     st.subheader("일일 환율 전망 by LLM")
#     outlooks: List[Dict] = [
#         {"기관": "KB국민은행", "기간": "일일 전망보고서", "내용": result_KB},
#         {"기관": "하나은행", "기간": "일일 전망보고서", "내용": result_HANA},
#         {"기관": "키움은행", "기간": "일일 전망보고서", "내용": "T.B.D"},
#     ]
#
#     for o in outlooks:
#         st.markdown("<div class='card'>", unsafe_allow_html=True)
#         st.markdown(f"**{o['기관']}** <span class='badge'>{o['기간']}</span>", unsafe_allow_html=True)
#
#         # ✅ 여기서 Markdown 대신 <pre> 태그로 감쌈
#         st.markdown(
#             f"<div class='muted' style='margin-top:6px'><pre>{o['내용']}</pre></div>",
#             unsafe_allow_html=True,
#         )
#
#         st.markdown("</div>", unsafe_allow_html=True)
#
#
# # ========================================
# # (6) 하단: 원시데이터 표
# # ========================================
# with st.expander("📄 원시 데이터 보기", expanded=False):
#     st.write("금리")
#     st.dataframe(df_rates.assign(날짜=df_rates["날짜"].dt.strftime("%Y-%m-%d")),
#                  hide_index=True, use_container_width=True)
#     st.write("환율")
#     st.dataframe(df_fx.assign(날짜=df_fx["날짜"].dt.strftime("%Y-%m-%d")),
#                  hide_index=True, use_container_width=True)
# # ========================= end of file =============================
#
#
#
#
