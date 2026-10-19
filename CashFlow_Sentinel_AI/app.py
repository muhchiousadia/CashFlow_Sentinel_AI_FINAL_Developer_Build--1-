from pathlib import Path
from html import escape
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from src.data_loader import validate_transactions, validate_network
from src.cashflow_engine import forecast_business, summarize_forecast
from src.scenario_engine import apply_payment_delay
from src.action_optimizer import rank_actions
from src.agent import generate_agent_brief
from src.network_risk import propagate_payment_shock
from src.copilot_features import risk_radar, financing_options, counterparty_vulnerability, rule_based_chat, ask_local_ollama
from src.security import require_permission, AuthorizationError, make_audit_record
from src.auth_store import init_db, user_count, create_user, authenticate, write_audit, read_audit
from src.security_policy import authorize
from src.input_quality import transaction_quality_report, network_quality_report, build_scenario_transactions

ROOT=Path(__file__).parent
st.set_page_config(page_title="CashFlow Sentinel AI",page_icon="🛡️",layout="wide")
if "ui_theme" not in st.session_state:
    st.session_state["ui_theme"] = "Light"

def segmented_choice(label, options, key, default):
    if hasattr(st, "segmented_control"):
        return st.segmented_control(label, options, key=key, default=default)
    return st.radio(label, options, key=key, index=options.index(default), horizontal=True)

def set_auth_mode(mode: str) -> None:
    st.session_state["auth_mode"] = mode

_, theme_col = st.columns([6, 2])
with theme_col:
    segmented_choice("Appearance", ["Light", "Dark"], "ui_theme", "Light")

dark_mode = st.session_state["ui_theme"] == "Dark"
palette = {
    "page": "#0b1427" if dark_mode else "#f4f7fd",
    "surface": "#111e34" if dark_mode else "#ffffff",
    "surface_alt": "#172740" if dark_mode else "#f8faff",
    "text": "#e8eefb" if dark_mode else "#101c36",
    "muted": "#a6b3ca" if dark_mode else "#64748b",
    "border": "#293a55" if dark_mode else "#dce5f3",
    "blue": "#5c9bff" if dark_mode else "#2878f0",
    "cyan": "#16c8e8",
    "navy": "#081329",
    "grid": "#293a55" if dark_mode else "#e5ebf4",
}
plot_template = "plotly_dark" if dark_mode else "plotly_white"
plot_background = palette["surface"] if dark_mode else "rgba(0,0,0,0)"
theme_css = f"""
<style>
:root {{
  color-scheme: {"dark" if dark_mode else "light"};
  --navy:{palette["navy"]}; --blue:{palette["blue"]}; --cyan:{palette["cyan"]};
  --ink:{palette["text"]}; --muted:{palette["muted"]}; --surface:{palette["surface"]};
  --surface-alt:{palette["surface_alt"]}; --canvas:{palette["page"]}; --border:{palette["border"]};
  --grid:{palette["grid"]}; --shadow:{"0 12px 30px rgba(0,0,0,.22)" if dark_mode else "0 10px 28px rgba(21,43,82,.07)"};
}}
.stApp {{ background:var(--canvas); color:var(--ink); }}
[data-testid="stHeader"] {{ background:var(--canvas); }}
[data-testid="stMain"] {{ color:var(--ink); }}
[data-testid="stSidebar"] {{ background:linear-gradient(180deg,#081329 0%,#102650 100%); }}
[data-testid="stSidebar"] * {{ color:#edf3ff; }}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] a {{ display:block; padding:.48rem .68rem; margin:.16rem 0; border-radius:9px; color:#dce8ff; text-decoration:none; font-weight:550; }}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] a:hover {{ background:rgba(255,255,255,.11); color:#fff; }}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {{ color:#dce8ff; }}
[data-testid="stWidgetLabel"] p, [data-testid="stMarkdownContainer"] p, [data-testid="stCaptionContainer"] {{ color:var(--muted); }}
h1,h2,h3,h4 {{ color:var(--ink); letter-spacing:-.025em; }}
[data-testid="stMetric"] {{ background:var(--surface); border:1px solid var(--border); border-radius:15px; padding:1rem 1.15rem; box-shadow:var(--shadow); }}
[data-testid="stMetricLabel"] {{ color:var(--muted); }}
[data-testid="stMetricValue"] {{ color:var(--ink); }}
[data-testid="stVerticalBlockBorderWrapper"] {{ border-color:var(--border)!important; border-radius:16px!important; background:var(--surface); }}
[data-testid="stForm"] {{ background:var(--surface); padding:1.35rem 1.45rem; border:1px solid var(--border); border-radius:18px; box-shadow:var(--shadow); }}
[data-testid="stTextInput"] input, [data-testid="stNumberInput"] input, [data-testid="stDateInput"] input,
[data-testid="stSelectbox"] [data-baseweb="select"] > div, [data-testid="stMultiSelect"] [data-baseweb="select"] > div,
[data-testid="stFileUploader"] section {{ background:var(--surface-alt); color:var(--ink); border-color:var(--border); border-radius:10px; }}
[data-testid="stTextInput"] input, [data-testid="stNumberInput"] input {{ caret-color:var(--blue); }}
[data-testid="stTextInput"] input::placeholder, [data-testid="stNumberInput"] input::placeholder {{ color:var(--muted); opacity:.8; }}
[data-baseweb="popover"], [data-baseweb="menu"], [role="listbox"] {{ background:var(--surface)!important; color:var(--ink)!important; border-color:var(--border)!important; }}
[role="option"] {{ color:var(--ink)!important; }}
[data-testid="stDataFrame"], [data-testid="stTable"] {{ border:1px solid var(--border); border-radius:12px; overflow:hidden; }}
[data-testid="stAlert"] {{ border-radius:12px; background:var(--surface-alt); color:var(--ink); border:1px solid var(--border); }}
[data-testid="stAlertContainer"], [data-testid^="stAlertContent"] {{ background:var(--surface-alt)!important; color:var(--ink); }}
.stButton > button, .stDownloadButton > button {{ border-radius:10px; font-weight:650; min-height:2.55rem; border-color:var(--border); }}
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {{ background:var(--blue); border-color:var(--blue); color:#fff; }}
.stButton > button:hover, .stDownloadButton > button:hover {{ border-color:var(--blue); color:var(--blue); }}
.hero {{ padding:1.35rem 1.55rem; border-radius:20px; color:#fff; background:linear-gradient(115deg,#081329 0%,#102650 72%,#126c8e 100%); box-shadow:var(--shadow); margin:.15rem 0 1.1rem; }}
.hero h1 {{ color:#fff; margin:0; font-size:1.8rem; }}
.hero p {{ color:#dbe7ff; margin:.45rem 0 0; }}
.eyebrow {{ color:#75dff0!important; text-transform:uppercase; letter-spacing:.12em; font-size:.72rem; font-weight:750; margin:0 0 .35rem!important; }}
.auth-shell {{ padding:1.35rem; border-radius:22px; border:1px solid var(--border); background:var(--surface); box-shadow:var(--shadow); }}
.auth-card {{ min-height:34rem; height:100%; display:flex; flex-direction:column; justify-content:center; padding:2.2rem; border:1px solid rgba(164,207,255,.15); border-radius:22px; color:#fff; background:radial-gradient(ellipse at 87% 13%,rgba(22,200,232,.24),transparent 36%),linear-gradient(145deg,#081329 0%,#102650 68%,#173d70 100%); box-shadow:var(--shadow); position:relative; overflow:hidden; }}
.auth-card h1 {{ color:#fff; font-size:clamp(1.8rem,3vw,2.45rem); line-height:1.14; margin:.55rem 0 .8rem; }}
.auth-card p {{ color:#d2def2; line-height:1.65; }}
.auth-card .auth-tag {{ color:#72deed; text-transform:uppercase; letter-spacing:.13em; font-weight:750; font-size:.76rem; }}
.brandmark {{ display:flex; align-items:center; gap:.7rem; margin-bottom:1.5rem; color:#fff; font-weight:720; font-size:1rem; }}
.brand-icon {{ display:grid; place-items:center; height:2.5rem; width:2.5rem; border:1px solid rgba(120,220,255,.4); border-radius:12px; background:rgba(40,120,240,.2); color:#7be4f1; font-size:1.35rem; }}
.feature-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:.65rem; margin:1.05rem 0 1.35rem; }}
.feature-item {{ padding:.72rem .8rem; border:1px solid rgba(205,225,255,.15); border-radius:12px; background:rgba(255,255,255,.055); }}
.feature-item strong {{ display:block; color:#f2f7ff; font-size:.83rem; }}
.feature-item span {{ color:#b7c7df; font-size:.72rem; }}
.auth-footnote {{ border-top:1px solid rgba(205,225,255,.17); padding-top:.8rem; color:#aabbd4!important; font-size:.72rem; }}
[role="radiogroup"][aria-label="Appearance"], [role="radiogroup"][aria-label="Account access"] {{ border:1px solid var(--border); border-radius:11px; background:var(--surface); padding:.2rem; }}
[role="radiogroup"][aria-label="Appearance"] button[data-variant="segmented_control"],
[role="radiogroup"][aria-label="Account access"] button[data-variant="segmented_control"] {{ border-radius:8px; color:var(--muted); background:transparent; }}
[role="radiogroup"][aria-label="Appearance"] button[data-variant="segmented_control"][aria-checked="true"],
[role="radiogroup"][aria-label="Account access"] button[data-variant="segmented_control"][aria-checked="true"] {{ color:#fff; background:var(--blue); box-shadow:none; }}
[role="radiogroup"][aria-label="Appearance"] button[data-variant="segmented_control"] p,
[role="radiogroup"][aria-label="Account access"] button[data-variant="segmented_control"] p {{ color:inherit!important; }}
[role="radiogroup"][aria-label="Appearance"] button[data-variant="segmented_control"]:focus-visible,
[role="radiogroup"][aria-label="Account access"] button[data-variant="segmented_control"]:focus-visible {{ outline:2px solid var(--cyan)!important; outline-offset:2px; border-color:var(--cyan)!important; }}
[data-testid="stRadio"] label, [data-testid="stCheckbox"] label {{ color:var(--ink); }}
button:focus-visible, input:focus-visible, a:focus-visible {{ outline:2px solid var(--cyan)!important; outline-offset:2px; }}
@media(max-width:760px) {{
  [data-testid="stMainBlockContainer"] {{ padding-left:1rem; padding-right:1rem; }}
  .auth-card {{ min-height:0; padding:1.35rem; margin-bottom:.4rem; }}
  .hero {{ padding:1.1rem; }}
  .feature-grid {{ gap:.5rem; }}
}}
</style>
"""
st.markdown(theme_css, unsafe_allow_html=True)
st.warning("DEMO ONLY — bundled data are synthetic. No bank connection, real payment, lending decision, or external message is performed.")

# Local account authentication. Roles are loaded from SQLite, never chosen by the user in the dashboard.
init_db()
if "auth_user" not in st.session_state:
    st.session_state.auth_user = None
if not st.session_state.auth_user:
    first_run = user_count() == 0
    if st.session_state.get("auth_mode", "Sign in") != "Create account":
        for key in ("register_password", "register_confirm", "register_show_password"):
            st.session_state.pop(key, None)
    if not first_run:
        st.session_state.pop("owner_confirm", None)
    welcome_col, form_col = st.columns([1.08, .92], gap="large")
    with welcome_col:
        st.markdown("""
        <div class="auth-card">
          <div class="brandmark"><span class="brand-icon">⌁</span><span>CashFlow Sentinel AI</span></div>
          <p class="auth-tag">SME FINANCE COPILOT</p>
          <h1>Cash flow clarity, built for better decisions.</h1>
          <p>Bring cash-flow forecasts and payment-delay scenarios together to see pressure sooner and make informed decisions.</p>
          <div class="feature-grid">
            <div class="feature-item"><strong>⌁ &nbsp; Forecast cash flow</strong><span>Understand your projected cash position.</span></div>
            <div class="feature-item"><strong>◉ &nbsp; Simulate risks</strong><span>Test payment timing under assumptions.</span></div>
            <div class="feature-item"><strong>↗ &nbsp; Compare options</strong><span>Review trade-offs and estimated impact.</span></div>
            <div class="feature-item"><strong>✓ &nbsp; Human-controlled</strong><span>Review evidence; no action is automated.</span></div>
          </div>
          <p class="auth-footnote">Prototype decision support · Bundled sample data are synthetic · Not financial advice</p>
        </div>
        """, unsafe_allow_html=True)
    with form_col:
        auth_notice = st.session_state.pop("auth_notice", None)
        if auth_notice:
            st.success(auth_notice)
        if first_run:
            auth_mode = "Create owner account"
        else:
            auth_mode = st.session_state.get("auth_mode", "Sign in")
        title = "Set up your workspace" if first_run else ("Create your account" if auth_mode == "Create account" else "Welcome back")
        subtitle = (
            "Create the first local owner account to initialize the workspace."
            if first_run else
            "Create a local viewer account for read-only access."
            if auth_mode == "Create account" else
            "Sign in to access your CashFlow Sentinel AI workspace."
        )
        st.markdown(f"### {title}")
        st.caption(subtitle)
        if auth_mode == "Create account":
            st.text_input("♙  Full name", key="register_full_name", max_chars=120)
            st.text_input("♙  Username", key="register_username", max_chars=64, help="3–64 characters: letters, numbers, underscores, or hyphens.")
            show_password = st.checkbox("Show passwords", key="register_show_password")
            password_type = "default" if show_password else "password"
            password = st.text_input("🔒  Password", type=password_type, key="register_password", help="Use at least 12 characters.")
            st.caption("Password guidance: use at least 12 characters; a unique 16+ character passphrase is recommended.")
            confirmation = st.text_input("🔒  Confirm password", type=password_type, key="register_confirm")
            submitted = st.button("Create account", type="primary", use_container_width=True)
        else:
            username_label = "Owner username" if first_run else "Username"
            if first_run:
                st.text_input("♙  Full name", key="owner_full_name", max_chars=120)
            st.text_input(f"♙  {username_label}", key="login_username", max_chars=64)
            show_password = st.checkbox("Show password", key="login_show_password")
            password_type = "default" if show_password else "password"
            password = st.text_input("🔒  Owner password" if first_run else "🔒  Password", type=password_type, key="login_password")
            confirmation = st.text_input("🔒  Confirm password", type=password_type, key="owner_confirm") if first_run else None
            submitted = st.button("Create owner account" if first_run else "Sign in", type="primary", use_container_width=True)
            username = st.session_state["login_username"]
        if submitted:
            if first_run:
                full_name = st.session_state.get("owner_full_name", "")
                if not full_name.strip():
                    st.error("Full name is required.")
                elif not username.strip():
                    st.error("Username is required.")
                elif not password or not confirmation:
                    st.error("Password and confirmation are required.")
                elif password != confirmation:
                    st.error("Passwords do not match.")
                else:
                    try:
                        created_username = create_user(username, password, "owner", full_name)
                    except ValueError as exc:
                        st.error(str(exc))
                    except sqlite3.Error:
                        st.error("The local account database could not save the account. Check database availability and try again.")
                    else:
                        auth_notice = "Owner account created. Sign in using your new credentials."
                        try:
                            write_audit(created_username, "owner", "ACCOUNT_CREATED", "local_owner", "success", "First local owner account created")
                        except sqlite3.Error:
                            auth_notice = "Owner account created, but its audit record could not be saved. Sign in using your new credentials."
                        st.session_state["auth_notice"] = auth_notice
                        st.session_state["auth_mode"] = "Sign in"
                        st.rerun()
            elif auth_mode == "Create account":
                full_name = st.session_state.get("register_full_name", "")
                username = st.session_state.get("register_username", "")
                if not full_name.strip():
                    st.error("Full name is required.")
                elif not username.strip():
                    st.error("Username is required.")
                elif not password or not confirmation:
                    st.error("Password and confirmation are required.")
                elif password != confirmation:
                    st.error("Passwords do not match.")
                else:
                    try:
                        created_username = create_user(username, password, "viewer", full_name)
                    except ValueError as exc:
                        st.error(str(exc))
                    except sqlite3.Error:
                        st.error("The local account database could not save the account. Check database availability and try again.")
                    else:
                        auth_notice = "Account created. Sign in to continue."
                        try:
                            write_audit(created_username, "viewer", "ACCOUNT_REGISTERED", "local_app", "success")
                        except sqlite3.Error:
                            auth_notice = "Account created, but its audit record could not be saved. Sign in to continue."
                        st.session_state["auth_notice"] = auth_notice
                        st.session_state["auth_mode"] = "Sign in"
                        st.rerun()
            else:
                if not username.strip() or not password:
                    st.error("Enter your username and password.")
                else:
                    try:
                        user = authenticate(username, password)
                    except sqlite3.Error:
                        st.error("The local account database is unavailable. Try again later.")
                    else:
                        if user:
                            st.session_state.auth_user = user
                            write_audit(user["username"], user["role"], "LOGIN", "local_app", "success")
                            st.rerun()
                        else:
                            write_audit(username.strip().lower() or "unknown", "viewer", "LOGIN", "local_app", "denied", "Invalid credentials")
                            st.error("Invalid username or password.")
        if not first_run:
            st.button(
                "Already have an account? Sign in" if auth_mode == "Create account" else "Create account",
                on_click=set_auth_mode,
                args=("Sign in" if auth_mode == "Create account" else "Create account",),
                use_container_width=True,
            )
    st.caption("Local prototype authentication only. Do not expose this app to the public internet or use highly sensitive production data.")
    st.stop()
else:
    for key in ("login_password", "login_show_password", "owner_confirm"):
        st.session_state.pop(key, None)
current_user = st.session_state.auth_user
with st.sidebar:
    st.markdown("## 🛡️ CashFlow Sentinel")
    st.caption("SME FINANCE COPILOT")
    st.markdown("---")
    st.markdown("**WORKSPACE**")
    st.markdown("""
    <a href="#overview">◈ &nbsp; Overview</a>
    <a href="#forecast">⌁ &nbsp; Cash-flow forecast</a>
    <a href="#stress-tests">◉ &nbsp; Payment stress tests</a>
    <a href="#actions">↗ &nbsp; Action comparison</a>
    <a href="#risk-radar">◎ &nbsp; Financial risk radar</a>
    <a href="#supply-chain">⬡ &nbsp; Supply-chain risk</a>
    <a href="#copilot">✦ &nbsp; AI insights & chat</a>
    <a href="#financing">▤ &nbsp; Financing comparison</a>
    <a href="#audit">▣ &nbsp; Audit & controls</a>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("**YOUR ACCOUNT**")
    st.success(f"Signed in: {current_user['username']} · {current_user['role'].title()}")
    if st.button("Sign out"):
        write_audit(current_user['username'], current_user['role'], "LOGOUT", "local_app", "success")
        # Clear potentially sensitive per-user outputs before ending the session.
        for key in ["copilot_answer", "time_machine_compare", "time_machine_forecast", "time_machine_forecasts", "last_network_result", "last_network_seed", "network_propagation_result", "demo_audit_log", "v05_audit_records"]:
            st.session_state.pop(key, None)
        st.session_state.auth_user = None
        st.rerun()
    if current_user['role'] == 'owner':
        with st.expander("Owner: create user"):
            with st.form("create_user_form"):
                uname = st.text_input("New username")
                upass = st.text_input("Temporary password (12+ characters)", type="password")
                urole = st.selectbox("Role", ["viewer", "analyst", "owner"])
                user_submit = st.form_submit_button("Create user")
            if user_submit:
                try:
                    create_user(uname, upass, urole)
                except ValueError as exc: st.error(str(exc))
                except sqlite3.Error:
                    st.error("The local account database could not save this user. Check database availability and try again.")
                else:
                    try:
                        write_audit(current_user['username'], current_user['role'], "USER_CREATED", uname, "success", f"Assigned role {urole}")
                    except sqlite3.Error:
                        st.warning("User created, but its audit record could not be saved.")
                    st.success("User created. Share credentials securely and ask them to change the password outside this demo if supported.")
role = {"viewer":"Tier 0 — Viewer", "analyst":"Tier 1 — Analyst", "owner":"Tier 2 — Owner review"}[current_user['role']]
initials = escape("".join(part[0] for part in current_user["username"].replace("_", " ").replace("-", " ").split()[:2]).upper())
st.markdown(f'<div class="hero" id="overview"><p class="eyebrow">Cash flow intelligence · Local demo workspace</p><h1>Welcome back, {escape(current_user["username"])} <span style="font-size:1.05rem;color:#9ce5dc">· {initials}</span></h1><p>Explainable forecasts, practical stress tests, and clear next steps — grounded in the selected data.</p></div>', unsafe_allow_html=True)
st.caption("Prototype decision support only · Synthetic bundled data · Verify assumptions before acting")
@st.cache_data
def load_sample():
    return validate_transactions(pd.read_csv(ROOT/"data/sample_transactions.csv")),validate_network(pd.read_csv(ROOT/"data/sample_network.csv"))
try: sample_tx,sample_net=load_sample()
except Exception as e: st.error(f"Sample data error: {e}"); st.stop()
with st.sidebar:
    st.header("Data")
    upload=st.checkbox("Use uploaded CSVs")
    txfile=st.file_uploader("Transactions CSV",type=["csv"],disabled=not upload)
    netfile=st.file_uploader("Network CSV",type=["csv"],disabled=not upload)
    if upload and txfile and netfile:
        try:
            transactions=validate_transactions(pd.read_csv(txfile)); network=validate_network(pd.read_csv(netfile))
            tq = transaction_quality_report(transactions); nq = network_quality_report(network)
            st.success("Schema validation passed")
            with st.expander("Upload data-quality report", expanded=bool(tq["warnings"] or nq["warnings"])):
                st.write({"transactions": tq, "network": nq})
                st.caption("Duplicate-like rows are flagged, not automatically removed, because they may be separate legitimate transactions. Reconcile against your accounting system before using real data.")
        except Exception as e: st.error(f"Validation failed: {e}"); st.stop()
    elif upload: st.info("Upload both files to continue."); st.stop()
    else: transactions,network=sample_tx.copy(),sample_net.copy()
    businesses=transactions[["business_id","business_name"]].drop_duplicates()
    selected=st.selectbox("Business",businesses.business_id.tolist(),format_func=lambda x: businesses.loc[businesses.business_id==x,"business_name"].iloc[0])
    start=st.date_input("Forecast start date",value=transactions.date.min().date())
    horizon=st.slider("Horizon (days)",7,60,30)
    opening=st.number_input("Opening cash (currency units)",min_value=0.0,value=100000.0,step=5000.0)

st.markdown('<div id="forecast"></div>', unsafe_allow_html=True)
st.subheader("Cash-flow forecast")
base=forecast_business(transactions,selected,opening,start,horizon); summary=summarize_forecast(base)
a,b,c=st.columns(3); a.metric("Ending cash",f"{summary['ending_cash']:,.0f}"); b.metric("Minimum cash",f"{summary['minimum_cash']:,.0f}"); c.metric("Shortfall days",summary["shortfall_days"])
if summary["first_shortfall_date"]: st.error(f"Potential negative cash begins {summary['first_shortfall_date']} (modelled scenario, not certainty).")
else: st.success("No negative closing balance in this baseline; liquidity is not guaranteed.")
fig=go.Figure(); fig.add_trace(go.Scatter(x=base.date,y=base.closing_cash,mode="lines+markers",name="Baseline",line=dict(color=palette["blue"],width=3))); fig.add_hline(y=0,line_dash="dash",annotation_text="Zero cash",line_color="#e9a23b"); fig.update_layout(template=plot_template,paper_bgcolor=plot_background,plot_bgcolor=plot_background,font=dict(color=palette["text"]),xaxis_title="Date",yaxis_title="Closing cash",height=350,margin=dict(l=12,r=12,t=24,b=12)); st.plotly_chart(fig,use_container_width=True)
with st.expander("Daily forecast table"): st.dataframe(base,use_container_width=True,hide_index=True)

st.markdown('<div id="stress-tests"></div>', unsafe_allow_html=True)
st.subheader("Payment-delay stress test")
st.write("This deterministic stress test shifts a selected incoming payment date. It does not predict the probability of a delay.")
edges=network[network.to_business_id.astype(str)==str(selected)]
if edges.empty: st.info("No incoming network edge for this business in the current sample.")
else:
    labels=edges.apply(lambda r:f"{r.from_business_id} → {r.to_business_id} | {r.amount:,.0f}",axis=1).tolist(); choice=st.selectbox("Payer → receiver",labels); edge=edges.iloc[labels.index(choice)]; delay=st.slider("Simulated delay (days)",0,30,10)
    if st.button("Run shock simulation",type="primary"):
        try:
            require_permission(role, "run_simulation")
            changed,_=apply_payment_delay(transactions,network,edge.from_business_id,edge.to_business_id,delay); scenario=forecast_business(changed,selected,opening,start,horizon); ss=summarize_forecast(scenario)
            x,y,z=st.columns(3); x.metric("Scenario ending cash",f"{ss['ending_cash']:,.0f}",delta=f"{ss['ending_cash']-summary['ending_cash']:,.0f} vs baseline"); y.metric("Scenario minimum cash",f"{ss['minimum_cash']:,.0f}"); z.metric("Scenario shortfall days",ss["shortfall_days"],delta=ss["shortfall_days"]-summary["shortfall_days"])
            chart=go.Figure(); chart.add_trace(go.Scatter(x=base.date,y=base.closing_cash,name="Baseline",mode="lines+markers",line=dict(color=palette["blue"],width=3))); chart.add_trace(go.Scatter(x=scenario.date,y=scenario.closing_cash,name=f"{delay}-day delay",mode="lines+markers",line=dict(color="#16c8e8",width=3))); chart.add_hline(y=0,line_dash="dash",line_color="#e9a23b"); chart.update_layout(template=plot_template,paper_bgcolor=plot_background,plot_bgcolor=plot_background,font=dict(color=palette["text"]),xaxis_title="Date",yaxis_title="Closing cash",height=350,margin=dict(l=12,r=12,t=24,b=12)); st.plotly_chart(chart,use_container_width=True)
            st.info("This single-receiver chart is distinct from the multi-hop network stress simulation in section 3. Both are deterministic scenarios, not calibrated probability predictions.")
            log=pd.DataFrame([{"event":"SIMULATED_PAYMENT_DELAY","payer":edge.from_business_id,"receiver":edge.to_business_id,"delay_days":delay,"baseline_ending_cash":summary["ending_cash"],"scenario_ending_cash":ss["ending_cash"],"human_approval_required":True,"external_action_executed":False}])
            st.download_button("Download simulated action log CSV",log.to_csv(index=False),"simulated_action_log.csv","text/csv")
        except Exception as e: st.error(f"Scenario error: {e}")

st.subheader("Network-wide payment-shock propagation")
st.caption("Deterministic multi-hop stress test over connected payment edges. This is a scenario, not a calibrated probability forecast.")
if network.empty:
    st.info("No network records available.")
else:
    network_payers = sorted(network["from_business_id"].astype(str).unique().tolist())
    shock_payer = st.selectbox("Shock origin (payer)", network_payers, key="network_shock_payer")
    network_delay = st.slider("Initial shock delay (days)", 0, 30, 10, key="network_shock_delay")
    liquidity_buffer = st.number_input("Assumed liquidity buffer per connected edge", min_value=0.0, value=20000.0, step=5000.0, key="network_buffer")
    max_hops = st.slider("Maximum propagation hops", 1, 10, 5, key="network_max_hops")
    if st.button("Run multi-hop network simulation", type="primary", key="run_network_simulation"):
        try:
            require_permission(role, "run_simulation")
            propagation = propagate_payment_shock(network, shock_payer, int(network_delay), float(liquidity_buffer), int(max_hops))
            st.session_state["network_propagation_result"] = propagation
            write_audit(current_user["username"], current_user["role"], "NETWORK_STRESS_TEST", shock_payer, "success",
                        f"delay_days={network_delay}; buffer={liquidity_buffer}; hops={max_hops}; edges={len(propagation)}")
        except (AuthorizationError, ValueError, TypeError) as exc:
            st.error(f"Network simulation failed: {exc}")
    if "network_propagation_result" in st.session_state:
        propagation = st.session_state["network_propagation_result"]
        if propagation.empty:
            st.info("No connected payment edges were reached for this shock origin and hop limit.")
        else:
            st.metric("Edges examined", len(propagation))
            affected = propagation[propagation["propagation_triggered"]]
            st.metric("Edges where shock propagates under assumptions", len(affected))
            st.dataframe(propagation, use_container_width=True, hide_index=True)
            try:
                require_permission(role, "export_simulated_log")
                st.download_button("Download network propagation evidence CSV", propagation.to_csv(index=False), "network_propagation_evidence.csv", "text/csv")
            except AuthorizationError:
                st.info("Evidence export requires Analyst or Owner role in this demo policy.")

st.markdown('<div id="actions"></div>', unsafe_allow_html=True)
st.subheader("Illustrative action comparison")
st.caption("Amounts below are editable assumptions, not model predictions.")
gap=st.number_input("Estimated cash gap",min_value=0.0,value=30000.0,step=5000.0)
def action(name,relief,cost,feasible,evidence,uncertainty): return {"name":name,"estimated_cash_relief":relief,"estimated_cost":cost,"feasible":feasible,"evidence":evidence,"uncertainty":uncertainty}
actions=[action("Request early customer payment",25000,0,True,"Open invoice must be confirmed","High: customer may decline or pay late"),action("Negotiate supplier payment date",20000,1000,True,"Supplier bill due soon; agreement required","Medium/high: supplier approval required"),action("Delay optional inventory purchase",15000,2500,True,"Optional purchase; check stock and sales impact","Medium: stockout or lost sales risk"),action("New short-term borrowing",30000,3500,False,"Disabled: no lending integration","High: eligibility and repayment burden unknown")]
with st.expander("Edit action assumptions"):
    for i,a0 in enumerate(actions):
        a0["estimated_cash_relief"]=st.number_input(f"{a0['name']} relief",min_value=0.0,value=float(a0["estimated_cash_relief"]),step=2500.0,key=f"relief{i}")
        a0["estimated_cost"]=st.number_input(f"{a0['name']} cost",min_value=0.0,value=float(a0["estimated_cost"]),step=500.0,key=f"cost{i}")
        a0["feasible"]=st.checkbox(f"{a0['name']} feasible?",value=bool(a0["feasible"]),key=f"feasible{i}")
ranked=rank_actions(actions,gap); st.dataframe(pd.DataFrame([{"Action":r["name"],"Estimated relief":r["estimated_cash_relief"],"Estimated cost":r["estimated_cost"],"Net benefit estimate":r["net_estimated_benefit"],"Feasible":r["feasible"],"Evidence/assumption":r["evidence"],"Uncertainty/trade-off":r["uncertainty"],"Covers gap":r["covers_shortfall"]} for r in ranked]),use_container_width=True,hide_index=True)
st.warning("No action is executed. Verify assumptions and obtain business-owner approval before taking any real-world action.")

st.markdown('<div id="copilot"></div>', unsafe_allow_html=True)
st.subheader("Explainable AI insights")
st.caption("This MVP uses transparent rules over forecast and transaction records. It is an agent-style decision-support prototype, not a generative LLM or trained ML model.")
brief = generate_agent_brief(transactions, selected, base)
st.info(f"Agent type: {brief['agent_type']}")
st.write(brief["model_note"])
for item in brief["actions"]:
    with st.container(border=True):
        st.markdown(f"**{item['priority']} · {item['recommendation']}**")
        st.write(item["reason"])
        st.caption(f"Evidence: {item['evidence']}")
        st.caption(f"Uncertainty: {item['uncertainty']}")
        st.caption(f"Control: {item['approval']}")

st.markdown('<div id="audit"></div>', unsafe_allow_html=True)
st.subheader("Security controls & human approval")
st.warning("Permissions are linked to the authenticated local account. This prototype login is not a production identity provider; do not expose it to the public internet or upload highly sensitive data.")
if role.startswith("Tier 0"):
    st.info("Viewer mode: view forecasts and agent brief only. Simulation, exports, and review recording are blocked by policy.")
elif role.startswith("Tier 1"):
    st.info("Analyst mode: run simulations and export simulated evidence. Recording owner review decisions is blocked.")
else:
    st.info("Owner-review mode: run simulations, export evidence, and record human review decisions. No external action is available.")
with st.form("approval_form"):
    proposed_action = st.selectbox("Action to review", [a["name"] for a in actions])
    decision = st.radio("Review decision", ["Needs more evidence", "Approved for human follow-up", "Rejected"], horizontal=True)
    note = st.text_input("Reason / evidence note", max_chars=250)
    submitted = st.form_submit_button("Record review decision")
    if submitted:
        try:
            record = make_audit_record(role, proposed_action, decision, note, pd.Timestamp.now(tz="UTC").isoformat())
            if "demo_audit_log" not in st.session_state:
                st.session_state["demo_audit_log"] = []
            st.session_state["demo_audit_log"].append(record)
            write_audit(current_user["username"], current_user["role"], "HUMAN_REVIEW", proposed_action, decision, note)
            st.success("Review decision saved to persistent local SQLite audit log. No real-world action was executed.")
        except (AuthorizationError, ValueError) as e:
            st.error(str(e))
if st.session_state.get("demo_audit_log"):
    audit = pd.DataFrame(st.session_state["demo_audit_log"])
    st.dataframe(audit, use_container_width=True, hide_index=True)
    try:
        require_permission(role, "export_simulated_log")
        st.download_button("Download demo security audit log CSV", audit.to_csv(index=False), "demo_security_audit_log.csv", "text/csv")
    except AuthorizationError:
        st.info("Audit log export requires Tier 1 Analyst or Tier 2 Owner in this demo policy.")


st.subheader("7. Enforced demo authorization checks")
st.caption("Role comes from the signed-in local account. This local prototype is not production-grade IAM.")
demo_role = current_user["role"]
st.caption(f"Authenticated role from local account store: {demo_role}")
requested_permission = st.selectbox("Permission to check", ["view", "simulate", "export", "review"], key="requested_permission")
if st.button("Check authorization", key="check_authorization"):
    try:
        authorize(demo_role, requested_permission)
        st.success(f"ALLOW: {demo_role} may perform '{requested_permission}'.")
    except AuthorizationError as exc:
        st.error(f"BLOCKED: {exc}")
with st.form("owner_review_v05"):
    st.write("Human review record (owner permission required)")
    review_action = st.text_input("Proposed action", value="Request customer payment confirmation", max_chars=120)
    review_decision = st.selectbox("Review decision", ["Needs more evidence", "Approved for human follow-up", "Rejected"])
    review_note = st.text_input("Review note", max_chars=250)
    review_submit = st.form_submit_button("Record review decision")
    if review_submit:
        try:
            audit_record = make_audit_record(role, review_action, review_decision, review_note)
            if "v05_audit_records" not in st.session_state:
                st.session_state["v05_audit_records"] = []
            st.session_state["v05_audit_records"].append(audit_record)
            write_audit(current_user["username"], current_user["role"], "HUMAN_REVIEW", review_action, decision, review_note)
            st.success("Review decision saved to persistent local SQLite audit log. No external action was executed.")
        except (AuthorizationError, ValueError) as exc:
            st.error(f"BLOCKED: {exc}")
if current_user["role"] == "owner":
    persisted = pd.DataFrame(read_audit())
    if not persisted.empty:
        st.markdown("**Persistent audit log (SQLite)**")
        st.dataframe(persisted, use_container_width=True, hide_index=True)
        st.download_button("Download persistent audit log CSV", persisted.to_csv(index=False), "persistent_audit_log.csv", "text/csv")


st.subheader("Finance Copilot chat")
st.caption("Python rules work offline. Optional Ollama mode runs a small language model locally; no OpenAI API key is needed. Financial calculations remain in Python.")
chat_mode = st.radio("Chat engine", ["Python Rule-Based (offline)", "Ollama Local AI (free)"] , horizontal=True, key="finance_chat_mode")
if chat_mode == "Ollama Local AI (free)":
    ollama_model = st.text_input("Local Ollama model", value="qwen2.5:3b", help="For 8 GB RAM, start with qwen2.5:3b. If slow, try qwen2.5:1.5b.", key="ollama_model")
    ollama_url = st.text_input("Ollama URL", value="http://localhost:11434", key="ollama_url")
else:
    ollama_model = "qwen2.5:3b"
    ollama_url = "http://localhost:11434"
question = st.text_input("Ask about this business", placeholder="Why is my cash decreasing? / Is there a cash shortage risk? / Which customer payments matter most?", key="finance_chat_question")
if st.button("Ask Finance Copilot", type="primary", key="ask_finance_copilot"):
    try:
        require_permission(role, "view_agent")
        if not question.strip():
            st.warning("Enter a question first.")
        elif chat_mode == "Ollama Local AI (free)":
            with st.spinner("Waiting for local Ollama model..."):
                answer = ask_local_ollama(question, transactions, selected, base, ollama_model, ollama_url)
            st.session_state["copilot_answer"] = answer
        else:
            answer = rule_based_chat(question, transactions, selected, base)
            st.session_state["copilot_answer"] = answer
    except Exception as exc:
        st.error(f"Chat could not answer: {exc}")
        if chat_mode == "Ollama Local AI (free)":
            st.info("Fallback: switch to Python Rule-Based (offline), or check that Ollama is running and the selected model is installed.")
if st.session_state.get("copilot_answer"):
    answer = st.session_state["copilot_answer"]
    st.caption("Mode: " + answer.get("mode", "Python rule-based chat"))
    st.markdown(answer.get("answer", "No answer returned."))
    st.caption("Uncertainty: " + answer.get("uncertainty", "Verify against the underlying records."))
    with st.expander("Evidence used for this answer", expanded=True):
        evidence = answer.get("evidence", pd.DataFrame())
        if isinstance(evidence, pd.DataFrame) and not evidence.empty:
            st.dataframe(evidence, use_container_width=True, hide_index=True)
        else:
            st.info("No row-level evidence was needed for this response. Check the selected business and data coverage.")
    if st.button("Clear chat answer", key="clear_finance_chat"):
        st.session_state.pop("copilot_answer", None)
        st.rerun()

st.markdown('<div id="risk-radar"></div>', unsafe_allow_html=True)
st.subheader("Explainable financial risk radar")
radar = risk_radar(transactions, network, selected, base)
st.dataframe(radar, use_container_width=True, hide_index=True)
st.caption("Severity labels follow simple demo thresholds, not calibrated probabilities or regulated credit-risk scores.")

st.markdown('<div id="financing"></div>', unsafe_allow_html=True)
st.subheader("Illustrative financing comparison")
st.caption("Illustrative products only. These are not live offers, market quotes, loan eligibility decisions, or financial advice.")
financing_gap = st.number_input("Cash gap to finance (currency units)", min_value=0.0, value=30000.0, step=5000.0, key="financing_gap")
financing = financing_options(financing_gap)
st.dataframe(financing, use_container_width=True, hide_index=True)
st.info("Rates, fees and approval speeds are synthetic assumptions. Confirm real APR, fees, collateral, recourse, eligibility and repayment terms with regulated providers before making a decision.")

st.markdown('<div id="supply-chain"></div>', unsafe_allow_html=True)
st.subheader("Supply-chain risk & counterparty vulnerability")
st.caption("Top counterparties ranked by recorded exposure amount. This is an exposure proxy, not a default probability.")
vulnerability = counterparty_vulnerability(transactions, network, selected)
if vulnerability.empty:
    st.info("No counterparty records found for the selected business.")
else:
    st.dataframe(vulnerability, use_container_width=True, hide_index=True)
    st.markdown("**Top 3 critical bottlenecks**")
    for _, row in vulnerability.head(3).iterrows():
        st.write(f"- **{row['Counterparty']}** — exposure {row['Exposure amount']:,.0f}; score {row['Criticality score']:.1f}/100. Evidence: {row['Evidence']}. Uncertainty: {row['Uncertainty']}.")

st.subheader("12. Financial Time Machine — Baseline vs Scenario A vs Scenario B")
st.caption("Compare two independent what-if scenarios against the same baseline. Results are deterministic cash-flow simulations, not probability forecasts. Price reduction is a conservative cash-impact assumption, not a demand or margin model.")
scenario_types = ["No change", "Customer payment delayed", "Inventory purchase", "Price reduced"]
sc_a, sc_b = st.columns(2)
with sc_a:
    st.markdown("**Scenario A**")
    type_a = st.selectbox("Scenario A type", scenario_types, index=1, key="tm_type_a")
    amount_a = st.number_input("Scenario A amount", min_value=0.0, value=50000.0, step=5000.0, key="tm_amount_a")
    days_a = st.slider("Scenario A delay / offset (days)", 0, 30, 15, key="tm_days_a")
    price_a = st.slider("Scenario A price reduction (%)", 0, 100, 10, key="tm_price_a")
with sc_b:
    st.markdown("**Scenario B**")
    type_b = st.selectbox("Scenario B type", scenario_types, index=2, key="tm_type_b")
    amount_b = st.number_input("Scenario B amount", min_value=0.0, value=50000.0, step=5000.0, key="tm_amount_b")
    days_b = st.slider("Scenario B delay / offset (days)", 0, 30, 7, key="tm_days_b")
    price_b = st.slider("Scenario B price reduction (%)", 0, 100, 10, key="tm_price_b")
if st.button("Compare Baseline vs A vs B", type="primary", key="run_time_machine"):
    try:
        require_permission(role, "run_simulation")
        tx_a, note_a = build_scenario_transactions(transactions, selected, "Baseline" if type_a == "No change" else type_a, amount_a, days_a, start, horizon, price_a)
        tx_b, note_b = build_scenario_transactions(transactions, selected, "Baseline" if type_b == "No change" else type_b, amount_b, days_b, start, horizon, price_b)
        fc_a = forecast_business(tx_a, selected, opening, start, horizon)
        fc_b = forecast_business(tx_b, selected, opening, start, horizon)
        sum_a, sum_b = summarize_forecast(fc_a), summarize_forecast(fc_b)
        compare = pd.DataFrame([
            {"Scenario":"Baseline", "Ending cash":summary["ending_cash"], "Minimum cash":summary["minimum_cash"], "Shortage days":summary["shortfall_days"], "Change in ending cash":0.0},
            {"Scenario":f"A — {type_a}", "Ending cash":sum_a["ending_cash"], "Minimum cash":sum_a["minimum_cash"], "Shortage days":sum_a["shortfall_days"], "Change in ending cash":sum_a["ending_cash"]-summary["ending_cash"]},
            {"Scenario":f"B — {type_b}", "Ending cash":sum_b["ending_cash"], "Minimum cash":sum_b["minimum_cash"], "Shortage days":sum_b["shortfall_days"], "Change in ending cash":sum_b["ending_cash"]-summary["ending_cash"]},
        ])
        st.session_state["time_machine_compare"] = compare
        st.session_state["time_machine_forecasts"] = {"Baseline":base, f"A — {type_a}":fc_a, f"B — {type_b}":fc_b}
        st.session_state["time_machine_notes"] = {"Scenario A":note_a, "Scenario B":note_b}
        st.session_state["time_machine_config"] = {"type_a":type_a,"amount_a":amount_a,"days_a":days_a,"price_a":price_a,"type_b":type_b,"amount_b":amount_b,"days_b":days_b,"price_b":price_b}
        write_audit(current_user["username"], current_user["role"], "WHAT_IF_COMPARE", str(selected), "success", "Baseline compared with two independent deterministic scenarios")
    except (AuthorizationError, ValueError) as exc:
        st.error(f"Scenario comparison blocked: {exc}")
if st.session_state.get("time_machine_compare") is not None:
    st.dataframe(st.session_state["time_machine_compare"], use_container_width=True, hide_index=True)
    notes = st.session_state.get("time_machine_notes", {})
    st.write("**Scenario A assumption:** " + notes.get("Scenario A", ""))
    st.write("**Scenario B assumption:** " + notes.get("Scenario B", ""))
    forecasts = st.session_state.get("time_machine_forecasts", {})
    tmfig = go.Figure()
    for name, frame in forecasts.items():
        tmfig.add_trace(go.Scatter(x=frame.date, y=frame.closing_cash, mode="lines+markers", name=name))
    tmfig.add_hline(y=0, line_dash="dash", annotation_text="Zero cash")
    tmfig.update_layout(template=plot_template, paper_bgcolor=plot_background, plot_bgcolor=plot_background, font=dict(color=palette["text"]), xaxis_title="Date", yaxis_title="Closing cash", height=380, margin=dict(l=12, r=12, t=24, b=12))
    st.plotly_chart(tmfig, use_container_width=True)
    cfg = st.session_state.get("time_machine_config", {})
    if cfg:
        st.download_button("Download scenario comparison CSV", st.session_state["time_machine_compare"].to_csv(index=False), "what_if_baseline_scenario_a_scenario_b.csv", "text/csv")


with st.expander("Known limitations"):
    st.markdown("- Bundled records are synthetic.\n- Opening cash is user-entered and not reconciled with a bank.\n- Expected inflows may not arrive on time.\n- Multi-hop propagation is deterministic and conservative; buffer values are assumptions, not calibrated liquidity measurements.\n- Action relief and costs are manual assumptions.\n- The current copilot uses deterministic evidence-grounded logic by default; optional LLM wording can still be wrong and must be checked against the evidence table. Financing products and time-machine shocks are illustrative assumptions. Upload quality diagnostics flag duplicate-like rows and missing counterparties but do not automatically reconcile them. Local password-based authentication and persistent SQLite audit records are implemented for this prototype. This is not a production identity provider; deployment still needs HTTPS/TLS, secret management, backup/retention policy, rate limiting, MFA and independent security review. Real-world forecast validation requires authorized, independently reconciled actual daily cash outcomes.")
st.caption("CashFlow Sentinel AI • Explainable SME Finance Copilot • Synthetic data • Decision support only")
