import streamlit as st
import pandas as pd
import numpy as np
import re
import datetime
import matplotlib.pyplot as plt
import pyperclip

st.set_page_config(page_title="DP1GAME METRIX", layout="wide")
st.title("📊 DP1GAME METRIX Dashboard")

st.subheader("Step 1: Upload Files")
col1, col2 = st.columns(2)

with col1:
    file1 = st.file_uploader("📥 Upload Retention Base File", type=["csv"])
with col2:
    file2 = st.file_uploader("📥 Upload Ad Event File", type=["csv"])

if file1 and file2:
    df1 = pd.read_csv(file1)
    df1.columns = df1.columns.str.strip()

    if 'LEVEL' in df1.columns and 'USERS' in df1.columns:
        df1 = df1[['LEVEL', 'USERS']]

        def clean_level(x):
            try:
                return int(re.search(r"(\d+)", str(x)).group(1))
            except:
                return None

        df1['LEVEL_CLEAN'] = df1['LEVEL'].apply(clean_level)
        df1.dropna(inplace=True)
        df1['LEVEL_CLEAN'] = df1['LEVEL_CLEAN'].astype(int)
        df1.sort_values('LEVEL_CLEAN', inplace=True)

        max_users = df1['USERS'].max()
        df1['Retention %'] = round((df1['USERS'] / max_users) * 100, 2)

        st.success("✅ Retention data cleaned successfully!")
    else:
        st.error("❌ Required columns not found in Retention file.")

    df2 = pd.read_csv(file2)
    df2.columns = df2.columns.str.strip()

    if 'EVENT' in df2.columns and 'USERS' in df2.columns:
        df2 = df2[['EVENT', 'USERS']]

        def extract_ad_number(x):
            try:
                return int(re.search(r"_(\d+)", str(x)).group(1))
            except:
                return None

        df2['EVENT_CLEAN'] = df2['EVENT'].apply(extract_ad_number)
        df2.dropna(inplace=True)
        df2['EVENT_CLEAN'] = df2['EVENT_CLEAN'].astype(int)
        df2 = df2.sort_values('EVENT_CLEAN')

        df2['% of Users at Ad'] = round((df2['USERS'] / max_users) * 100, 2)

        df2['Diff of Ads'] = df2['EVENT_CLEAN'].diff().fillna(df2['EVENT_CLEAN']).astype(int)
        df2['Multi'] = df2['Diff of Ads'] * df2['USERS']
        avg_diff = df2['Diff of Ads'].mean()
        df2['Diff of Users'] = df2['USERS'].diff().fillna(df2['USERS']).astype(int)
        df2['Multi 2'] = avg_diff * df2['Diff of Users']
        total_avg_ads = round((df2['Multi'].sum() + df2['Multi 2'].sum()) / max_users, 2)

        st.success("✅ Ad data processed successfully!")
    else:
        st.error("❌ Required columns not found in Ad Event file.")

    # 📈 Charts
    st.subheader("📈 Retention Chart (All Levels)")
    fig1, ax1 = plt.subplots()
    ax1.plot(df1['LEVEL_CLEAN'], df1['Retention %'], marker='o')
    ax1.set_title("User Retention by Level")
    ax1.set_xlabel("Level")
    ax1.set_ylabel("Retention %")
    ax1.grid(True)
    st.pyplot(fig1)

    st.subheader("📈 Retention Chart (Levels 1-100)")
    fig2, ax2 = plt.subplots()
    df1_100 = df1[df1['LEVEL_CLEAN'] <= 100]
    ax2.plot(df1_100['LEVEL_CLEAN'], df1_100['Retention %'], marker='o')
    ax2.set_title("User Retention (Levels 1-100)")
    ax2.set_xlabel("Level")
    ax2.set_ylabel("Retention %")
    ax2.grid(True)
    st.pyplot(fig2)

    # 📋 Summary Table
    st.subheader("📋 Final Summary Table (Vertical)")

    def get_retention(level):
        return f"{df1[df1['LEVEL_CLEAN'] == level]['Retention %'].values[0]}%" if level in df1['LEVEL_CLEAN'].values else "N/A"

    def get_ad(ad_num):
        return f"{df2[df2['EVENT_CLEAN'] == ad_num]['% of Users at Ad'].values[0]}%" if ad_num in df2['EVENT_CLEAN'].values else "N/A"

    summary_data = {
        "Metric": [
            "Version", "Date Selected", "CHECK DATE", "LEVEL 1 users",
            "Total Level Retention(20)", "Total Level Retention(50)", "Total Level Retention(75)",
            "Total Level Retention(100)", "Total Level Retention(150)", "Total Level Retention(200)",
            "% of Users at Ad 10", "% of Users at Ad 20", "% of Users at Ad 40",
            "% of Users at Ad 70", "% of Users at Ad 100", "Avg ads per users",
            "Day 1 Retention", "Day 3 Retention", "Session Length", "Playtime length"
        ],
        "Value": [
            "0.58", datetime.date.today().strftime("%d-%b-%y"),
            (datetime.date.today() + datetime.timedelta(days=1)).strftime("%d-%b-%y"),
            max_users,
            get_retention(20), get_retention(50), get_retention(75),
            get_retention(100), get_retention(150), get_retention(200),
            get_ad(10), get_ad(20), get_ad(40),
            get_ad(70), get_ad(100), total_avg_ads,
            "", "", "", ""
        ]
    }

    df_summary = pd.DataFrame(summary_data)
    st.dataframe(df_summary, use_container_width=True)

    # 📝 Manual Input
    st.subheader("📝 Step 6: Pasteable Manual Metrics")
    tab1, tab2 = st.tabs(["🛠️ Manual Input", "📋 Copy Summary"])

    with tab1:
        st.markdown("### 🔧 Enter Manual Metrics Here:")
        day1 = st.text_input("Day 1 Retention (%)", value="29.56%")
        day3 = st.text_input("Day 3 Retention (%)", value="13.26%")
        session_len = st.text_input("Session Length (in sec)", value="264.5")
        play_len = st.text_input("Playtime Length (in sec)", value="936.6")

        if st.button("Update Summary Table"):
            df_summary.loc[df_summary['Metric'] == "Day 1 Retention", 'Value'] = day1
            df_summary.loc[df_summary['Metric'] == "Day 3 Retention", 'Value'] = day3
            df_summary.loc[df_summary['Metric'] == "Session Length", 'Value'] = session_len + " s"
            df_summary.loc[df_summary['Metric'] == "Playtime length", 'Value'] = play_len + " s"
            st.success("✅ Summary table updated!")

    with tab2:
        st.markdown("### 📋 Final Summary (Copy Ready)")
        st.dataframe(df_summary, use_container_width=True)

        summary_str = df_summary.to_string(index=False)
        if st.button("📋 Copy Summary to Clipboard"):
            try:
                pyperclip.copy(summary_str)
                st.success("Summary copied to clipboard!")
            except:
                st.error("Clipboard copy not supported in this browser. Use Ctrl+C manually.")

else:
    st.warning("⏫ Please upload both files to continue.")
