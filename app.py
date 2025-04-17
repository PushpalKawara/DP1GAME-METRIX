import streamlit as st
import pandas as pd
import numpy as np
import re
import datetime
import matplotlib.pyplot as plt

def main():
    # -------------------- PAGE CONFIG -------------------- #
    st.set_page_config(page_title="DP1GAME METRIX", layout="wide")
    st.title("📊 DP1GAME METRIX Dashboard")

    # -------------------- STEP 1: UPLOAD FILES -------------------- #
    st.subheader("Step 1: Upload Files")
    col1, col2 = st.columns(2)

    with col1:
        file1 = st.file_uploader("📥 Upload Retention Base File", type=["csv"])
    with col2:
        file2 = st.file_uploader("📥 Upload Ad Event File", type=["csv"])

    if file1 and file2:
        # -------------------- STEP 2: CLEAN FILE 1 -------------------- #
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
            st.error("❌ Required columns not found in file 1.")

        # -------------------- STEP 3: CLEAN FILE 2 -------------------- #
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
            st.error("❌ Required columns not found in file 2.")

        # -------------------- STEP 4: CHARTS -------------------- #
        st.subheader("📈 Retention Chart (Levels 1 - Continue)")
        fig1, ax1 = plt.subplots()
        ax1.plot(df1['LEVEL_CLEAN'], df1['Retention %'], marker='o', linestyle='-', color='blue')
        ax1.set_xlabel("Level")
        ax1.set_ylabel("Retention %")
        ax1.set_title("Retention Chart (All Levels)")
        ax1.grid(True)
        st.pyplot(fig1)

        st.subheader("📉 Retention Chart (Levels 1 - 100)")
        df_100 = df1[df1['LEVEL_CLEAN'] <= 100]
        fig2, ax2 = plt.subplots()
        ax2.plot(df_100['LEVEL_CLEAN'], df_100['Retention %'], marker='o', linestyle='-', color='green')
        ax2.set_xlabel("Level")
        ax2.set_ylabel("Retention %")
        ax2.set_title("Retention Chart (Levels 1-100)")
        ax2.grid(True)
        st.pyplot(fig2)

        # -------------------- STEP 5: FINAL SUMMARY -------------------- #
        st.subheader("📋 Final Summary Table (Vertical View)")

        summary_data = {
            "Version": "0.58",
            "Date Selected": datetime.date.today().strftime("%d-%b-%y"),
            "CHECK DATE": (datetime.date.today() + datetime.timedelta(days=1)).strftime("%d-%b-%y"),
            "LEVEL 1 users": max_users,
            "Total Level Retention(20)": f"{df1[df1['LEVEL_CLEAN'] == 20]['Retention %'].values[0]}%" if 20 in df1['LEVEL_CLEAN'].values else "N/A",
            "Total Level Retention(50)": f"{df1[df1['LEVEL_CLEAN'] == 50]['Retention %'].values[0]}%" if 50 in df1['LEVEL_CLEAN'].values else "N/A",
            "Total Level Retention(75)": f"{df1[df1['LEVEL_CLEAN'] == 75]['Retention %'].values[0]}%" if 75 in df1['LEVEL_CLEAN'].values else "N/A",
            "Total Level Retention(100)": f"{df1[df1['LEVEL_CLEAN'] == 100]['Retention %'].values[0]}%" if 100 in df1['LEVEL_CLEAN'].values else "N/A",
            "Total Level Retention(150)": f"{df1[df1['LEVEL_CLEAN'] == 150]['Retention %'].values[0]}%" if 150 in df1['LEVEL_CLEAN'].values else "N/A",
            "Total Level Retention(200)": f"{df1[df1['LEVEL_CLEAN'] == 200]['Retention %'].values[0]}%" if 200 in df1['LEVEL_CLEAN'].values else "N/A",
            "% of Users at Ad 10": f"{df2[df2['EVENT_CLEAN'] == 10]['% of Users at Ad'].values[0]}%" if 10 in df2['EVENT_CLEAN'].values else "N/A",
            "% of Users at Ad 20": f"{df2[df2['EVENT_CLEAN'] == 20]['% of Users at Ad'].values[0]}%" if 20 in df2['EVENT_CLEAN'].values else "N/A",
            "% of Users at Ad 40": f"{df2[df2['EVENT_CLEAN'] == 40]['% of Users at Ad'].values[0]}%" if 40 in df2['EVENT_CLEAN'].values else "N/A",
            "% of Users at Ad 70": f"{df2[df2['EVENT_CLEAN'] == 70]['% of Users at Ad'].values[0]}%" if 70 in df2['EVENT_CLEAN'].values else "N/A",
            "% of Users at Ad 100": f"{df2[df2['EVENT_CLEAN'] == 100]['% of Users at Ad'].values[0]}%" if 100 in df2['EVENT_CLEAN'].values else "N/A",
            "Avg ads per users": total_avg_ads
        }

        df_summary = pd.DataFrame.from_dict(summary_data, orient='index', columns=['Value'])
        st.dataframe(df_summary, use_container_width=True)

        # -------------------- STEP 6: MANUAL METRICS SECTION -------------------- #
        st.subheader("📝 Step 6: Pasteable Manual Metrics")

        tab1, tab2 = st.tabs(["📥 Manual Input", "📋 Copy Summary"])

        with tab1:
            st.markdown("### 🔧 Enter Manual Metrics Here:")
            day1_retention = st.text_input("Day 1 Retention (%)", value="29.56%")
            day3_retention = st.text_input("Day 3 Retention (%)", value="13.26%")
            session_length = st.text_input("Session Length (in sec)", value="264.5")
            playtime_length = st.text_input("Playtime Length (in sec)", value="936.6")

            if st.button("Update Summary Table"):
                df_summary.loc["Day 1 Retention"] = day1_retention
                df_summary.loc["Day 3 Retention"] = day3_retention
                df_summary.loc["Session Length"] = f"{session_length} s"
                df_summary.loc["Playtime length"] = f"{playtime_length} s"
                st.success("Summary table updated with manual values.")

        with tab2:
            st.markdown("### 📋 Final Summary Table (Paste Anywhere)")
            st.dataframe(df_summary, use_container_width=True)

    else:
        st.warning("⬆️ Please upload both files to continue.")

if __name__ == "__main__":
    main()
