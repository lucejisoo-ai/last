import streamlit as st
import pandas as pd
import dart_fss as dart
import requests
import json
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ── 페이지 설정 ───────────────────────────────────────────────────────────────
st.set_page_config(layout="wide", page_title="김지수의 주식 연구소", page_icon="📈")

# ── DART API 설정 ─────────────────────────────────────────────────────────────
DART_API_KEY = "e7901f254435f298ea758cba82c3d814c19b4176"
dart.set_api_key(api_key=DART_API_KEY)

# ── KIS API 설정 ──────────────────────────────────────────────────────────────
try:
    KIS_KEY    = st.secrets["KIS_APP_KEY"]
    KIS_SECRET = st.secrets["KIS_APP_SECRET"]
    BASE_URL   = "https://openapivts.koreainvestment.com:29443"
except Exception:
    st.error("API 키 설정이 없습니다. Streamlit Secrets에 KIS_APP_KEY / KIS_APP_SECRET을 추가하세요.")
    st.stop()

# ── 전역 스타일 ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background:#0d1117; }
[data-testid="stSidebar"]          { background:#161b22; border-right:1px solid #30363d; }
section.main > div                 { padding-top:1.5rem; }
.page-header {
    display:flex; align-items:baseline; gap:12px;
    border-bottom:1px solid #21262d; padding-bottom:16px; margin-bottom:24px;
}
.page-header h1  { color:#e6edf3; font-size:1.6rem; font-weight:700; margin:0; }
.page-header .sub{ color:#8b949e; font-size:0.85rem; }
.sec-title {
    color:#c9d1d9; font-size:0.78rem; font-weight:600;
    letter-spacing:.12em; text-transform:uppercase;
    margin:0 0 12px; padding-bottom:6px; border-bottom:1px solid #21262d;
}
.kpi-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin-bottom:20px; }
.kpi-card {
    background:#161b22; border:1px solid #30363d; border-radius:8px; padding:14px 16px;
}
.kpi-card .lbl  { color:#8b949e; font-size:0.72rem; letter-spacing:.06em; text-transform:uppercase; }
.kpi-card .val  { color:#e6edf3; font-size:1.4rem; font-weight:700; margin:4px 0 2px; }
.kpi-card .dlt  { font-size:0.75rem; }
.kpi-card .pos  { color:#3fb950; }
.kpi-card .neg  { color:#f85149; }
.bar-track { background:#21262d; border-radius:4px; height:7px; overflow:hidden; margin-top:8px; }
.bar-pos   { background:#3fb950; height:7px; border-radius:4px; }
.bar-neg   { background:#f85149; height:7px; border-radius:4px; }
hr         { border-color:#21262d !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# KIS 유틸
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def get_kis_token():
    url  = f"{BASE_URL}/oauth2/tokenP"
    body = {"grant_type":"client_credentials","appkey":KIS_KEY,"appsecret":KIS_SECRET}
    res  = requests.post(url, data=json.dumps(body),
                         headers={"Content-Type":"application/json"}, timeout=10)
    return res.json()["access_token"]

def kis_headers(tr_id):
    # [수정포인트] appkey, appsecret 소문자 적용 및 custtype (개인=P) 추가
    return {
        "authorization": f"Bearer {get_kis_token()}",
        "appkey":    KIS_KEY,
        "appsecret": KIS_SECRET,
        "custtype":  "P",
        "tr_id":     tr_id,
        "Content-Type": "application/json",
    }

# ─────────────────────────────────────────────────────────────────────────────
# 현재가 (휴일이면 직전 영업일 종가 fallback)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def get_kis_price(ticker):
    """returns (price:int, label:str)"""
    # ① 실시간 현재가
    try:
        # [수정포인트] KIS API 요청 파라미터 Key를 모두 대문자로 변경
        params = {"FID_COND_MRKT_DIV_CODE":"J", "FID_INPUT_ISCD":ticker}
        res    = requests.get(
            f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price",
            headers=kis_headers("FHKST01010100"), params=params, timeout=5)
        out   = res.json().get("output", {})
        price = int(out.get("stck_prpr", 0) or 0)
        if price > 0:
            return price, "실시간"
    except Exception:
        pass

    # ② 직전 영업일 종가 fallback
    try:
        today    = datetime.today()
        end_dt   = today.strftime("%Y%m%d")
        start_dt = (today - timedelta(days=14)).strftime("%Y%m%d")
        # [수정포인트] KIS API 요청 파라미터 Key를 모두 대문자로 변경
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD":         ticker,
            "FID_INPUT_DATE_1":       start_dt,
            "FID_INPUT_DATE_2":       end_dt,
            "FID_PERIOD_DIV_CODE":    "D",
            "FID_ORG_ADJ_PRC":        "0",
        }
        res  = requests.get(
            f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-daily-price",
            headers=kis_headers("FHKST01010400"), params=params, timeout=5)
        rows = res.json().get("output", [])
        for row in rows:
            close = int(row.get("stck_clpr", 0) or 0)
            date  = row.get("stck_bsop_date", "")
            if close > 0 and date:
                return close, f"{date[:4]}-{date[4:6]}-{date[6:]} 종가"
    except Exception:
        pass

    return 0, "조회 실패"

# ─────────────────────────────────────────────────────────────────────────────
# 주간 수급 — KRX 정보데이터시스템 (공개, 인증 불필요)
# ─────────────────────────────────────────────────────────────────────────────
KRX_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer":    "http://data.krx.co.kr/",
}

def _prev_weekdays(n=5):
    """오늘 포함 최근 n 영업일(토·일 제외) 날짜 리스트 반환 (최신순)"""
    days, cur = [], datetime.today()
    while len(days) < n:
        if cur.weekday() < 5:
            days.append(cur)
        cur -= timedelta(days=1)
    return days  # 최신 → 과거 순

@st.cache_data(ttl=600)
def get_krx_investor_flow(market):
    """
    KRX 투자자별 거래실적 (일별)
    market: 'STK'=코스피, 'KSQ'=코스닥
    """
    url  = "http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"
    rows = []

    for dt in _prev_weekdays(5):
        trd_dd = dt.strftime("%Y%m%d")
        data   = {
            "bld":        "dbms/MDC/STAT/standard/MDCSTAT02303",
            "locale":     "ko_KR",
            "trdDd":      trd_dd,
            "market":     market,
            "invstTpCd":  "4",   # 전체
            "askBid":     "01",  # 순매수
            "share":      "1",
            "money":      "1",   # 억 원
            "csvxls_isNo":"false",
        }
        try:
            res  = requests.post(url, data=data, headers=KRX_HEADERS, timeout=8)
            body = res.json()
            arr  = body.get("output", [])
            if not arr:
                continue

            parsed = {"날짜": dt.strftime("%m/%d"), "외국인": 0, "기관": 0, "개인": 0}
            for item in arr:
                nm  = (item.get("INVST_TP_NM") or item.get("invstTpNm") or "").strip()
                val_raw = (item.get("NETBUY_TRDVAL") or item.get("netbuyTrdval") or "0")
                try:
                    val = int(str(val_raw).replace(",", "").replace(" ", "") or "0")
                except ValueError:
                    val = 0
                if "외국인" in nm:
                    parsed["외국인"] = val
                elif "기관" in nm:
                    parsed["기관"] = val
                elif "개인" in nm:
                    parsed["개인"] = val
            rows.append(parsed)
        except Exception:
            continue

    if rows:
        return pd.DataFrame(rows[::-1])
    return pd.DataFrame(columns=["날짜","외국인","기관","개인"])

# ─────────────────────────────────────────────────────────────────────────────
# 수급 차트
# ─────────────────────────────────────────────────────────────────────────────
COLORS = {"외국인":"#58a6ff","기관":"#f0883e","개인":"#3fb950"}
LAYOUT = dict(
    plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
    font=dict(color="#8b949e", size=11),
    legend=dict(bgcolor="#161b22", bordercolor="#30363d", borderwidth=1,
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    xaxis=dict(gridcolor="#21262d", linecolor="#30363d"),
    yaxis=dict(gridcolor="#21262d", linecolor="#30363d", tickformat=","),
    margin=dict(l=8,r=8,t=44,b=8), height=265,
)

def bar_chart(df, title):
    fig = go.Figure()
    for col in ["외국인","기관","개인"]:
        if col in df.columns:
            fig.add_trace(go.Bar(name=col, x=df["날짜"], y=df[col],
                                 marker_color=COLORS[col], opacity=0.85))
    fig.update_layout(barmode="group",
                      title=dict(text=title, font=dict(color="#c9d1d9",size=13), x=0),
                      **LAYOUT)
    return fig

def line_chart(df, title):
    fig = go.Figure()
    for col in ["외국인","기관","개인"]:
        if col in df.columns:
            fig.add_trace(go.Scatter(name=col, x=df["날짜"], y=df[col].cumsum(),
                                     mode="lines+markers",
                                     line=dict(color=COLORS[col],width=2),
                                     marker=dict(size=5)))
    fig.update_layout(title=dict(text=title, font=dict(color="#c9d1d9",size=13), x=0),
                      **LAYOUT)
    return fig

def kpi_html(df):
    if df.empty:
        return "<p style='color:#8b949e;font-size:0.8rem'>데이터를 불러오지 못했습니다.</p>"
    totals  = {c: int(df[c].sum()) for c in ["외국인","기관","개인"] if c in df.columns}
    max_abs = max((abs(v) for v in totals.values()), default=1) or 1
    icons   = {"외국인":"🌐","기관":"🏦","개인":"🧑‍💼"}
    cards   = ""
    for k, v in totals.items():
        pct  = abs(v)/max_abs*100
        cls  = "pos" if v>=0 else "neg"
        sign = "▲" if v>=0 else "▼"
        bar  = "bar-pos" if v>=0 else "bar-neg"
        cards += f"""
        <div class="kpi-card">
          <div class="lbl">{icons[k]} {k}</div>
          <div class="val">{v:+,}</div>
          <div class="dlt {cls}">{sign} 주간 누적 (억원)</div>
          <div class="bar-track"><div class="{bar}" style="width:{pct:.1f}%"></div></div>
        </div>"""
    return f'<div class="kpi-grid">{cards}</div>'

# ─────────────────────────────────────────────────────────────────────────────
# DART 기업 목록 (캐시)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource
def load_corp_list():
    return dart.get_corp_list()

corp_list = load_corp_list()
all_corps = {c.corp_name: c.corp_code for c in corp_list}

# ─────────────────────────────────────────────────────────────────────────────
# 종목 분석 — EPS 3단계 fallback + 연도 자동 후퇴
# ─────────────────────────────────────────────────────────────────────────────
def _extract_fs_safe(corp):
    """2025 → 2024 → 2023 순으로 연간 재무제표 시도"""
    for year in [2025, 2024, 2023]:
        try:
            fs_list = corp.extract_fs(bgn_de=f"{year}0101")
            if fs_list and len(fs_list) > 0:
                fs = fs_list[0]
                if fs is not None and not fs.empty:
                    return fs, year
        except Exception:
            continue
    return None, None

@st.cache_data(ttl=3600, show_spinner=False)
def get_analysis_data(name):
    err = {"종목":name,"현재가":"에러","기준일":"-","PER":"-","그레이엄":"-","DCF":"-","fs_year":"-"}
    try:
        results = corp_list.find_by_corp_name(name)
        if not results:
            return {**err, "PER":"기업 없음"}
        corp = results[0]

        # ── 재무제표 ──────────────────────────────────────────────────────────
        fs, fs_year = _extract_fs_safe(corp)
        if fs is None:
            return {**err, "PER":"재무제표 없음"}

        # 당기순이익
        net_income = None
        for lbl in ["당기순이익(손실)","당기순이익","분기순이익(손실)","분기순이익"]:
            if lbl in fs.index:
                try:
                    net_income = float(str(fs.loc[lbl].iloc[0]).replace(",",""))
                    break
                except Exception:
                    continue
        if net_income is None:
            return {**err, "PER":"순이익 없음"}

        # ── EPS 결정 ──────────────────────────────────────────────────────────
        eps = None

        # A. 재무제표 주당순이익 직접 참조
        for lbl in ["주당순이익(기본)","기본주당순이익(손실)","기본주당순이익",
                    "기본주당이익(손실)","기본주당이익"]:
            if lbl in fs.index:
                try:
                    v = float(str(fs.loc[lbl].iloc[0]).replace(",",""))
                    if v != 0:
                        eps = v
                        break
                except Exception:
                    continue

        # B. 발행주식수로 직접 계산
        if eps is None:
            for lbl in ["보통주발행주식수","발행주식수","유통보통주식수","보통주식수"]:
                if lbl in fs.index:
                    try:
                        shares = float(str(fs.loc[lbl].iloc[0]).replace(",",""))
                        if shares > 0:
                            eps = net_income / shares
                            break
                    except Exception:
                        continue

        # C. KIS inquire-price 의 eps 필드
        # [수정포인트] corp.ticker -> corp.stock_code 로 변경 & 파라미터 Key 대문자 변경
        if eps is None and corp.stock_code:
            try:
                params = {"FID_COND_MRKT_DIV_CODE":"J", "FID_INPUT_ISCD":corp.stock_code}
                res    = requests.get(
                    f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price",
                    headers=kis_headers("FHKST01010100"), params=params, timeout=5)
                out     = res.json().get("output",{})
                eps_str = str(out.get("eps","0")).replace(",","")
                if eps_str and eps_str not in ("0",""):
                    eps = float(eps_str)
            except Exception:
                pass

        # ── 현재가 ────────────────────────────────────────────────────────────
        current_price, price_label = (0,"종목코드 없음")
        # [수정포인트] corp.ticker -> corp.stock_code 로 변경
        if corp.stock_code:
            current_price, price_label = get_kis_price(corp.stock_code)

        # ── PER / 밸류에이션 ──────────────────────────────────────────────────
        per = graham = dcf = None
        if eps and eps != 0 and current_price > 0:
            per    = round(current_price / eps, 2)
            graham = round(eps * 22.5)
            dcf    = round(eps * 15)

        return {
            "종목":    name,
            "현재가":  f"₩{current_price:,}" if current_price else "조회 실패",
            "기준일":  price_label,
            "PER":     f"{per:.1f}x" if per else "산출 불가",
            "그레이엄": f"₩{graham:,}" if graham else "-",
            "DCF":     f"₩{dcf:,}"   if dcf    else "-",
            "fs_year": str(fs_year),
        }
    except Exception as e:
        return {**err, "PER": f"에러: {e}"}

# ─────────────────────────────────────────────────────────────────────────────
# 사이드바
# ─────────────────────────────────────────────────────────────────────────────
if "watch_list" not in st.session_state:
    st.session_state.watch_list = []

with st.sidebar:
    st.markdown('<p class="sec-title">📌 관심 종목</p>', unsafe_allow_html=True)
    search = st.selectbox("종목 검색", [""] + sorted(all_corps.keys()),
                          label_visibility="collapsed")
    if st.button("➕ 추가", use_container_width=True) and search:
        if len(st.session_state.watch_list) >= 10:
            st.warning("최대 10개까지 추가 가능합니다.")
        elif search not in st.session_state.watch_list:
            st.session_state.watch_list.append(search)
            st.rerun()

    st.markdown("---")
    st.markdown('<p class="sec-title">📋 목록</p>', unsafe_allow_html=True)
    if not st.session_state.watch_list:
        st.markdown('<p style="color:#8b949e;font-size:0.8rem">아직 추가된 종목이 없습니다.</p>',
                    unsafe_allow_html=True)
    for i, nm in enumerate(st.session_state.watch_list):
        c1, c2 = st.columns([0.8, 0.2])
        c1.markdown(f'<div style="color:#58a6ff;font-size:0.85rem;padding-top:6px">{nm}</div>',
                    unsafe_allow_html=True)
        if c2.button("✕", key=f"sb_{i}"):
            st.session_state.watch_list.pop(i)
            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
  <h1>📈 김지수의 주식 연구소</h1>
  <span class="sub">실시간 시세 · 수급 동향 · 밸류에이션</span>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# 섹션 A — 주간 수급 대시보드
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<p class="sec-title">📊 주간 투자자 수급 동향</p>', unsafe_allow_html=True)

tab_kp, tab_kq = st.tabs(["🔵 코스피 (KOSPI)", "🟠 코스닥 (KOSDAQ)"])

for tab, market, mname in [(tab_kp,"STK","코스피"),(tab_kq,"KSQ","코스닥")]:
    with tab:
        with st.spinner(f"{mname} 수급 로딩 중…"):
            df = get_krx_investor_flow(market)

        st.markdown(kpi_html(df), unsafe_allow_html=True)

        if not df.empty:
            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(bar_chart(df, f"{mname} 일별 순매수 (억원)"),
                                use_container_width=True, key=f"bar_{market}")
            with c2:
                st.plotly_chart(line_chart(df, f"{mname} 누적 순매수 (억원)"),
                                use_container_width=True, key=f"cum_{market}")
            with st.expander("📋 원본 데이터"):
                fmt = {c: "{:,}" for c in ["외국인","기관","개인"] if c in df.columns}
                st.dataframe(
                    df.set_index("날짜").style.format(fmt).map(
                        lambda v: "color:#3fb950" if v>0 else ("color:#f85149" if v<0 else ""),
                        subset=[c for c in ["외국인","기관","개인"] if c in df.columns]
                    ),
                    use_container_width=True
                )
        else:
            st.warning("KRX에서 수급 데이터를 가져오지 못했습니다. 잠시 후 다시 시도하세요.")

st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# 섹션 B — 관심 종목 분석
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<p class="sec-title">🔍 관심 종목 분석</p>', unsafe_allow_html=True)

if not st.session_state.watch_list:
    st.markdown("""
    <div style="background:#161b22;border:1px dashed #30363d;border-radius:8px;
                padding:32px;text-align:center;color:#8b949e;font-size:0.88rem">
        왼쪽 사이드바에서 종목을 검색해 추가하면 밸류에이션 분석이 표시됩니다.
    </div>
    """, unsafe_allow_html=True)
else:
    # 헤더
    hcols = st.columns([2.4, 1.8, 2.0, 1.4, 2.0, 2.0, 1.0])
    for hc, lbl in zip(hcols, ["종목","현재가","기준일","PER","그레이엄","DCF",""]):
        hc.markdown(
            f'<span style="color:#8b949e;font-size:0.73rem;text-transform:uppercase">{lbl}</span>',
            unsafe_allow_html=True)
    st.markdown('<hr style="margin:4px 0 8px">', unsafe_allow_html=True)

    for idx, nm in enumerate(st.session_state.watch_list):
        with st.spinner(f"{nm} 분석 중…"):
            d = get_analysis_data(nm)

        # PER 색상
        per_color = "#c9d1d9"
        raw_per   = str(d["PER"]).replace("x","")
        try:
            pv = float(raw_per)
            per_color = "#3fb950" if pv<15 else ("#f85149" if pv>30 else "#f0883e")
        except Exception:
            pass

        # fs_year 표시 (재무제표 기준연도)
        yr_badge = ""
        if d.get("fs_year","-") not in ("-","None"):
            yr_badge = f' <span style="color:#8b949e;font-size:0.7rem">({d["fs_year"]}년)</span>'

        cols = st.columns([2.4, 1.8, 2.0, 1.4, 2.0, 2.0, 1.0])
        cols[0].markdown(
            f'<span style="color:#58a6ff;font-weight:600">{d["종목"]}</span>{yr_badge}',
            unsafe_allow_html=True)
        cols[1].markdown(
            f'<span style="color:#e6edf3;font-weight:700">{d["현재가"]}</span>',
            unsafe_allow_html=True)
        cols[2].markdown(
            f'<span style="color:#8b949e;font-size:0.77rem">{d["기준일"]}</span>',
            unsafe_allow_html=True)
        cols[3].markdown(
            f'<span style="color:{per_color};font-weight:600">{d["PER"]}</span>',
            unsafe_allow_html=True)
        cols[4].markdown(
            f'<span style="color:#3fb950">{d["그레이엄"]}</span>',
            unsafe_allow_html=True)
        cols[5].markdown(
            f'<span style="color:#f0883e">{d["DCF"]}</span>',
            unsafe_allow_html=True)
        if cols[6].button("삭제", key=f"del_{idx}"):
            st.session_state.watch_list.pop(idx)
            st.rerun()

        st.markdown('<hr style="margin:4px 0">', unsafe_allow_html=True)
