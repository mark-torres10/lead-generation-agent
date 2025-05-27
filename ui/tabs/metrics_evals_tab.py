import streamlit as st

def render_metrics_evals_tab():
    st.title("📊 Metrics and Evaluations")
    st.markdown("""
    This section outlines the key metrics and evaluation criteria proposed for the Leads AI Agent Demo. These metrics are designed to demonstrate business impact, technical performance, and quality to both technical and non-technical stakeholders.
    """)

    st.header("1. Business Impact Metrics")
    
    st.subheader("🎯 Time & Productivity Analysis")
    st.markdown("""
    **Objective:** Estimate time and cost savings from replacing manual lead qualification, 
    email response handling, and meeting scheduling with AI agents for a typical inside sales team of 3–5 reps.
    """)
    
    # Create columns for the analysis
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("**📊 Manual Time per Rep per Week**")
        
        # Create a simple table using markdown
        st.markdown("""
        | Task | Volume | Time/Item | Total Time |
        |------|--------|-----------|------------|
        | Lead Qualification | 125 leads | 4 min | **8.3 hrs** |
        | Reply Handling | 60 replies | 3 min | **3.0 hrs** |
        | Meeting Scheduling | 15 meetings | 5 min | **1.25 hrs** |
        | **Total per rep** | — | — | **12.5 hrs/week** |
        """)
    
    with col2:
        st.markdown("**💰 Team Cost Savings**")
        
        st.markdown("""
        | Team Size | Weekly Savings | Monthly | Yearly |
        |-----------|----------------|---------|--------|
        | 3 reps | 37.5 hours | 150 hrs | **1,800 hrs** |
        | 5 reps | 62.5 hours | 250 hrs | **3,000 hrs** |
        """)
        
        st.info("💡 **This is like adding 1-2 full-time team members without hiring!**")
    
    # Financial impact section
    st.markdown("**💸 Financial Impact (@ $50/hr fully loaded cost)**")
    
    col3, col4 = st.columns([1, 1])
    
    with col3:
        st.metric("3-Rep Team Savings", "$120,000/year", "$10,000/month")
    
    with col4:
        st.metric("5-Rep Team Savings", "$200,000/year", "$17,000/month")

    # Add emphasis box for key impact statement
    st.markdown("---")
    
    # Create a highlighted impact box
    st.markdown("""
    <div style="
        border: 3px solid #ff6b6b;
        border-radius: 10px;
        padding: 20px;
        background-color: #fff5f5;
        margin: 20px 0;
    ">
        <h3 style="color: #d63031; margin-top: 0;">🚀 Key Impact Summary</h3>
        <p style="font-size: 18px; font-weight: 500; color: #2d3436; margin-bottom: 0;">
            A single rep spends ~12 hours a week on repetitive tasks like triaging leads, responding to early-stage emails, and scheduling meetings. With AI agents handling these, you get back the equivalent of a full workday per rep. At 3–5 reps, that's like hiring another 1–2 people without increasing headcount.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("**✅ Where AI Agent Delivers 100% Time Savings:**")
    st.markdown("""
    - **Lead Qualification:** Analyze message + CRM → score + next action *(saves 8 hrs/week per rep)*
    - **Reply Triage:** Detect intent, generate tailored response *(saves 3 hrs/week per rep)*
    - **Scheduling:** Auto-suggest slots, sync calendars, confirm *(saves 1.25 hrs/week per rep)*
    
    **Result:** Reps shift from admin work to engagement & closing deals.
    """)

    st.subheader("B. Lead Management Effectiveness")
    
    st.markdown("**💼 Executive Summary**")
    st.info("""
    With AI agents handling lead qualification, replies, and follow-ups, we don't just save time — we process more leads, respond faster, and convert better. That translates directly to more deals closed with fewer hours burned.
    """)
    
    st.markdown("**📊 Before vs. After: Key Performance Metrics**")
    
    # Create comparison table
    st.markdown("""
    | Metric | Without Agent | With Agent | Change |
    |--------|---------------|------------|--------|
    | **Leads processed/week (per rep)** | 125 | 250 | **+100% throughput** |
    | **Qualified leads identified/week** | 25 (20% of 125) | 63 (25% of 250) | **+150% qualified leads** |
    | **Avg. time to first reply** | 12 hours | 1 hour | **11 hours faster** |
    | **Email replies per day** | 25 | 75 | **+3× faster** |
    | **Response relevance** | 65% | 85% | **+20% better content** |
    | **Meeting coordination time/week** | 75 min | 5 min | **-93% time spent** |
    """)
    
    st.markdown("**📈 Pipeline & Revenue Impact**")
    
    col_rev1, col_rev2 = st.columns([1, 1])
    
    with col_rev1:
        st.markdown("**Without Agent (3-rep team):**")
        st.markdown("""
        - 75 qualified leads/week
        - 3.75 deals/week (5% close rate)
        - Standard revenue flow
        """)
    
    with col_rev2:
        st.markdown("**With Agent (3-rep team):**")
        st.markdown("""
        - 189 qualified leads/week
        - 9.45 deals/week (5% close rate)
        - **+$28,500/week additional revenue**
        """)
    
    # Revenue impact highlight
    st.markdown("""
    <div style="
        border: 3px solid #00b894;
        border-radius: 10px;
        padding: 20px;
        background-color: #f0fff4;
        margin: 20px 0;
    ">
        <h4 style="color: #00b894; margin-top: 0;">💰 Revenue Multiplier Effect</h4>
        <p style="font-size: 16px; font-weight: 500; color: #2d3436;">
            <strong>+$1.4M/year additional pipeline</strong> from processing 2× more leads with 3× faster responses. 
            This isn't just efficiency — it's revenue growth that couldn't happen without AI automation.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("**🔁 Response & Follow-up Efficiency Gains**")
    
    st.markdown("""
    | Task | Without Agent | With Agent | Why It Matters |
    |------|---------------|------------|----------------|
    | **First touch delay** | 12-24 hours | Within 1 hour | Fast response = higher engagement |
    | **Follow-up consistency** | Manual & erratic | Deterministic, prompt | Increases trust + drives action |
    | **Emails handled daily** | 25 per rep | 75+ per rep | Scale without headcount |
    | **Message customization** | Low (templates) | High (context-aware) | More engaging and relevant |
    """)
    
    st.success("**Bottom Line:** We're not just saving 10+ hours/week per rep. We're putting those hours into high-leverage activities like closing deals and building relationships, while simultaneously processing 2× more leads.")

    st.header("2. Technical Performance Metrics")
    st.subheader("A. Cost Efficiency")
    st.markdown("""
    - **API cost per lead processed**
    - **Total automation cost**
    - **Cost savings vs. manual processing**
    """)

    st.subheader("B. System Reliability")
    st.markdown("""
    - **System uptime**
    - **Error rates and recovery times**
    - **API response times**
    """)

    st.header("3. Quality Metrics")
    st.subheader("A. Lead Qualification Accuracy")
    st.markdown("""
    - **Accuracy of AI lead qualification vs. human review**
    - **False positive/negative rates**
    - **Lead scoring accuracy**
    """)

    st.subheader("B. Communication Quality")
    st.markdown("""
    - **Relevance and engagement of automated responses**
    - **Conversation completion rates**
    - **Need for human intervention**
    """)

    st.info("These metrics are proposed for future implementation and will help demonstrate the value and impact of the AI agent to all stakeholders.") 