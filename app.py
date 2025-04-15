import streamlit as st
import pandas as pd
import numpy as np
import re
import datetime
import matplotlib.pyplot as plt

st.set_page_config(page_title="DP1GAME METRIX", layout="wide")
st.title("\U0001F4CA DP1GAME METRIX Dashboard")

st.subheader("Step 1: Upload Files")
col1, col2 = st.columns(2)

with col1:
    file1 = st.file_uploader("\U0001F4E5 Upload Retention Base File", type=["csv"])
with col2:
    file2 = st.file_uploader("\U0001F4E5 Upload Ad Event File", type=["csv"])

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

        st.success("\u2705 Retention data cleaned successfully!")
    else:
        st.error("\u274C Required columns not found in file 1.")

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

        st.success("\u2705 Ad data processed successfully!")
    else:
        st.error("\u274C Required columns not found in file 2.")

    st.subheader("\U0001F4C8 Retention Chart (Levels 1-Continue)")
    fig1, ax1 = plt.subplots()
    ax1.plot(df1['LEVEL_CLEAN'], df1['Retention %'], marker='o', linestyle='-')
    ax1.set_xlabel("Level")
    ax1.set_ylabel("Retention %")
    ax1.set_title("User Retention by Level")
    ax1.grid(True)
    st.pyplot(fig1)

    st.subheader("\U0001F4C8 Retention Chart (Levels 1-100 Only)")
    fig2, ax2 = plt.subplots()
    df1_100 = df1[df1['LEVEL_CLEAN'] <= 100]
    ax2.plot(df1_100['LEVEL_CLEAN'], df1_100['Retention %'], marker='o', linestyle='-')
    ax2.set_xlabel("Level")
    ax2.set_ylabel("Retention %")
    ax2.set_title("User Retention (1-100)")
    ax2.grid(True)
    st.pyplot(fig2)

    st.subheader("\U0001F4CB Final Summary Table (Vertical)")

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
            "0.58", datetime.date.today().strftime("%d-%b-%y"), (datetime.date.today() + datetime.timedelta(days=1)).strftime("%d-%b-%y"),
            max_users,
            f"{df1[df1['LEVEL_CLEAN'] == 20]['Retention %'].values[0]}%" if 20 in df1['LEVEL_CLEAN'].values else "N/A",
            f"{df1[df1['LEVEL_CLEAN'] == 50]['Retention %'].values[0]}%" if 50 in df1['LEVEL_CLEAN'].values else "N/A",
            f"{df1[df1['LEVEL_CLEAN'] == 75]['Retention %'].values[0]}%" if 75 in df1['LEVEL_CLEAN'].values else "N/A",
            f"{df1[df1['LEVEL_CLEAN'] == 100]['Retention %'].values[0]}%" if 100 in df1['LEVEL_CLEAN'].values else "N/A",
            f"{df1[df1['LEVEL_CLEAN'] == 150]['Retention %'].values[0]}%" if 150 in df1['LEVEL_CLEAN'].values else "N/A",
            f"{df1[df1['LEVEL_CLEAN'] == 200]['Retention %'].values[0]}%" if 200 in df1['LEVEL_CLEAN'].values else "N/A",
            f"{df2[df2['EVENT_CLEAN'] == 10]['% of Users at Ad'].values[0]}%" if 10 in df2['EVENT_CLEAN'].values else "N/A",
            f"{df2[df2['EVENT_CLEAN'] == 20]['% of Users at Ad'].values[0]}%" if 20 in df2['EVENT_CLEAN'].values else "N/A",
            f"{df2[df2['EVENT_CLEAN'] == 40]['% of Users at Ad'].values[0]}%" if 40 in df2['EVENT_CLEAN'].values else "N/A",
            f"{df2[df2['EVENT_CLEAN'] == 70]['% of Users at Ad'].values[0]}%" if 70 in df2['EVENT_CLEAN'].values else "N/A",
            f"{df2[df2['EVENT_CLEAN'] == 100]['% of Users at Ad'].values[0]}%" if 100 in df2['EVENT_CLEAN'].values else "N/A",
            total_avg_ads, "", "", "", ""
        ]
    }
    df_summary = pd.DataFrame(summary_data)
    st.dataframe(df_summary, use_container_width=True)

    st.subheader("\U0001F4DD Step 6: Pasteable Manual Metrics")

    tab1, tab2 = st.tabs(["\U0001F4E5 Manual Input", "\U0001F4CB Copy Summary"])

    with tab1:
        st.markdown("### \U0001F527 Enter Manual Metrics Here:")
        day1_retention = st.text_input("Day 1 Retention (%)", value="29.56%")
        day3_retention = st.text_input("Day 3 Retention (%)", value="13.26%")
        session_length = st.text_input("Session Length (in sec)", value="264.5")
        playtime_length = st.text_input("Playtime Length (in sec)", value="936.6")

        if st.button("Update Summary Table"):
            df_summary.loc[df_summary['Metric'] == "Day 1 Retention", 'Value'] = day1_retention
            df_summary.loc[df_summary['Metric'] == "Day 3 Retention", 'Value'] = day3_retention
            df_summary.loc[df_summary['Metric'] == "Session Length", 'Value'] = session_length + " s"
            df_summary.loc[df_summary['Metric'] == "Playtime length", 'Value'] = playtime_length + " s"
            st.success("Summary table updated with manual values.")

    with tab2:
        st.markdown("### \U0001F4CB Final Summary Table (Paste Anywhere)")
        st.dataframe(df_summary, use_container_width=True)

else:
    st.warning("\u2B06\uFE0F Please upload both files to continue.")
