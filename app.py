"""
OmniGuard: AI-Powered Financial Sentinel & Wealth Advisory Platform
100% Free Technology Stack: Streamlit + Supabase (PostgreSQL) + Google AI Studio Gemini 3 Flash
"""

import io
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timezone

# Internal Services
from services.db_service import DatabaseService
from services.gemini_client import GeminiService
from services.fraud_engine import FraudEngine
from services.advisory_engine import AdvisoryEngine
from utils.mock_data import get_demo_csv_string

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="OmniGuard | AI Sentinel & Wealth Advisory",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling for FinTech Theme
st.markdown("""
<style>
    /* Metric Card Styling */
    div[data-testid="stMetricValue"] {
        font-size: 1.85rem !important;
        font-weight: 700 !important;
        color: #00E5FF !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.9rem !important;
        color: #94A3B8 !important;
    }
    /* Status Badges */
    .badge-critical {
        background-color: rgba(239, 68, 68, 0.2);
        color: #EF4444;
        border: 1px solid #EF4444;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .badge-high {
        background-color: rgba(245, 158, 11, 0.2);
        color: #F59E0B;
        border: 1px solid #F59E0B;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .badge-low {
        background-color: rgba(16, 185, 129, 0.2);
        color: #10B981;
        border: 1px solid #10B981;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    /* Card Container */
    .fin-card {
        background-color: #1C2541;
        border: 1px solid #3A4A7A;
        border-radius: 8px;
        padding: 18px;
        margin-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# SESSION STATE & SERVICE INITIALIZATION
# -----------------------------------------------------------------------------
def get_secret(key: str, default: str = "") -> str:
    """Safely retrieves keys from st.secrets or os.environ."""
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key, default)


# Initialize Database Service
if "db_service" not in st.session_state:
    supabase_url = get_secret("SUPABASE_URL")
    supabase_key = get_secret("SUPABASE_KEY")
    st.session_state.db_service = DatabaseService(supabase_url=supabase_url, supabase_key=supabase_key)

# Initialize Gemini API Service
if "gemini_service" not in st.session_state:
    gemini_key = get_secret("GEMINI_API_KEY")
    gemini_model = get_secret("GEMINI_MODEL", "gemini-3-flash")
    st.session_state.gemini_service = GeminiService(api_key=gemini_key, model_name=gemini_model)

# Engines
db = st.session_state.db_service
gemini = st.session_state.gemini_service
fraud_engine = FraudEngine(db=db, gemini=gemini)
advisory_engine = AdvisoryEngine(db=db, gemini=gemini)

# Chat history session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": "Welcome to **OmniGuard Copilot**! I continuously monitor your transactions for threats while surfacing personalized budgeting opportunities. How can I assist your financial journey today?"}
    ]


# -----------------------------------------------------------------------------
# SIDEBAR CONTROLS & SYSTEM TELEMETRY
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🛡️ **OmniGuard**")
    st.caption("AI Sentinel & Wealth Advisory Platform")
    st.divider()

    nav_selection = st.radio(
        "Navigation",
        [
            "📊 Executive Dashboard",
            "🛡️ Fraud Sentinel",
            "💡 Wealth & Budget Advisor",
            "📋 Transaction Ledger & Audit",
            "🚀 Deployment Blueprint",
        ],
        index=0
    )

    st.divider()
    st.markdown("#### **System Connectivity**")

    # Supabase Connection Status
    if db.is_connected:
        st.success("🟢 Supabase: Connected (PostgreSQL)")
    else:
        st.info("🟡 Supabase: In-Memory Demo Mode")

    # Gemini Flash Status
    if gemini.is_connected:
        st.success(f"🟢 Gemini: Active ({gemini.model_name})")
    else:
        st.warning("🟡 Gemini: Smart Simulation Mode")

    # Dynamic API Key Input (No code edits required)
    with st.expander("🔑 API & Cloud Credentials", expanded=False):
        st.caption("Enter your free Google AI Studio key to activate live Gemini inference:")
        user_gemini_key = st.text_input(
            "Gemini API Key",
            type="password",
            value=gemini.api_key if gemini.is_connected else "",
            placeholder="AIzaSy..."
        )
        model_choice = st.selectbox(
            "Target Model",
            ["gemini-3-flash", "gemini-2.5-flash", "gemini-2.0-flash"],
            index=0
        )
        if st.button("Apply AI Credentials"):
            st.session_state.gemini_service = GeminiService(api_key=user_gemini_key, model_name=model_choice)
            st.rerun()

        st.caption("Supabase Connection:")
        user_supa_url = st.text_input("Supabase URL", value=db.supabase_url or "", placeholder="https://xyz.supabase.co")
        user_supa_key = st.text_input("Supabase Anon Key", type="password", value=db.supabase_key or "", placeholder="eyJhbG...")
        if st.button("Connect Supabase"):
            st.session_state.db_service = DatabaseService(supabase_url=user_supa_url, supabase_key=user_supa_key)
            st.rerun()

    if st.button("🔄 Reset Demo Ledger"):
        db.reset_to_seed_data()
        st.success("Demo transactions refreshed!")
        st.rerun()

    st.caption("100% Free Stack: Streamlit + Supabase + Gemini 3 Flash")


# -----------------------------------------------------------------------------
# TAB 1: EXECUTIVE DASHBOARD
# -----------------------------------------------------------------------------
if nav_selection == "📊 Executive Dashboard":
    st.title("📊 Executive Risk & Wealth Overview")
    st.markdown("Real-time telemetry uniting fraud vigilance and wealth health metrics.")

    # High-level Metrics Row
    kpi = fraud_engine.get_risk_summary()
    profile = db.get_profile()
    accounts = db.get_accounts()
    total_balance = sum(float(a.get("current_balance", 0)) for a in accounts)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Analyzed", f"${kpi['total_volume_analyzed']:,.2f}", f"{kpi['total_transactions']} Txs")
    col2.metric("Liquid Reserves", f"${total_balance:,.2f}", f"{len(accounts)} Accounts")
    col3.metric("Flagged Alerts", kpi["flagged_alerts"], delta=f"{kpi['critical_threats']} Critical", delta_color="inverse")
    col4.metric("Average Risk", f"{kpi['average_risk_score']}/100", delta="Healthy" if kpi['average_risk_score'] < 30 else "Attention", delta_color="normal")
    col5.metric("Health Score", "84 / 100", delta="+3 pts this month")

    st.markdown("---")

    # Critical Alerts Banner
    if kpi["critical_threats"] > 0:
        st.error(
            f"⚠️ **Attention Required**: {kpi['critical_threats']} high-priority transaction anomalies detected! "
            f"Review these immediately in the **Fraud Sentinel** tab to prevent account unauthorized drainage."
        )

    # Visual Analytics Columns
    v_col1, v_col2 = st.columns([3, 2])

    with v_col1:
        st.subheader("📈 30-Day Outflow & Risk Trajectory")
        txs = db.get_transactions(limit=60)
        chart_data = []
        for t in txs:
            fa = t.get("fraud_assessment") or {}
            chart_data.append({
                "Date": str(t.get("transaction_time"))[:10],
                "Amount ($)": float(t.get("amount", 0)),
                "Merchant": t.get("merchant_name"),
                "Risk Score": fa.get("risk_score", 10),
                "Category": t.get("category", "General"),
            })
        if chart_data:
            df_chart = pd.DataFrame(chart_data)
            fig = px.scatter(
                df_chart,
                x="Date",
                y="Amount ($)",
                size="Amount ($)",
                color="Risk Score",
                color_continuous_scale=["#10B981", "#F59E0B", "#EF4444"],
                hover_data=["Merchant", "Category", "Risk Score"],
                title="Transaction Volumes Mapped Against Risk Scores"
            )
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=340
            )
            st.plotly_chart(fig, use_container_width=True)

    with v_col2:
        st.subheader("🎯 Risk Categorization Breakdown")
        levels = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        for t in txs:
            fa = t.get("fraud_assessment") or {}
            lvl = fa.get("risk_level", "LOW")
            levels[lvl] = levels.get(lvl, 0) + 1

        fig_pie = go.Figure(data=[go.Pie(
            labels=list(levels.keys()),
            values=list(levels.values()),
            hole=.45,
            marker_colors=["#10B981", "#F59E0B", "#F97316", "#EF4444"]
        )])
        fig_pie.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=340,
            margin=dict(t=10, b=10, l=10, r=10)
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # Quick Triage Table
    st.subheader("⚡ Recent High-Risk Anomaly Alerts")
    flagged_txs = db.get_transactions(limit=10, only_anomalies=True)
    if flagged_txs:
        table_rows = []
        for t in flagged_txs:
            fa = t.get("fraud_assessment") or {}
            table_rows.append({
                "Tx ID": t.get("id"),
                "Timestamp": str(t.get("transaction_time"))[:19],
                "Merchant": t.get("merchant_name"),
                "Amount ($)": f"${float(t.get('amount', 0)):,.2f}",
                "Channel": t.get("channel"),
                "Risk Score": f"{fa.get('risk_score', 0)} / 100",
                "Level": fa.get("risk_level", "UNKNOWN"),
                "Action": fa.get("recommended_action", "REVIEW"),
                "Status": fa.get("resolution_status", "PENDING"),
            })
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)
    else:
        st.success("No active anomalies detected across the monitored window.")


# -----------------------------------------------------------------------------
# TAB 2: FRAUD SENTINEL
# -----------------------------------------------------------------------------
elif nav_selection == "🛡️ Fraud Sentinel":
    st.title("🛡️ Fraud Sentinel Engine")
    st.markdown("Real-time behavioral risk scoring and batch CSV anomaly detection powered by **Gemini 3 Flash**.")

    tab_single, tab_batch = st.tabs(["⚡ Live Transaction Inspector", "📁 Batch Ingestion (CSV)"])

    # --- SINGLE TRANSACTION INSPECTOR ---
    with tab_single:
        st.markdown("#### Test Real-Time Transaction Scoring")
        st.caption("Select a simulated test scenario or input custom transaction attributes:")

        # Quick Load Preset Buttons
        p_col1, p_col2, p_col3, p_col4 = st.columns(4)
        preset_chosen = None
        if p_col1.button("☕ Normal Coffee ($8.50)"):
            preset_chosen = ("Blue Bottle Coffee", 8.50, "Dining", "POS_CHIP", "New York", "US", "72.229.28.185")
        if p_col2.button("✈️ London Travel Spike ($1,840)"):
            preset_chosen = ("Harrods Luxury Dept", 1840.00, "Shopping", "POS_SWIPE", "London", "GB", "185.220.101.44")
        if p_col3.button("🌐 Offshore Wire ($7,950)"):
            preset_chosen = ("BitEx OTC Remittance", 7950.00, "Wire Transfer", "WIRE_TRANSFER", "Victoria", "SC", "45.154.255.89")
        if p_col4.button("🏧 ATM Rapid Burst ($800)"):
            preset_chosen = ("NCR-CashExpress #402", 800.00, "ATM Withdrawal", "ATM_WITHDRAWAL", "Miami", "US", "104.28.19.112")

        with st.form("single_tx_form"):
            f_col1, f_col2, f_col3 = st.columns(3)
            with f_col1:
                tx_merchant = st.text_input("Merchant Name", value=preset_chosen[0] if preset_chosen else "Nordstrom Dept Store")
                tx_amount = st.number_input("Amount ($)", min_value=0.01, max_value=500000.0, value=preset_chosen[1] if preset_chosen else 249.50)
            with f_col2:
                tx_category = st.selectbox(
                    "Expense Category",
                    ["Shopping", "Dining", "Groceries", "Transport", "Utilities", "Wire Transfer", "ATM Withdrawal", "Entertainment"],
                    index=0 if not preset_chosen else (
                        ["Shopping", "Dining", "Groceries", "Transport", "Utilities", "Wire Transfer", "ATM Withdrawal", "Entertainment"].index(preset_chosen[2])
                        if preset_chosen[2] in ["Shopping", "Dining", "Groceries", "Transport", "Utilities", "Wire Transfer", "ATM Withdrawal", "Entertainment"] else 0
                    )
                )
                tx_channel = st.selectbox(
                    "Payment Channel",
                    ["ONLINE", "POS_CHIP", "POS_SWIPE", "WIRE_TRANSFER", "ATM_WITHDRAWAL"],
                    index=0 if not preset_chosen else (
                        ["ONLINE", "POS_CHIP", "POS_SWIPE", "WIRE_TRANSFER", "ATM_WITHDRAWAL"].index(preset_chosen[3])
                    )
                )
            with f_col3:
                tx_city = st.text_input("City", value=preset_chosen[4] if preset_chosen else "New York")
                tx_country = st.text_input("Country Code (ISO-2)", value=preset_chosen[5] if preset_chosen else "US")
                tx_ip = st.text_input("Client IP", value=preset_chosen[6] if preset_chosen else "72.229.28.185")

            submit_eval = st.form_submit_button("🛡️ Execute AI Fraud Evaluation", use_container_width=True)

        if submit_eval:
            tx_payload = {
                "amount": tx_amount,
                "currency": "USD",
                "merchant_name": tx_merchant,
                "category": tx_category,
                "channel": tx_channel,
                "location_city": tx_city,
                "location_country": tx_country,
                "device_ip": tx_ip,
                "transaction_time": datetime.now(timezone.utc).isoformat(),
            }

            with st.spinner("Analyzing behavioral vectors with Gemini 3 Flash..."):
                res = fraud_engine.process_single_transaction(tx_payload)

            eval_data = res["evaluation"]
            score = eval_data["risk_score"]
            level = eval_data["risk_level"]
            action = eval_data["recommended_action"]

            st.markdown("### 🎯 Assessment Results")
            res_c1, res_c2 = st.columns([1, 2])

            with res_c1:
                # Plotly Gauge Meter
                gauge_color = "#10B981" if score < 30 else ("#F59E0B" if score < 60 else "#EF4444")
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=score,
                    title={"text": f"Risk Score: {level}"},
                    gauge={
                        "axis": {"range": [0, 100], "tickcolor": "#F8FAFC"},
                        "bar": {"color": gauge_color},
                        "steps": [
                            {"range": [0, 30], "color": "rgba(16, 185, 129, 0.2)"},
                            {"range": [30, 60], "color": "rgba(245, 158, 11, 0.2)"},
                            {"range": [60, 100], "color": "rgba(239, 68, 68, 0.2)"},
                        ],
                    }
                ))
                fig_gauge.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    height=260,
                    margin=dict(t=30, b=10, l=20, r=20)
                )
                st.plotly_chart(fig_gauge, use_container_width=True)

            with res_c2:
                # Explainable AI (XAI) Details
                st.markdown(f"**Recommended Action**: `{action}` | **Confidence**: `{eval_data['confidence_score']*100:.1f}%`")
                if eval_data["anomaly_detected"]:
                    st.error(f"⚠️ **Anomaly Flagged**: {eval_data['ai_explanation']}")
                else:
                    st.success(f"✅ **Verified Clean**: {eval_data['ai_explanation']}")

                if eval_data["triggered_indicators"]:
                    st.markdown("**Triggered Risk Indicators:**")
                    for ind in eval_data["triggered_indicators"]:
                        st.markdown(f"- 🔴 `{ind}`")

                st.caption(f"Transaction ID `{res['transaction_id']}` saved to financial ledger.")

    # --- BATCH CSV INGESTION ---
    with tab_batch:
        st.markdown("#### High-Volume Batch Transaction Triage")
        st.caption("Upload raw CSV files for automated bulk risk classification with rate-limit protection.")

        demo_csv = get_demo_csv_string()
        st.download_button(
            label="📥 Download Sample Batch CSV",
            data=demo_csv,
            file_name="omniguard_sample_transactions.csv",
            mime="text/csv",
        )

        uploaded_file = st.file_uploader("Upload Transaction CSV", type=["csv"])
        if uploaded_file is not None:
            df_upload = pd.read_csv(uploaded_file)
            st.write(f"Loaded **{len(df_upload)} transactions** ready for evaluation:")
            st.dataframe(df_upload.head(5), use_container_width=True)

            if st.button("🚀 Process Batch Evaluation"):
                progress_bar = st.progress(0.0)
                status_text = st.empty()

                def update_progress(pct, msg):
                    progress_bar.progress(pct)
                    status_text.text(msg)

                batch_results = fraud_engine.process_batch_transactions(
                    df=df_upload,
                    progress_callback=update_progress
                )

                st.success(f"Batch evaluation complete! Processed {len(batch_results)} transactions.")
                summary_rows = []
                for b in batch_results:
                    tx = b["transaction"]
                    ev = b["evaluation"]
                    summary_rows.append({
                        "Merchant": tx.get("merchant_name"),
                        "Amount": f"${tx.get('amount'):,.2f}",
                        "Channel": tx.get("channel"),
                        "Score": ev.get("risk_score"),
                        "Level": ev.get("risk_level"),
                        "Action": ev.get("recommended_action"),
                        "Explanation": ev.get("ai_explanation")[:70] + "...",
                    })
                st.dataframe(pd.DataFrame(summary_rows), use_container_width=True)


# -----------------------------------------------------------------------------
# TAB 3: WEALTH & BUDGET ADVISOR
# -----------------------------------------------------------------------------
elif nav_selection == "💡 Wealth & Budget Advisor":
    st.title("💡 Wealth & Budget Copilot")
    st.markdown("Long-context financial intelligence powered by **Gemini 3 Flash** to optimize cash-flows and accelerate goals.")

    adv_tab1, adv_tab2 = st.tabs(["📊 Financial Health & Budgeting", "💬 Conversational Copilot"])

    with adv_tab1:
        with st.spinner("Analyzing transaction ledger and computing wealth metrics..."):
            health_eval = advisory_engine.get_full_financial_evaluation()

        # Health Score Banner
        h_col1, h_col2 = st.columns([1, 2])
        with h_col1:
            fig_h = go.Figure(go.Indicator(
                mode="gauge+number",
                value=health_eval.health_score,
                title={"text": "Financial Health Index"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": "#00E5FF"},
                    "steps": [
                        {"range": [0, 50], "color": "rgba(239, 68, 68, 0.2)"},
                        {"range": [50, 75], "color": "rgba(245, 158, 11, 0.2)"},
                        {"range": [75, 100], "color": "rgba(16, 185, 129, 0.2)"},
                    ],
                }
            ))
            fig_h.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", height=240, margin=dict(t=20, b=10, l=20, r=20))
            st.plotly_chart(fig_h, use_container_width=True)

        with h_col2:
            st.markdown("### **Cash Flow Diagnostics**")
            st.info(f"**Velocity Summary**: {health_eval.cash_flow_summary}")
            st.success(f"**Emergency Buffer**: {health_eval.emergency_fund_assessment}")

        st.divider()

        # Category Spending Breakdown Chart & Table
        st.subheader("🛒 Monthly Spending Optimization Opportunities")
        c_chart, c_table = st.columns([1, 1])

        df_cat = advisory_engine.get_category_spending_df()
        with c_chart:
            if not df_cat.empty:
                fig_cat = px.bar(
                    df_cat,
                    x="amount",
                    y="category",
                    orientation="h",
                    color="amount",
                    color_continuous_scale="Viridis",
                    title="Actual 30-Day Spending Outflows ($)",
                    labels={"amount": "Total Spend ($)", "category": "Category"}
                )
                fig_cat.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=320)
                st.plotly_chart(fig_cat, use_container_width=True)

        with c_table:
            st.markdown("**AI Prescribed Budget Ceilings:**")
            for tip in health_eval.category_insights:
                with st.expander(f"📌 {tip.category}: Potential Savings ${tip.potential_monthly_savings:,.2f}/mo"):
                    st.write(f"- **Current**: `${tip.current_monthly_spend:,.2f}` | **Recommended Ceiling**: `${tip.recommended_ceiling:,.2f}`")
                    st.write(f"- **Action Tip**: {tip.optimization_tip}")

        st.divider()

        # Goals Tracking
        st.subheader("🎯 Savings Goals Progress")
        df_goals = advisory_engine.get_goals_progress_df()
        if not df_goals.empty:
            for _, g in df_goals.iterrows():
                g_col1, g_col2 = st.columns([3, 1])
                with g_col1:
                    st.markdown(f"**{g['Goal']}** (Target: `${g['Target ($)']:,.2f}` by {g['Target Date']})")
                    st.progress(float(g["Completion (%)"]) / 100.0)
                with g_col2:
                    st.metric("Funded", f"${g['Current ($)']:,.2f}", f"{g['Completion (%)']}%")

        st.subheader("📋 Top 3 Prioritized Next Steps")
        for i, step in enumerate(health_eval.actionable_steps, 1):
            st.markdown(f"**{i}.** {step}")

    # --- COPILOT CHAT ---
    with adv_tab2:
        st.markdown("#### Chat with OmniGuard Wealth Copilot")
        st.caption("Ask questions about your budget, fraud alerts, or simulation scenarios.")

        # Quick prompt suggestions
        q_col1, q_col2, q_col3 = st.columns(3)
        quick_prompt = None
        if q_col1.button("💡 How can I save $400 this month?"):
            quick_prompt = "How can I realistically save $400 this month given my current spending habits?"
        if q_col2.button("⚠️ Summarize flagged transactions"):
            quick_prompt = "Can you summarize all flagged or high-risk transactions detected on my account?"
        if q_col3.button("🎯 Emergency fund trajectory"):
            quick_prompt = "Am I on track to complete my 6-month emergency reserve this year?"

        # Display history
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        user_input = st.chat_input("Ask OmniGuard anything about your finances...") or quick_prompt

        if user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            with st.chat_message("assistant"):
                with st.spinner("OmniGuard is thinking..."):
                    reply = advisory_engine.handle_copilot_chat(
                        user_message=user_input,
                        conversation_history=st.session_state.chat_history,
                    )
                    st.markdown(reply)
            st.session_state.chat_history.append({"role": "assistant", "content": reply})


# -----------------------------------------------------------------------------
# TAB 4: TRANSACTION LEDGER & AUDIT
# -----------------------------------------------------------------------------
elif nav_selection == "📋 Transaction Ledger & Audit":
    st.title("📋 Transaction Ledger & Audit Trail")
    st.markdown("Filter, search, and triage flagged transactions with regulatory compliance audit history.")

    col_search, col_filter, col_status = st.columns([2, 1, 1])
    with col_search:
        search_query = st.text_input("🔍 Search Merchant, City, or Tx ID", value="")
    with col_filter:
        risk_filter = st.selectbox("Filter Risk Level", ["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"], index=0)
    with col_status:
        anomaly_only = st.checkbox("Show Flagged Anomalies Only", value=False)

    all_txs = db.get_transactions(limit=100, only_anomalies=anomaly_only)

    # Filter transactions
    filtered_txs = []
    for t in all_txs:
        fa = t.get("fraud_assessment") or {}
        lvl = fa.get("risk_level", "LOW")
        if risk_filter != "ALL" and lvl != risk_filter:
            continue
        if search_query:
            query = search_query.lower()
            m = t.get("merchant_name", "").lower()
            c = t.get("location_city", "").lower()
            tid = t.get("id", "").lower()
            if query not in m and query not in c and query not in tid:
                continue
        filtered_txs.append(t)

    st.caption(f"Showing **{len(filtered_txs)} transactions** matching criteria.")

    # Ledger Display Table
    table_data = []
    for t in filtered_txs:
        fa = t.get("fraud_assessment") or {}
        table_data.append({
            "Tx ID": t.get("id"),
            "Date": str(t.get("transaction_time"))[:16].replace("T", " "),
            "Merchant": t.get("merchant_name"),
            "Category": t.get("category"),
            "Amount": f"${float(t.get('amount', 0)):,.2f}",
            "Channel": t.get("channel"),
            "Location": f"{t.get('location_city', '')}, {t.get('location_country', '')}",
            "Risk Score": fa.get("risk_score", 0),
            "Risk Level": fa.get("risk_level", "LOW"),
            "Action": fa.get("recommended_action", "APPROVE"),
            "Audit Status": fa.get("resolution_status", "PENDING"),
        })

    if table_data:
        df_ledger = pd.DataFrame(table_data)
        st.dataframe(df_ledger, use_container_width=True, hide_index=True)

        # Download CSV
        csv_buffer = io.StringIO()
        df_ledger.to_csv(csv_buffer, index=False)
        st.download_button(
            label="📥 Export Filtered Ledger to CSV",
            data=csv_buffer.getvalue(),
            file_name=f"omniguard_ledger_export_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No transactions match the selected filter criteria.")

    st.divider()

    # Triage Action Sub-Panel
    st.subheader("⚖️ Anomaly Triage & Resolution")
    st.caption("Update the regulatory status of flagged transactions:")
    flagged_ids = [t["id"] for t in filtered_txs if t.get("fraud_assessment", {}).get("anomaly_detected")]

    if flagged_ids:
        t_col1, t_col2, t_col3 = st.columns([2, 1, 1])
        with t_col1:
            selected_tx_id = st.selectbox("Select Flagged Transaction ID", flagged_ids)
        with t_col2:
            new_status = st.selectbox("Resolution Decision", ["CONFIRMED_FRAUD", "FALSE_POSITIVE", "RESOLVED", "PENDING"])
        with t_col3:
            st.write("")
            st.write("")
            if st.button("Apply Decision"):
                db.update_resolution_status(selected_tx_id, new_status)
                st.success(f"Transaction `{selected_tx_id}` status updated to `{new_status}`!")
                st.rerun()
    else:
        st.caption("No flagged transactions currently in view to resolve.")


# -----------------------------------------------------------------------------
# TAB 5: DEPLOYMENT BLUEPRINT
# -----------------------------------------------------------------------------
elif nav_selection == "🚀 Deployment Blueprint":
    st.title("🚀 Free Deployment Blueprint & Checklist")
    st.markdown(r"Guide to deploying OmniGuard into production at **$0.00 cost** via GitHub & Streamlit Community Cloud.")

    st.success(r"✅ **Architecture Advantage**: Zero server maintenance, zero database fees, and zero AI hosting costs.")

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.markdown("""
        ### Step 1: GitHub Repository
        1. Create a repository on GitHub (public or private):
           ```bash
           git init
           git add .
           git commit -m "Initial OmniGuard commit"
           git branch -M main
           git remote add origin https://github.com/<username>/omniguard.git
           git push -u origin main
           ```
        2. Ensure `.streamlit/secrets.toml` is in `.gitignore` (never commit API keys!).
        """)

        st.markdown("""
        ### Step 2: Supabase (PostgreSQL) Setup
        1. Sign up for free at [supabase.com](https://supabase.com).
        2. Create a new project.
        3. Navigate to **SQL Editor** and run the DDL script from the documentation.
        4. In **Project Settings > API**, copy the `Project URL` and `anon public key`.
        """)

    with col_d2:
        st.markdown("""
        ### Step 3: Google AI Studio Key
        1. Visit [aistudio.google.com](https://aistudio.google.com) and sign in.
        2. Click **Get API key** and generate a free API key.
        3. Free tier permits up to 15 Requests Per Minute (RPM) with Gemini Flash.
        """)

        st.markdown("""
        ### Step 4: Streamlit Community Cloud
        1. Go to [share.streamlit.io](https://share.streamlit.io) and link your GitHub account.
        2. Click **Deploy an app**, selecting your repository and `app.py`.
        3. Under **Advanced settings > Secrets**, paste the following block:
        """)
        st.code("""
GEMINI_API_KEY = "AIzaSy..."
GEMINI_MODEL = "gemini-2.5-flash"
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "eyJhbGciOi..."
        """, language="toml")
