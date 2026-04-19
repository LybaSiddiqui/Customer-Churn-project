import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
from db import q, run_query, insert, check_connected, get_client
from queries import QUERIES, EXTENDED_QUERIES, SECTION_COLORS, SECTION_DESCRIPTIONS
from styles import CSS

st.set_page_config(page_title="DBMT Admin", page_icon="🗄️", layout="wide",
                   initial_sidebar_state="expanded")
st.markdown(CSS, unsafe_allow_html=True)

# ── helpers ───────────────────────────────────────────────────
def rq(qid):
    for qr in QUERIES:
        if qr["id"] == qid:
            df, _ = run_query(qr["sql"])
            return df if df is not None else pd.DataFrame()
    return pd.DataFrame()

def eq(key, **kwargs):
    sql = EXTENDED_QUERIES[key]
    for k, v in kwargs.items():
        sql = sql.replace("{" + k + "}", str(v))
    return q(sql)

def kpi(col, label, val, sub, color):
    with col:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">{label}</div>'
                    f'<div class="kpi-value" style="color:{color}">{val}</div>'
                    f'<div class="kpi-sub">{sub}</div></div>', unsafe_allow_html=True)

def badge(txt):
    st.markdown(f'<div class="query-badge">⚡ {txt}</div>', unsafe_allow_html=True)

def chart_theme():
    return dict(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0,r=0,t=40,b=0))

SEG_COLORS = {
    "VIP Loyalists":"#a78bfa","High Value":"#10b981","Regular Customers":"#3b82f6",
    "Medium Value":"#22d3ee","At Risk":"#f59e0b","Dormant / No Purchases":"#ef4444"
}
SEG_LIST = list(SEG_COLORS.keys())

# ── sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🗄️ DBMT Admin")
    st.caption("Customer Segmentation System · v2.0")
    st.divider()
    if check_connected():
        st.success("✅ Supabase connected", icon="🟢")
    else:
        st.error("❌ Not connected")
        st.info("Check `.streamlit/secrets.toml`")
    st.divider()
    st.markdown("**SQL Query filters**")
    section_filter = st.selectbox("Section", ["All","Basic","Intermediate","Advanced"])
    search = st.text_input("Search queries", placeholder="e.g. revenue, JOIN…")
    st.divider()
    for sec, color in SECTION_COLORS.items():
        count = sum(1 for qr in QUERIES if qr["section"] == sec)
        st.markdown(f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">'
                    f'<div style="width:9px;height:9px;border-radius:50%;background:{color}"></div>'
                    f'<span style="font-size:13px">{sec}</span>'
                    f'<span style="margin-left:auto;font-size:12px;color:#8fa3bd">{count}</span></div>',
                    unsafe_allow_html=True)
    st.divider()
    st.caption("Team 7 · Uvashree · Mashiat · Lyba · Ranjitha · Hamza")

# ── tabs ──────────────────────────────────────────────────────
(tab_ov, tab_cu, tab_pr, tab_ch,
 tab_pe, tab_ce, tab_ins, tab_dm, tab_sq) = st.tabs([
    "📊 Overview", "👥 Customers", "📦 Products", "⚠️ Churn Risk",
    "🔎 Product Explorer", "👤 Customer Explorer",
    "📈 Insights", "➕ Data Management", "🔍 SQL Queries"
])

# ══════════════════════════════════════════════════════════════
# OVERVIEW — Q6, Q9, Q11
# ══════════════════════════════════════════════════════════════
with tab_ov:
    st.markdown("## Overview")
    st.caption("Real-time metrics across your entire customer base")

    with st.spinner("Loading overview…"):
        df_bm      = rq(6)
        df_cat_rev = rq(9)
        df_segs    = rq(11)
        df_tc      = q("SELECT COUNT(*) AS v FROM customers")
        df_cc      = q("SELECT COUNT(*) AS v FROM behavioral_metrics WHERE recencyofpurchase>180 AND purchasefrequency>=2")
        df_hv      = q("SELECT COUNT(*) AS v FROM segmentation_results WHERE segmentlabel IN ('High Value','VIP Loyalists')")
        df_monthly = eq("monthly_revenue_all")
        df_new_c   = eq("new_customers_monthly")

    tc  = int(df_tc["v"].iloc[0])   if not df_tc.empty  else 0
    tr  = float(df_cat_rev["totalrevenue"].astype(float).sum()) if not df_cat_rev.empty else 0
    av  = float(df_bm["averagespending"].astype(float).mean())  if not df_bm.empty      else 0
    cc  = int(df_cc["v"].iloc[0])   if not df_cc.empty  else 0
    hv  = int(df_hv["v"].iloc[0])   if not df_hv.empty  else 0
    ret = round((tc-cc)/tc*100,1)   if tc else 0

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    kpi(c1,"Total customers",   f"{tc:,}",          "",                       "#3b82f6")
    kpi(c2,"Total revenue",     f"${tr/1000:.1f}k", f"${tr/tc:.0f}/customer", "#10b981")
    kpi(c3,"Avg spend",         f"${av:.0f}",        "per active customer",    "#3b82f6")
    kpi(c4,"Churn risk",        f"{cc:,}",           "inactive 180+ days",    "#f59e0b")
    kpi(c5,"High-value",        f"{hv:,}",           "VIP + High segments",   "#a78bfa")
    kpi(c6,"Retention",         f"{ret}%",           "non-churned base",      "#10b981" if ret>80 else "#f59e0b")

    st.markdown("")
    cl, cr = st.columns([3,2])
    with cl:
        badge("Monthly revenue trend — all transactions aggregated")
        if not df_monthly.empty:
            df_monthly["revenue"] = pd.to_numeric(df_monthly["revenue"])
            df_monthly["active_customers"] = pd.to_numeric(df_monthly["active_customers"])
            df_monthly = df_monthly.sort_values("month")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_monthly["month"], y=df_monthly["revenue"],
                                     fill="tozeroy", name="Revenue", line=dict(color="#3b82f6",width=2)))
            fig.update_layout(title="Monthly revenue", height=280, **chart_theme())
            fig.update_yaxes(gridcolor="#1e293b", tickprefix="$")
            fig.update_xaxes(showgrid=False)
            st.plotly_chart(fig, use_container_width=True)

    with cr:
        badge("Q11 — segment distribution")
        if not df_segs.empty:
            df_segs["customercount"] = pd.to_numeric(df_segs["customercount"])
            fig = px.pie(df_segs, names="segmentlabel", values="customercount",
                         title="Customer segments", hole=0.55,
                         color="segmentlabel",
                         color_discrete_map=SEG_COLORS)
            fig.update_layout(height=280, **chart_theme())
            st.plotly_chart(fig, use_container_width=True)

    # new customers growth
    st.markdown("### New customer registrations over time")
    badge("customers.registrationdate aggregated monthly")
    if not df_new_c.empty:
        df_new_c["new_customers"] = pd.to_numeric(df_new_c["new_customers"])
        df_new_c = df_new_c.sort_values("month")
        fig = px.bar(df_new_c, x="month", y="new_customers",
                     title="New customers per month",
                     color_discrete_sequence=["#10b981"])
        fig.update_layout(height=260, **chart_theme())
        fig.update_yaxes(gridcolor="#1e293b")
        fig.update_xaxes(showgrid=False)
        st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# CUSTOMERS — Q7, Q11, Q17
# ══════════════════════════════════════════════════════════════
with tab_cu:
    st.markdown("## Customer statistics")
    st.caption("Demographics, segments, and behavioral breakdown")

    with st.spinner("Loading…"):
        df_segs  = rq(11)
        df_cprof = rq(17)
        df_age   = q("""
            SELECT CASE WHEN age<=25 THEN '18-25' WHEN age<=35 THEN '26-35'
                        WHEN age<=45 THEN '36-45' WHEN age<=55 THEN '46-55'
                        WHEN age<=65 THEN '56-65' ELSE '65+' END AS agegroup,
                   COUNT(*) AS cnt FROM customers GROUP BY agegroup ORDER BY agegroup
        """)
        df_gen  = q("SELECT gender, COUNT(*) AS cnt FROM customers GROUP BY gender")
        df_freq = eq("repeat_vs_onetime")

    badge("Q11 — segment statistics")
    if not df_segs.empty:
        cols = st.columns(min(len(df_segs), 6))
        for i, row in df_segs.iterrows():
            color = SEG_COLORS.get(row["segmentlabel"], "#3b82f6")
            with cols[i % len(cols)]:
                st.markdown(f'<div class="kpi-card">'
                            f'<div class="kpi-label">{row["segmentlabel"]}</div>'
                            f'<div class="kpi-value" style="color:{color}">{int(row["customercount"]):,}</div>'
                            f'<div class="kpi-sub">Avg ${float(row["avgspending"]):.0f} · {float(row["avgfrequency"]):.1f}× freq</div>'
                            f'</div>', unsafe_allow_html=True)

    st.markdown("")
    ca, cg = st.columns([3,2])
    with ca:
        badge("Q7 — customers table age distribution")
        if not df_age.empty:
            df_age["cnt"] = pd.to_numeric(df_age["cnt"])
            fig = px.bar(df_age, x="agegroup", y="cnt", title="Age distribution",
                         color="agegroup", color_discrete_sequence=px.colors.sequential.Blues_r)
            fig.update_layout(height=280, showlegend=False, **chart_theme())
            fig.update_yaxes(gridcolor="#1e293b")
            st.plotly_chart(fig, use_container_width=True)
    with cg:
        if not df_gen.empty:
            df_gen["cnt"] = pd.to_numeric(df_gen["cnt"])
            fig = px.pie(df_gen, names="gender", values="cnt", title="Gender split",
                         hole=0.55, color_discrete_sequence=["#3b82f6","#a78bfa","#22d3ee"])
            fig.update_layout(height=280, **chart_theme())
            st.plotly_chart(fig, use_container_width=True)

    # purchase frequency breakdown
    st.markdown("### Purchase frequency breakdown")
    badge("Derived from transactions — buyer loyalty tiers")
    if not df_freq.empty:
        df_freq["customers"] = pd.to_numeric(df_freq["customers"])
        fig = px.bar(df_freq, x="buyer_type", y="customers", color="buyer_type",
                     title="Buyer loyalty tiers",
                     color_discrete_sequence=["#ef4444","#f59e0b","#3b82f6","#10b981"])
        fig.update_layout(height=260, showlegend=False, **chart_theme())
        fig.update_yaxes(gridcolor="#1e293b")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Segment comparison table")
    badge("Q11 — full breakdown")
    if not df_segs.empty:
        df_segs["customercount"] = pd.to_numeric(df_segs["customercount"])
        tot = df_segs["customercount"].sum()
        df_segs["Share %"] = (df_segs["customercount"]/tot*100).round(1).astype(str)+"%"
        df_segs["Est. Total Value"] = (
            df_segs["customercount"]*pd.to_numeric(df_segs["avgspending"])
        ).round(0).apply(lambda x: f"${x:,.0f}")
        st.dataframe(df_segs.rename(columns={"segmentlabel":"Segment","customercount":"Customers",
                                              "avgspending":"Avg Spend","avgfrequency":"Avg Freq"}),
                     use_container_width=True, hide_index=True)

    st.markdown("### Customer profile sample")
    badge("Q17 — customers joined with segmentation_results")
    if not df_cprof.empty:
        st.dataframe(df_cprof.head(15), use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════
# PRODUCTS — Q9, Q13, Q20
# ══════════════════════════════════════════════════════════════
with tab_pr:
    st.markdown("## Product performance")
    st.caption("Revenue, units sold, and segment preferences")

    with st.spinner("Loading…"):
        df_cat  = rq(9)
        df_top5 = rq(13)
        df_best = rq(20)
        df_heat = eq("category_segment_heatmap")

    ct, cc2 = st.columns([3,2])
    with ct:
        badge("Q13 — top 5 products by units sold")
        if not df_top5.empty:
            df_top5["totalsold"] = pd.to_numeric(df_top5["totalsold"])
            fig = px.bar(df_top5, x="totalsold", y="productname", orientation="h",
                         color="totalsold", title="Top 5 products by units sold",
                         color_continuous_scale="Blues")
            fig.update_layout(height=280, showlegend=False,
                              yaxis=dict(categoryorder="total ascending"), **chart_theme())
            fig.update_xaxes(gridcolor="#1e293b")
            st.plotly_chart(fig, use_container_width=True)

    with cc2:
        badge("Q9 — revenue by category")
        if not df_cat.empty:
            df_cat["totalrevenue"] = pd.to_numeric(df_cat["totalrevenue"])
            fig = px.pie(df_cat, names="category", values="totalrevenue",
                         title="Revenue by category", hole=0.55,
                         color_discrete_sequence=["#3b82f6","#10b981","#a78bfa","#22d3ee","#f59e0b","#ef4444"])
            fig.update_layout(height=280, **chart_theme())
            st.plotly_chart(fig, use_container_width=True)

    # segment × category heatmap
    st.markdown("### Which segments buy which categories")
    badge("Extended — transactions × products × segmentation_results cross-join")
    if not df_heat.empty:
        df_heat["revenue"] = pd.to_numeric(df_heat["revenue"])
        pivot = df_heat.pivot_table(index="segmentlabel", columns="category",
                                    values="revenue", aggfunc="sum", fill_value=0)
        fig = px.imshow(pivot, color_continuous_scale="Blues",
                        title="Revenue heatmap: segment × category",
                        aspect="auto")
        fig.update_layout(height=340, **chart_theme())
        st.plotly_chart(fig, use_container_width=True)

    ct2, cb2 = st.columns(2)
    with ct2:
        st.markdown("### ✅ Top 5 by units (Q13)")
        if not df_top5.empty:
            st.dataframe(df_top5.rename(columns={"productname":"Product",
                                                  "category":"Category","totalsold":"Units Sold"}),
                         use_container_width=True, hide_index=True)
    with cb2:
        st.markdown("### 🏆 Best per category (Q20)")
        badge("Q20")
        if not df_best.empty:
            df_best["totalrevenue"] = pd.to_numeric(df_best["totalrevenue"]).apply(lambda x: f"${x:,.0f}")
            st.dataframe(df_best.rename(columns={"category":"Category","productname":"Product",
                                                  "totalrevenue":"Revenue","totalunitssold":"Units"}),
                         use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════
# CHURN RISK — Q12, Q14, Q21
# ══════════════════════════════════════════════════════════════
with tab_ch:
    st.markdown("## Churn risk")
    st.caption("Identify, prioritize, and act on at-risk customers")

    with st.spinner("Loading…"):
        df_rfm   = rq(14)
        df_above = rq(12)
        df_ltv   = rq(21)
        df_cl    = q("""
            SELECT c.customerid, c.firstname||' '||c.lastname AS fullname,
                   c.email, s.segmentlabel,
                   bm.recencyofpurchase, bm.purchasefrequency, bm.averagespending
            FROM behavioral_metrics bm
            JOIN customers c            ON bm.customerid=c.customerid
            JOIN segmentation_results s ON bm.customerid=s.customerid
            WHERE bm.recencyofpurchase>180 AND bm.purchasefrequency>=2
            ORDER BY bm.recencyofpurchase DESC LIMIT 300
        """)

    if not df_cl.empty:
        for col in ["recencyofpurchase","purchasefrequency","averagespending"]:
            df_cl[col] = pd.to_numeric(df_cl[col])

        def rscore(r):
            return round(min(r["recencyofpurchase"]/365,1)*50
                         + max(0,(7-r["purchasefrequency"])/7)*30
                         + (20 if r["averagespending"]>1000 else 10 if r["averagespending"]>500 else 0))
        df_cl["risk_score"] = df_cl.apply(rscore, axis=1)
        df_cl["risk_level"] = df_cl["risk_score"].apply(
            lambda s: "Critical" if s>=75 else "High" if s>=50 else "Medium")

        crit=len(df_cl[df_cl["risk_level"]=="Critical"])
        high=len(df_cl[df_cl["risk_level"]=="High"])
        med =len(df_cl[df_cl["risk_level"]=="Medium"])
        avgd=int(df_cl["recencyofpurchase"].mean())
        est_loss = df_cl["averagespending"].sum()

        k1,k2,k3,k4,k5 = st.columns(5)
        kpi(k1,"Total at-risk",     len(df_cl),        "",               "#f59e0b")
        kpi(k2,"Critical (≥75)",    crit,              "immediate action","#ef4444")
        kpi(k3,"High (50–74)",      high,              "watch closely",  "#f59e0b")
        kpi(k4,"Avg days inactive", f"{avgd}d",        "",               "#8fa3bd")
        kpi(k5,"Est. revenue at risk", f"${est_loss/1000:.0f}k","avg spend × at-risk","#ef4444")

        st.markdown("")

        # RFM scatter
        st.markdown("### RFM score distribution")
        badge("Q14 — NTILE window functions across Recency, Frequency, Monetary")
        if not df_rfm.empty:
            for col in ["averagespending","purchasefrequency","rfm_score"]:
                df_rfm[col] = pd.to_numeric(df_rfm[col])
            fig = px.scatter(df_rfm, x="averagespending", y="purchasefrequency",
                             color="rfm_score", size="rfm_score",
                             hover_data=["fullname","segmentlabel"],
                             title="RFM map — low score = higher churn risk",
                             color_continuous_scale="RdYlGn")
            fig.update_layout(height=360, **chart_theme())
            st.plotly_chart(fig, use_container_width=True)

        # filter + table
        fl,sl,_ = st.columns([2,2,4])
        with fl: lf = st.selectbox("Filter level",["All","Critical","High","Medium"])
        with sl: sb = st.selectbox("Sort by",["Days inactive","Risk score","Avg spend"])

        df_show = df_cl.copy()
        if lf!="All": df_show=df_show[df_show["risk_level"]==lf]
        sc={"Days inactive":"recencyofpurchase","Risk score":"risk_score","Avg spend":"averagespending"}[sb]
        df_show=df_show.sort_values(sc,ascending=False)
        st.caption(f"Showing {len(df_show)} customers")

        disp=df_show.copy()
        disp["averagespending"]=disp["averagespending"].apply(lambda x:f"${x:.0f}")
        disp["recencyofpurchase"]=disp["recencyofpurchase"].astype(str)+"d"
        st.dataframe(disp.rename(columns={"customerid":"ID","fullname":"Customer",
                                           "segmentlabel":"Segment","recencyofpurchase":"Days Inactive",
                                           "purchasefrequency":"Purchases","averagespending":"Avg Spend",
                                           "risk_score":"Score","risk_level":"Level","email":"Email"}),
                     use_container_width=True,height=380,hide_index=True)

        # Q21 LTV priority
        st.markdown("### High-LTV customers to prioritize for re-engagement")
        badge("Q21 — CTE lifetime value × churn risk cross-reference")
        if not df_ltv.empty:
            df_ltv["customerid"] = pd.to_numeric(df_ltv["customerid"], errors="coerce")
            df_cl["customerid"]  = pd.to_numeric(df_cl["customerid"],  errors="coerce")
            at_risk = set(df_cl["customerid"].tolist())
            df_ltv_risk = df_ltv[df_ltv["customerid"].isin(at_risk)].copy()
            if not df_ltv_risk.empty:
                df_ltv_risk["lifetimevalue"]=pd.to_numeric(df_ltv_risk["lifetimevalue"]).apply(lambda x:f"${x:,.0f}")
                st.dataframe(df_ltv_risk[["customerid","customername","totalorders",
                                           "lifetimevalue","dayssincelastorder","segmentlabel"]].rename(
                    columns={"customerid":"ID","customername":"Customer","totalorders":"Orders",
                             "lifetimevalue":"LTV","dayssincelastorder":"Days Since Last","segmentlabel":"Segment"}
                ), use_container_width=True, hide_index=True)
            else:
                st.info("No LTV data overlaps current churn risk customers — try increasing LIMIT in Q21 in queries.py")

# ══════════════════════════════════════════════════════════════
# PRODUCT EXPLORER
# ══════════════════════════════════════════════════════════════
with tab_pe:
    st.markdown("## Product Explorer")
    st.caption("Search any product — see monthly performance, buyers, and segment preferences")

    search_term = st.text_input("🔍 Search product by name or category",
                                placeholder="e.g. Product_42, Electronics, Books…",
                                key="prod_search")

    if search_term.strip():
        with st.spinner(f"Searching for '{search_term}'…"):
            df_results = eq("product_search", term=search_term)

        if df_results.empty:
            st.warning(f"No products found matching '{search_term}'")
        else:
            df_results["totalrevenue"] = pd.to_numeric(df_results["totalrevenue"])
            df_results["unitssold"]    = pd.to_numeric(df_results["unitssold"])

            st.markdown(f"### {len(df_results)} product(s) found")
            sel_col = st.columns([3,1])
            with sel_col[0]:
                selected_product = st.selectbox(
                    "Select a product for detailed analysis",
                    df_results["productname"].tolist()
                )

            if selected_product:
                row = df_results[df_results["productname"]==selected_product].iloc[0]

                # KPIs
                p1,p2,p3,p4 = st.columns(4)
                kpi(p1,"Category",      row["category"],                   "",                     "#3b82f6")
                kpi(p2,"Total revenue", f"${float(row['totalrevenue']):,.0f}", "all time",          "#10b981")
                kpi(p3,"Units sold",    f"{int(row['unitssold']):,}",       "all time",             "#a78bfa")
                kpi(p4,"Unique buyers", f"{int(row['uniquebuyers']):,}",    "distinct customers",   "#f59e0b")

                st.markdown("")

                with st.spinner("Loading product details…"):
                    df_monthly_p = eq("product_monthly",  name=selected_product)
                    df_buyers    = eq("product_buyers",    name=selected_product)
                    df_by_seg    = eq("product_by_segment",name=selected_product)

                pm1, pm2 = st.columns([3,2])
                with pm1:
                    st.markdown(f"### Monthly performance — {selected_product}")
                    badge("Extended Q — transactions grouped by month for selected product")
                    if not df_monthly_p.empty:
                        df_monthly_p["revenue"] = pd.to_numeric(df_monthly_p["revenue"])
                        df_monthly_p["units"]   = pd.to_numeric(df_monthly_p["units"])
                        fig = go.Figure()
                        fig.add_trace(go.Bar(x=df_monthly_p["month"], y=df_monthly_p["revenue"],
                                             name="Revenue", marker_color="#3b82f6", yaxis="y"))
                        fig.add_trace(go.Scatter(x=df_monthly_p["month"], y=df_monthly_p["units"],
                                                 name="Units", line=dict(color="#10b981",width=2),
                                                 yaxis="y2", mode="lines+markers"))
                        fig.update_layout(
                            height=320, title="Revenue & units by month",
                            yaxis=dict(title="Revenue ($)", gridcolor="#1e293b", tickprefix="$"),
                            yaxis2=dict(title="Units", overlaying="y", side="right"),
                            legend=dict(orientation="h", y=1.1), **chart_theme()
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No transaction data found for this product.")

                with pm2:
                    st.markdown("### Sales by customer segment")
                    badge("Extended Q — product × segmentation_results cross-join")
                    if not df_by_seg.empty:
                        df_by_seg["revenue"] = pd.to_numeric(df_by_seg["revenue"])
                        df_by_seg["buyers"]  = pd.to_numeric(df_by_seg["buyers"])
                        fig = px.bar(df_by_seg, x="segmentlabel", y="revenue",
                                     color="segmentlabel", title="Revenue by segment",
                                     color_discrete_map=SEG_COLORS)
                        fig.update_layout(height=180, showlegend=False, **chart_theme())
                        fig.update_yaxes(gridcolor="#1e293b", tickprefix="$")
                        st.plotly_chart(fig, use_container_width=True)

                        st.dataframe(df_by_seg.rename(columns={
                            "segmentlabel":"Segment","buyers":"Buyers",
                            "revenue":"Revenue","units":"Units"
                        }), use_container_width=True, hide_index=True)
                    else:
                        st.info("No segment data available.")

                # who bought it
                st.markdown(f"### Customers who bought {selected_product}")
                badge("Extended Q — transactions filtered by product, joined with customers + segmentation")
                if not df_buyers.empty:
                    df_buyers["totalspent"] = pd.to_numeric(df_buyers["totalspent"]).apply(lambda x:f"${x:,.0f}")
                    st.dataframe(df_buyers.rename(columns={
                        "customerid":"ID","customername":"Customer","email":"Email",
                        "segmentlabel":"Segment","totalspent":"Spent",
                        "unitsbought":"Units","orders":"Orders","lastpurchase":"Last Purchase"
                    }), use_container_width=True, height=340, hide_index=True)
                else:
                    st.info("No buyer data found.")

        # product list
        st.markdown("### All matching products")
        df_results_show = df_results.copy()
        df_results_show["totalrevenue"] = df_results_show["totalrevenue"].apply(lambda x:f"${x:,.0f}")
        st.dataframe(df_results_show.rename(columns={
            "productid":"ID","productname":"Product","category":"Category","price":"Price",
            "totalrevenue":"Revenue","unitssold":"Units","uniquebuyers":"Buyers"
        }), use_container_width=True, hide_index=True)
    else:
        st.info("👆 Type a product name or category above to start exploring.")
        # show quick stats
        st.markdown("### Quick product summary")
        df_all_cat = rq(9)
        if not df_all_cat.empty:
            df_all_cat["totalrevenue"] = pd.to_numeric(df_all_cat["totalrevenue"])
            fig = px.bar(df_all_cat, x="category", y="totalrevenue", color="category",
                         title="Revenue by category — click a bar then search that category",
                         color_discrete_sequence=px.colors.qualitative.Bold)
            fig.update_layout(height=300, showlegend=False, **chart_theme())
            fig.update_yaxes(gridcolor="#1e293b", tickprefix="$")
            st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# CUSTOMER EXPLORER
# ══════════════════════════════════════════════════════════════
with tab_ce:
    st.markdown("## Customer Explorer")
    st.caption("Look up any customer — transactions, RFM profile, spending breakdown")

    cust_search = st.text_input("🔍 Search by name or email",
                                placeholder="e.g. Sarah Brown, david.garcia…",
                                key="cust_search")

    if cust_search.strip():
        with st.spinner(f"Searching for '{cust_search}'…"):
            df_cres = eq("customer_search", term=cust_search)

        if df_cres.empty:
            st.warning(f"No customers found matching '{cust_search}'")
        else:
            selected_cust = st.selectbox(
                "Select a customer",
                df_cres["fullname"].tolist(),
                key="cust_select"
            )
            if selected_cust:
                crow = df_cres[df_cres["fullname"]==selected_cust].iloc[0]
                cid  = int(crow["customerid"])

                # profile card
                seg_color = SEG_COLORS.get(str(crow.get("segmentlabel","")), "#3b82f6")
                st.markdown(f"""
                <div class="profile-card">
                  <div class="profile-name">{crow['fullname']}</div>
                  <div class="profile-sub">Customer #{cid} ·
                    <span style="color:{seg_color};font-weight:600">{crow.get('segmentlabel','—')}</span>
                  </div>
                  <div class="profile-row">
                    <div class="profile-item"><span>Email: </span>{crow.get('email','—')}</div>
                    <div class="profile-item"><span>Phone: </span>{crow.get('phone','—')}</div>
                    <div class="profile-item"><span>Age: </span>{crow.get('age','—')}</div>
                    <div class="profile-item"><span>Gender: </span>{crow.get('gender','—')}</div>
                    <div class="profile-item"><span>Registered: </span>{crow.get('registrationdate','—')}</div>
                  </div>
                </div>""", unsafe_allow_html=True)

                with st.spinner("Loading customer data…"):
                    df_txns   = eq("customer_transactions",   cid=cid)
                    df_cat_sp = eq("customer_category_spend", cid=cid)
                    df_rfm_c  = eq("customer_rfm",            cid=cid)

                # behavioral KPIs
                if not df_rfm_c.empty:
                    r = df_rfm_c.iloc[0]
                    b1,b2,b3 = st.columns(3)
                    kpi(b1,"Purchase frequency",f"{r['purchasefrequency']}×",  "total orders",         "#3b82f6")
                    kpi(b2,"Avg spend",         f"${float(r['averagespending']):.0f}", "per transaction","#10b981")
                    kpi(b3,"Days since purchase",f"{r['recencyofpurchase']}d", "last transaction",     "#f59e0b" if int(r['recencyofpurchase'])>90 else "#10b981")

                st.markdown("")
                tx_col, cat_col = st.columns([3,2])

                with tx_col:
                    st.markdown("### Transaction history")
                    badge(f"Extended Q — transactions for customer #{cid} with cumulative spend window function")
                    if not df_txns.empty:
                        df_txns["totalamount"]    = pd.to_numeric(df_txns["totalamount"])
                        df_txns["cumulativespend"]= pd.to_numeric(df_txns["cumulativespend"])

                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=df_txns["transactiondate"],
                            y=df_txns["cumulativespend"],
                            fill="tozeroy", name="Cumulative spend",
                            line=dict(color="#3b82f6", width=2)
                        ))
                        fig.update_layout(title="Cumulative spend over time", height=240, **chart_theme())
                        fig.update_yaxes(gridcolor="#1e293b", tickprefix="$")
                        st.plotly_chart(fig, use_container_width=True)

                        disp = df_txns[["transactionid","transactiondate","productname",
                                        "category","quantity","totalamount","cumulativespend"]].copy()
                        disp["totalamount"]     = disp["totalamount"].apply(lambda x:f"${x:.2f}")
                        disp["cumulativespend"] = disp["cumulativespend"].apply(lambda x:f"${x:.2f}")
                        st.dataframe(disp.rename(columns={
                            "transactionid":"Tx ID","transactiondate":"Date",
                            "productname":"Product","category":"Category",
                            "quantity":"Qty","totalamount":"Amount","cumulativespend":"Cumulative"
                        }), use_container_width=True, height=280, hide_index=True)
                    else:
                        st.info("No transactions found for this customer.")

                with cat_col:
                    st.markdown("### Spending by category")
                    badge(f"Extended Q — category preferences for customer #{cid}")
                    if not df_cat_sp.empty:
                        df_cat_sp["spent"] = pd.to_numeric(df_cat_sp["spent"])
                        fig = px.pie(df_cat_sp, names="category", values="spent",
                                     title="Spend breakdown", hole=0.5,
                                     color_discrete_sequence=["#3b82f6","#10b981","#a78bfa","#22d3ee","#f59e0b","#ef4444"])
                        fig.update_layout(height=260, **chart_theme())
                        st.plotly_chart(fig, use_container_width=True)

                        df_cat_sp["spent"] = df_cat_sp["spent"].apply(lambda x:f"${x:,.0f}")
                        st.dataframe(df_cat_sp.rename(columns={"category":"Category",
                                                                "spent":"Spent","units":"Units"}),
                                     use_container_width=True, hide_index=True)
    else:
        st.info("👆 Type a customer name or email above to look them up.")

# ══════════════════════════════════════════════════════════════
# INSIGHTS
# ══════════════════════════════════════════════════════════════
with tab_ins:
    st.markdown("## Business Insights")
    st.caption("Advanced analytics beyond the standard metrics")

    with st.spinner("Loading insights…"):
        df_rev_seg  = eq("revenue_per_segment_monthly")
        df_top_cust = eq("top_customers_overall")
        df_days_btw = eq("avg_days_between_purchases")
        df_monthly  = eq("monthly_revenue_all")

    # revenue per segment over time
    st.markdown("### Revenue per segment over time")
    badge("Extended Q — transactions × segmentation grouped by month and segment")
    if not df_rev_seg.empty:
        df_rev_seg["revenue"] = pd.to_numeric(df_rev_seg["revenue"])
        fig = px.line(df_rev_seg, x="month", y="revenue", color="segmentlabel",
                      title="Monthly revenue by customer segment",
                      color_discrete_map=SEG_COLORS)
        fig.update_layout(height=340, **chart_theme())
        fig.update_yaxes(gridcolor="#1e293b", tickprefix="$")
        fig.update_xaxes(showgrid=False)
        st.plotly_chart(fig, use_container_width=True)

    ins1, ins2 = st.columns(2)

    with ins1:
        st.markdown("### 🏆 Top 20 customers by lifetime value")
        badge("Extended Q — CTE: SUM(totalamount) per customer joined with segmentation")
        if not df_top_cust.empty:
            df_top_cust["lifetime_value"] = pd.to_numeric(df_top_cust["lifetime_value"]).apply(lambda x:f"${x:,.0f}")
            df_top_cust["avg_order"]      = pd.to_numeric(df_top_cust["avg_order"]).apply(lambda x:f"${x:.0f}")
            st.dataframe(df_top_cust.rename(columns={
                "customerid":"ID","fullname":"Customer","segmentlabel":"Segment",
                "orders":"Orders","lifetime_value":"LTV","avg_order":"Avg Order",
                "last_purchase":"Last Purchase"
            }), use_container_width=True, height=420, hide_index=True)

    with ins2:
        st.markdown("### ⏱️ Avg days between purchases — loyal customers")
        badge("Extended Q — date arithmetic: (MAX-MIN) / (count-1) grouped per customer")
        if not df_days_btw.empty:
            df_days_btw["avg_days_between_orders"] = pd.to_numeric(df_days_btw["avg_days_between_orders"])
            fig = px.histogram(df_days_btw, x="avg_days_between_orders",
                               nbins=20, title="Purchase cadence distribution",
                               color_discrete_sequence=["#3b82f6"])
            fig.update_layout(height=240, **chart_theme())
            fig.update_yaxes(gridcolor="#1e293b")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df_days_btw.head(15).rename(columns={
                "customerid":"ID","fullname":"Customer","segmentlabel":"Segment",
                "orders":"Orders","avg_days_between_orders":"Avg Days Between Orders"
            }), use_container_width=True, height=200, hide_index=True)

    # MoM growth
    st.markdown("### Month-over-month revenue growth")
    badge("Extended Q — monthly_revenue_all with LAG-derived growth %")
    if not df_monthly.empty:
        df_monthly["revenue"] = pd.to_numeric(df_monthly["revenue"])
        df_monthly["orders"]  = pd.to_numeric(df_monthly["orders"])
        df_monthly = df_monthly.sort_values("month")
        df_monthly["mom_growth"] = df_monthly["revenue"].pct_change()*100
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_monthly["month"],
            y=df_monthly["mom_growth"],
            marker_color=["#10b981" if x>=0 else "#ef4444" for x in df_monthly["mom_growth"].fillna(0)],
            name="MoM Growth %"
        ))
        fig.add_hline(y=0, line_dash="dash", line_color="#475569")
        fig.update_layout(title="Month-over-month revenue growth (%)", height=260, **chart_theme())
        fig.update_yaxes(gridcolor="#1e293b", ticksuffix="%")
        st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# DATA MANAGEMENT
# ══════════════════════════════════════════════════════════════
with tab_dm:
    st.markdown("## Data Management")
    st.caption("Add new records directly to the database from this interface")

    dm1, dm2 = st.tabs(["➕ Add product", "👤 Add customer"])

    with dm1:
        st.markdown("### Add a new product")
        st.caption("Fill in all fields — data is validated before insertion")

        with st.form("add_product_form", clear_on_submit=True):
            pc1, pc2 = st.columns(2)
            with pc1:
                p_name     = st.text_input("Product name *", placeholder="Product_501")
                p_category = st.selectbox("Category *",
                    ["Books","Sports","Electronics","Beauty","Home","Clothing","Other"])
            with pc2:
                p_price = st.number_input("Price ($) *", min_value=0.01, max_value=9999.99,
                                          value=99.99, step=0.01)

            st.markdown("")
            submitted = st.form_submit_button("💾 Add product to database",
                                              type="primary", use_container_width=True)

            if submitted:
                if not p_name.strip():
                    st.error("Product name is required.")
                elif p_price <= 0:
                    st.error("Price must be greater than $0.")
                else:
                    ok, err = insert("products", {
                        "productname": p_name.strip(),
                        "category":    p_category,
                        "price":       round(p_price, 2)
                    })
                    if ok:
                        st.success(f"✅ '{p_name}' added successfully to the Products table!")
                        st.balloons()
                    else:
                        st.error(f"❌ Insert failed: {err}")

        # preview recent products
        st.markdown("### Recently added products")
        df_recent_p = q("SELECT productid, productname, category, price FROM products ORDER BY productid DESC LIMIT 10")
        if not df_recent_p.empty:
            st.dataframe(df_recent_p, use_container_width=True, hide_index=True)

    with dm2:
        st.markdown("### Add a new customer")
        st.caption("All fields are required — email must be unique")

        with st.form("add_customer_form", clear_on_submit=True):
            cc1, cc2 = st.columns(2)
            with cc1:
                c_first = st.text_input("First name *", placeholder="Sarah")
                c_last  = st.text_input("Last name *",  placeholder="Brown")
                c_email = st.text_input("Email *",      placeholder="sarah@example.com")
                c_phone = st.text_input("Phone",        placeholder="9773957037")
            with cc2:
                c_age    = st.number_input("Age *",     min_value=18, max_value=100, value=30)
                c_gender = st.selectbox("Gender *",     ["Male","Female","Other","Prefer not to say"])
                c_regdate= st.date_input("Registration date *", value=date.today())

            st.markdown("")
            sub2 = st.form_submit_button("💾 Add customer to database",
                                         type="primary", use_container_width=True)

            if sub2:
                if not c_first.strip() or not c_last.strip():
                    st.error("First and last name are required.")
                elif not c_email.strip() or "@" not in c_email:
                    st.error("A valid email address is required.")
                else:
                    ok, err = insert("customers", {
                        "firstname":        c_first.strip(),
                        "lastname":         c_last.strip(),
                        "age":              int(c_age),
                        "gender":           c_gender,
                        "email":            c_email.strip().lower(),
                        "phone":            c_phone.strip(),
                        "registrationdate": str(c_regdate),
                    })
                    if ok:
                        st.success(f"✅ {c_first} {c_last} added to the Customers table!")
                        st.balloons()
                    else:
                        st.error(f"❌ Insert failed: {err}")

        st.markdown("### Recently added customers")
        df_recent_c = q("""SELECT customerid, firstname||' '||lastname AS name,
                                  email, gender, age, registrationdate
                           FROM customers ORDER BY customerid DESC LIMIT 10""")
        if not df_recent_c.empty:
            st.dataframe(df_recent_c, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════
# SQL QUERIES
# ══════════════════════════════════════════════════════════════
with tab_sq:
    st.markdown("## SQL Query Explorer")
    st.caption("All 25 original queries — same SQL powering the dashboard above")

    USED_IN = {
        6:["Overview"], 9:["Overview","Products"], 11:["Overview","Customers"],
        7:["Customers"], 17:["Customers"], 12:["Churn Risk"], 14:["Churn Risk"],
        21:["Churn Risk"], 13:["Products"], 20:["Products"]
    }

    filtered = [
        qr for qr in QUERIES
        if (section_filter=="All" or qr["section"]==section_filter)
        and (search.strip()==""
             or search.lower() in qr["title"].lower()
             or search.lower() in qr["purpose"].lower()
             or search.lower() in qr["sql"].lower())
    ]

    if not filtered:
        st.warning(f'No queries match "{search}"')
    else:
        current_section = None
        for qr in filtered:
            sec   = qr["section"]
            color = SECTION_COLORS[sec]

            if sec != current_section:
                current_section = sec
                st.markdown(f'<div style="display:flex;align-items:center;margin:24px 0 10px">'
                            f'<span class="section-bar" style="background:{color}"></span>'
                            f'<div><strong style="font-size:16px">{sec} Queries</strong>'
                            f'<span style="font-size:12px;color:#8fa3bd;margin-left:10px">{SECTION_DESCRIPTIONS[sec]}</span>'
                            f'</div></div>', unsafe_allow_html=True)

            badge_txt=""
            if qr["id"]==22:   badge_txt=" 🔴 TRIGGER"
            elif qr["id"]==23: badge_txt=" 🟣 PROCEDURE"
            elif qr["id"]==24: badge_txt=" 🔵 INDEX"
            elif qr["id"]==25: badge_txt=" 🟢 VIEW"

            used = USED_IN.get(qr["id"],[])
            used_txt = f"  ·  📍 {', '.join(used)}" if used else ""

            with st.expander(f"**{str(qr['id']).zfill(2)}  {qr['title']}**{badge_txt}{used_txt}"):
                st.markdown(f'<div class="query-meta" style="border-color:{color}">'
                            f'<strong style="color:#e2e8f0">Purpose: </strong>{qr["purpose"]}</div>',
                            unsafe_allow_html=True)
                if used:
                    st.info(f"⚡ Powers the **{', '.join(used)}** tab(s) in this dashboard.")
                st.code(qr["sql"], language="sql")

                if qr.get("note"):
                    st.markdown(f'<div class="static-note">💡 {qr["note"]}</div>', unsafe_allow_html=True)
                if qr.get("static"):
                    st.markdown('<div class="static-note">⚠️ DDL — run in Supabase SQL Editor.</div>',
                                unsafe_allow_html=True)
                else:
                    cr1,cr2,_=st.columns([1,1,6])
                    with cr1: run_btn=st.button("▶ Run",  key=f"run_{qr['id']}", type="primary",use_container_width=True)
                    with cr2: clr_btn=st.button("✕ Clear",key=f"clr_{qr['id']}", use_container_width=True)

                    if clr_btn and f"df_{qr['id']}" in st.session_state:
                        del st.session_state[f"df_{qr['id']}"]

                    if run_btn:
                        with st.spinner("Querying…"):
                            df,err=run_query(qr["sql"])
                        if err: st.error(f"Error: {err}")
                        elif df is not None: st.session_state[f"df_{qr['id']}"]=df

                    if f"df_{qr['id']}" in st.session_state:
                        df=st.session_state[f"df_{qr['id']}"]
                        st.caption(f"✅ {len(df)} rows · {len(df.columns)} columns")
                        st.dataframe(df,use_container_width=True,height=min(400,40+len(df)*35))

                        if qr["id"]==9 and "totalrevenue" in df.columns:
                            fig=px.bar(df,x="category",y=pd.to_numeric(df["totalrevenue"]),
                                       color="category",title="Revenue by Category",
                                       color_discrete_sequence=px.colors.qualitative.Bold)
                            fig.update_layout(showlegend=False,height=300,**chart_theme())
                            st.plotly_chart(fig,use_container_width=True)
                        elif qr["id"]==14 and "rfm_score" in df.columns:
                            fig=px.scatter(df,x=pd.to_numeric(df["averagespending"]),
                                           y=pd.to_numeric(df["purchasefrequency"]),
                                           color=pd.to_numeric(df["rfm_score"]),
                                           size=pd.to_numeric(df["rfm_score"]),
                                           hover_data=["fullname","segmentlabel"],
                                           title="RFM Score Distribution",
                                           color_continuous_scale="Blues")
                            fig.update_layout(height=360,**chart_theme())
                            st.plotly_chart(fig,use_container_width=True)

                        st.download_button("⬇ Download CSV",data=df.to_csv(index=False),
                                           file_name=f"query_{qr['id']}.csv",
                                           mime="text/csv",key=f"dl_{qr['id']}")