import streamlit as st
import pandas as pd
import dart_fss as dart
import requests
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ── 페이지 설정 ──────────────────────────────────────────────────────────────
st.set_page_config(layout="wide", page_title="김지수의 주식 연구소", page_icon="📈")

# ── DART API 설정 ────────────────────────────────────────────────────────────
DART_API_KEY = "e7901f254435f298ea758cba82c3d814c19b4176"
dart.set_api_key(api_key=DART_API_KEY)

# ── KIS API 설정 ─────────────────────────────────────────────────────────────
try:
    KIS_KEY    = st.secrets["KIS_APP_KEY"]
    KIS_SECRET = st.secrets["KIS_APP_SECRET"]
    BASE_URL   = "https://openapi.koreainvestment.com:9443"
except Exception:
    st.error("API 키 설정이 없습니다. Secrets를 확인하세요.")
    st.stop()

# ── 전역 스타일 ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* 전체 배경 */
[data-testid="stAppViewContainer"] { background: #0d1117; }
[data-testid="stSidebar"]          { background: #161b22; border-right: 1px solid #30363d; }
section.main > div                 { padding-top: 1.5rem; }

/* 헤더 */
.page-header {
    display: flex; align-items: baseline; gap: 12px;
    border-bottom: 1px solid #21262d; padding-bottom: 16px; margin-bottom: 24px;
}
.page-header h1 { color: #e6edf3; font-size: 1.6rem; font-weight: 700; margin: 0; }
.page-header .sub { color: #8b949e; font-size: 0.85rem; }

/* 섹션 타이틀 */
.section-title {
    color: #c9d1d9; font-size: 0.8rem; font-weight: 600;
    letter-spacing: .12em; text-transform: uppercase;
    margin: 0 0 12px 0; padding-bottom: 6px;
    border-bottom: 1px solid #21262d;
}

/* KPI 카드 */
.kpi-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 20px; }
.kpi-card {
    background: #161b22; border: 1px solid #30363d; border-radius: 8px;
    padding: 14px 16px;
}
.kpi-card .label { color: #8b949e; font-size: 0.72rem; letter-spacing: .06em; text-transform: uppercase; }
.kpi-card .value { color: #e6edf3; font-size: 1.45rem; font-weight: 700; margin: 4px 0 2px; }
.kpi-card .delta { font-size: 0.75rem; }
.kpi-card .delta.pos { color: #3fb950; }
.kpi-card .delta.neg { color: #f85149; }

/* 수급 강도 바 */
.flow-bar-wrap { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.flow-bar-label { color: #8b949e; font-size: 0.78rem; width: 48px; }
.flow-bar-track { flex: 1; background: #21262d; border-radius: 4px; height: 8px; overflow: hidden; }
.flow-bar-fill-pos { background: #3fb950; height: 8px; border-radius: 4px; }
.flow-bar-fill-neg { background: #f85149; height: 8px; border-radius: 4px; }
.flow-bar-val { color: #c9d1d9; font-size: 0.78rem; width: 80px; text-align: right; }

/* 종목 카드 */
.stock-card {
    background: #161b22; border: 1px solid #30363d; border-radius: 8px;
    padding: 12px 16px; margin-bottom: 10px;
}
.stock-card .name  { color: #58a6ff; font-size: 0.88rem; font-weight: 600; }
.stock-card .price { color: #e6edf3; font-size: 1.1rem; font-weight: 700; }

/* 구분선 */
hr { border-color: #21262d !important; }

/* Plotly 배경 통일 */
.js-plotly-plot .plotly .bg { fill: transparent !important; }
</style>
""", unsafe_allow_html=True)

# ── KIS 토큰 캐시 ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def get_kis_token():
    url  = f"{BASE_URL}/oauth2/tokenP"
    body = {"grant_type": "client_credentials", "appkey": KIS_KEY, "appsecret": KIS_SECRET}
    res  = requests.post(url, data=json.dumps(body), headers={"Content-Type": "application/json"})
    return res.json()["access_token"]

def kis_headers(tr_id: str) -> dict:
    return {
        "authorization": f"Bearer {get_kis_token()}",
        "appKey":   KIS_KEY,
        "appSecret": KIS_SECRET,
        "tr_id":    tr_id,
        "Content-Type": "application/json",
    }

# ── KIS 현재가 ────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def get_kis_price(ticker: str) -> int:
    params = {"fid_cond_mrkt_div_code": "J", "fid_input_iscd": ticker}
    res = requests.get(
        f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price",
        headers=kis_headers("FHKST01010100"), params=params
    )
    return int(res.json()["output"]["stck_prpr"])

# ── KIS 주간 수급 (시장별) ────────────────────────────────────────────────────
@st.cache_data(ttl=600)
def get_weekly_investor_flow(market_code: str = "J") -> pd.DataFrame:
    """
    FHKST01010900 — 주식 투자자별 매매동향 (일별)
    market_code: J=코스피, Q=코스닥
    최근 5거래일 데이터를 반환합니다.
    """
    today = datetime.today()
    rows  = []

    # 최근 7 캘린더일 안에서 5거래일치 수집
    for delta in range(7):
        date = today - timedelta(days=delta)
        if date.weekday() >= 5:   # 토·일 건너뜀
            continue
        date_str = date.strftime("%Y%m%d")

        params = {
            "fid_cond_mrkt_div_code": market_code,
            "fid_input_date_1": date_str,
            "fid_input_date_2": date_str,
        }
        try:
            res  = requests.get(
                f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-investor",
                headers=kis_headers("FHKST01010900"),
                params=params, timeout=5
            )
            out  = res.json().get("output", [])
            if not out:
                continue
            o = out[0]
            rows.append({
                "날짜":   date.strftime("%m/%d"),
                "외국인": int(o.get("frgn_ntby_qty", 0)),
                "기관":   int(o.get("orgn_ntby_qty", 0)),
                "개인":   int(o.get("indv_ntby_qty", 0)),
            })
            if len(rows) >= 5:
                break
        except Exception:
            continue

    if rows:
        df = pd.DataFrame(rows[::-1])   # 오래된 날짜 → 최근 순
    else:
        # API 실패 시 — 빈 더미로 UI 유지
        df = pd.DataFrame({"날짜": [], "외국인": [], "기관": [], "개인": []})

    return df

# ── 수급 차트 생성 ────────────────────────────────────────────────────────────
def make_flow_chart(df: pd.DataFrame, title: str) -> go.Figure:
    colors = {"외국인": "#58a6ff", "기관": "#f0883e", "개인": "#3fb950"}
    fig = go.Figure()
    for col in ["외국인", "기관", "개인"]:
        if col not in df.columns:
            continue
        fig.add_trace(go.Bar(
            name=col, x=df["날짜"], y=df[col],
            marker_color=colors[col], opacity=0.85,
        ))
    fig.update_layout(
        title=dict(text=title, font=dict(color="#c9d1d9", size=13), x=0),
        barmode="group",
        plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
        font=dict(color="#8b949e", size=11),
        legend=dict(bgcolor="#161b22", bordercolor="#30363d", borderwidth=1,
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(gridcolor="#21262d", linecolor="#30363d"),
        yaxis=dict(gridcolor="#21262d", linecolor="#30363d", tickformat=","),
        margin=dict(l=8, r=8, t=40, b=8),
        height=260,
    )
    return fig

def make_cumulative_chart(df: pd.DataFrame, title: str) -> go.Figure:
    colors = {"외국인": "#58a6ff", "기관": "#f0883e", "개인": "#3fb950"}
    fig = go.Figure()
    for col in ["외국인", "기관", "개인"]:
        if col not in df.columns:
            continue
        fig.add_trace(go.Scatter(
            name=col, x=df["날짜"], y=df[col].cumsum(),
            mode="lines+markers",
            line=dict(color=colors[col], width=2),
            marker=dict(size=5),
        ))
    fig.update_layout(
        title=dict(text=title, font=dict(color="#c9d1d9", size=13), x=0),
        plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
        font=dict(color="#8b949e", size=11),
        legend=dict(bgcolor="#161b22", bordercolor="#30363d", borderwidth=1,
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(gridcolor="#21262d", linecolor="#30363d"),
        yaxis=dict(gridcolor="#21262d", linecolor="#30363d", tickformat=","),
        margin=dict(l=8, r=8, t=40, b=8),
        height=260,
    )
    return fig

# ── 수급 KPI 요약 ─────────────────────────────────────────────────────────────
def flow_kpi_html(df: pd.DataFrame) -> str:
    if df.empty:
        return "<p style='color:#8b949e;font-size:0.8rem'>데이터 없음</p>"
    totals = {col: int(df[col].sum()) for col in ["외국인", "기관", "개인"] if col in df.columns}
    max_abs = max(abs(v) for v in totals.values()) or 1

    cards = ""
    icon  = {"외국인": "🌐", "기관": "🏦", "개인": "🧑‍💼"}
    for k, v in totals.items():
        pct    = abs(v) / max_abs * 100
        cls    = "pos" if v >= 0 else "neg"
        sign   = "▲" if v >= 0 else "▼"
        bar_cl = "flow-bar-fill-pos" if v >= 0 else "flow-bar-fill-neg"
        cards += f"""
        <div class="kpi-card">
            <div class="label">{icon[k]} {k}</div>
            <div class="value">{v:+,}</div>
            <div class="delta {cls}">{sign} 주간 누적</div>
            <div style="margin-top:8px">
                <div class="flow-bar-track"><div class="{bar_cl}" style="width:{pct:.1f}%"></div></div>
            </div>
        </div>"""
    return f'<div class="kpi-grid">{cards}</div>'

# ── DART 분석 ─────────────────────────────────────────────────────────────────
corp_list = dart.get_corp_list()
all_corps = {c.corp_name: c.corp_code for c in corp_list}

def get_analysis_data(name: str) -> dict:
    try:
        corp      = corp_list.find_by_corp_name(name)[0]
        fs        = corp.extract_fs(bgn_de="20250101")[0]
        net_income = fs.loc["당기순이익(손실)"].iloc[0]
        current_price = get_kis_price(corp.ticker)
        eps  = net_income / 100_000_000
        per  = round(current_price / eps, 2) if eps != 0 else 0
        return {
            "종목": name,
            "현재가": f"₩{current_price:,}",
            "PER":   per,
            "그레이엄": f"₩{round(eps * 22.5):,}",
            "DCF":   f"₩{round(eps * 1.5):,}",
        }
    except Exception:
        return {"종목": name, "현재가": "에러", "PER": "-", "그레이엄": "-", "DCF": "-"}

# ── 사이드바 ──────────────────────────────────────────────────────────────────
if "watch_list" not in st.session_state:
    st.session_state.watch_list = []

with st.sidebar:
    st.markdown('<p class="section-title">📌 관심 종목</p>', unsafe_allow_html=True)
    search = st.selectbox("종목 검색", [""] + list(all_corps.keys()), label_visibility="collapsed")
    if st.button("➕ 추가", use_container_width=True) and search:
        if len(st.session_state.watch_list) >= 10:
            st.warning("최대 10개까지 추가 가능합니다.")
        elif search not in st.session_state.watch_list:
            st.session_state.watch_list.append(search)
            st.rerun()

    st.markdown("---")
    st.markdown('<p class="section-title">📋 목록</p>', unsafe_allow_html=True)
    if not st.session_state.watch_list:
        st.markdown('<p style="color:#8b949e;font-size:0.8rem">아직 추가된 종목이 없습니다.</p>',
                    unsafe_allow_html=True)
    for i, name in enumerate(st.session_state.watch_list):
        c1, c2 = st.columns([0.8, 0.2])
        c1.markdown(f'<div style="color:#58a6ff;font-size:0.85rem;padding-top:6px">{name}</div>',
                    unsafe_allow_html=True)
        if c2.button("✕", key=f"sb_del_{i}"):
            st.session_state.watch_list.pop(i)
            st.rerun()

# ── 메인 ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
  <h1>📈 김지수의 주식 연구소</h1>
  <span class="sub">실시간 시세 · 수급 동향 · 밸류에이션</span>
</div>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════
# 섹션 A — 투자자 수급 대시보드
# ════════════════════════════════════════════════════════════════════════════════
st.markdown('<p class="section-title">📊 주간 투자자 수급 동향</p>', unsafe_allow_html=True)

tab_kospi, tab_kosdaq = st.tabs(["🔵 코스피 (KOSPI)", "🟠 코스닥 (KOSDAQ)"])

for tab, mcode, mname in [
    (tab_kospi,  "J", "코스피"),
    (tab_kosdaq, "Q", "코스닥"),
]:
    with tab:
        with st.spinner(f"{mname} 수급 데이터 로딩 중…"):
            df_flow = get_weekly_investor_flow(mcode)

        # KPI 카드
        st.markdown(flow_kpi_html(df_flow), unsafe_allow_html=True)

        if not df_flow.empty:
            col_bar, col_cum = st.columns(2)
            with col_bar:
                st.plotly_chart(
                    make_flow_chart(df_flow, f"{mname} — 일별 순매수 (주)"),
                    use_container_width=True, key=f"bar_{mcode}"
                )
            with col_cum:
                st.plotly_chart(
                    make_cumulative_chart(df_flow, f"{mname} — 누적 순매수 (주)"),
                    use_container_width=True, key=f"cum_{mcode}"
                )

            # 상세 표
            with st.expander("📋 원본 데이터 보기"):
                styled = df_flow.set_index("날짜").style.format("{:,}").applymap(
                    lambda v: "color:#3fb950" if v > 0 else ("color:#f85149" if v < 0 else ""),
                    subset=["외국인", "기관", "개인"]
                )
                st.dataframe(styled, use_container_width=True)
        else:
            st.info("수급 데이터를 불러오지 못했습니다. API 권한 또는 날짜를 확인하세요.")

st.markdown("<br>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════
# 섹션 B — 관심 종목 분석
# ════════════════════════════════════════════════════════════════════════════════
st.markdown('<p class="section-title">🔍 관심 종목 분석</p>', unsafe_allow_html=True)

if not st.session_state.watch_list:
    st.markdown("""
    <div style="background:#161b22;border:1px dashed #30363d;border-radius:8px;
                padding:32px;text-align:center;color:#8b949e;font-size:0.88rem">
        왼쪽 사이드바에서 종목을 검색해 추가하면 밸류에이션 분석이 표시됩니다.
    </div>
    """, unsafe_allow_html=True)
else:
    header_cols = st.columns([3, 2, 1.5, 2, 2, 1])
    for h, label in zip(header_cols, ["종목", "현재가", "PER", "그레이엄 가치", "DCF 가치", ""]):
        h.markdown(f'<span style="color:#8b949e;font-size:0.75rem;text-transform:uppercase">{label}</span>',
                   unsafe_allow_html=True)
    st.markdown('<hr style="margin:4px 0 8px">', unsafe_allow_html=True)

    for idx, name in enumerate(st.session_state.watch_list):
        with st.spinner(f"{name} 분석 중…"):
            data = get_analysis_data(name)

        cols = st.columns([3, 2, 1.5, 2, 2, 1])
        cols[0].markdown(f'<span style="color:#58a6ff;font-weight:600">{data["종목"]}</span>',
                         unsafe_allow_html=True)
        cols[1].markdown(f'<span style="color:#e6edf3;font-weight:700">{data["현재가"]}</span>',
                         unsafe_allow_html=True)
        cols[2].markdown(f'<span style="color:#c9d1d9">{data["PER"]}</span>',
                         unsafe_allow_html=True)
        cols[3].markdown(f'<span style="color:#3fb950">{data["그레이엄"]}</span>',
                         unsafe_allow_html=True)
        cols[4].markdown(f'<span style="color:#f0883e">{data["DCF"]}</span>',
                         unsafe_allow_html=True)
        if cols[5].button("삭제", key=f"del_{idx}"):
            st.session_state.watch_list.pop(idx)
            st.rerun()

        st.markdown('<hr style="margin:4px 0">', unsafe_allow_html=True)
