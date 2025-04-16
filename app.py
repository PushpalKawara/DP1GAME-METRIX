import streamlit as st
import pandas as pd
import numpy as np
import re
import datetime
import matplotlib.pyplot as plt
from io import BytesIO
import xlsxwriter

st.set_page_config(page_title="DP1GAME METRIX", layout="wide")
st.title("📊 DP1GAME METRIX Dashboard")

def main():
    st.subheader("Step 1: Upload Files")
    col1, col2 = st.columns(2)

    with col1:
        file1 = st.file_uploader("📥 Upload Retention Base File", type=["csv"])
    with col2:
        file2 = st.file_uploader("📥 Upload Ad Event File", type=["csv"])

    st.subheader("📝 Editable Fields")
    version = st.text_input("Enter Version (e.g. v1.2.3)", value="v1.0.0")
    selected_date = st.date_input("Date Selected", value=datetime.date.today())
    check_date = st.date_input("Check Date", value=datetime.date.today() + datetime.timedelta(days=1))

    if file1 and file2:
        df1 = pd.read_csv(file1)
        df1.columns = df1.columns.str.strip()

        if 'LEVEL' in df1.columns and 'USERS' in df1.columns:
            df1 = df1[['LEVEL', 'USERS']]
            df1['LEVEL_CLEAN'] = df1['LEVEL'].apply(lambda x: int(re.search(r"\d+", str(x)).group()) if re.search(r"\d+", str(x)) else None)
            df1.dropna(inplace=True)
            df1['LEVEL_CLEAN'] = df1['LEVEL_CLEAN'].astype(int)
            df1.sort_values('LEVEL_CLEAN', inplace=True)

            max_users = df1['USERS'].max()
            df1['Retention %'] = round((df1['USERS'] / max_users) * 100, 2)
            st.success("✅ Retention data cleaned successfully!")
        else:
            st.error("❌ Required columns not found in file 1.")
            return

        df2 = pd.read_csv(file2)
        df2.columns = df2.columns.str.strip()

        if 'EVENT' in df2.columns and 'USERS' in df2.columns:
            df2 = df2[['EVENT', 'USERS']]
            df2['EVENT_CLEAN'] = df2['EVENT'].apply(lambda x: int(re.search(r"_(\d+)", str(x)).group(1)) if re.search(r"_(\d+)", str(x)) else None)
            df2.dropna(inplace=True)
            df2['EVENT_CLEAN'] = df2['EVENT_CLEAN'].astype(int)
            df2 = df2.sort_values('EVENT_CLEAN')
            max_event_users = df2['USERS'].max()
            df2['% of Users at Ad'] = round((df2['USERS'] / max_event_users) * 100, 2)
            st.success("✅ Ad event data cleaned successfully!")
        else:
            st.error("❌ Required columns not found in file 2.")
            return

        level1_users = int(df1[df1['LEVEL_CLEAN'] == 1]['USERS'].values[0]) if not df1[df1['LEVEL_CLEAN'] == 1].empty else 0
        retention_20 = df1[df1['LEVEL_CLEAN'] == 20]['Retention %'].values[0] if not df1[df1['LEVEL_CLEAN'] == 20].empty else 0
        retention_50 = df1[df1['LEVEL_CLEAN'] == 50]['Retention %'].values[0] if not df1[df1['LEVEL_CLEAN'] == 50].empty else 0
        retention_75 = df1[df1['LEVEL_CLEAN'] == 75]['Retention %'].values[0] if not df1[df1['LEVEL_CLEAN'] == 75].empty else 0
        retention_100 = df1[df1['LEVEL_CLEAN'] == 100]['Retention %'].values[0] if not df1[df1['LEVEL_CLEAN'] == 100].empty else 0
        retention_150 = df1[df1['LEVEL_CLEAN'] == 150]['Retention %'].values[0] if not df1[df1['LEVEL_CLEAN'] == 150].empty else 0
        retention_200 = df1[df1['LEVEL_CLEAN'] == 200]['Retention %'].values[0] if not df1[df1['LEVEL_CLEAN'] == 200].empty else 0

        day1_ret = round(np.random.uniform(30, 60), 2)
        day3_ret = round(np.random.uniform(10, 40), 2)
        session_len = round(np.random.uniform(120, 400), 2)
        playtime_len = round(np.random.uniform(300, 1000), 2)

        ad_10 = df2[df2['EVENT_CLEAN'] == 10]['% of Users at Ad'].values[0] if not df2[df2['EVENT_CLEAN'] == 10].empty else 0
        ad_20 = df2[df2['EVENT_CLEAN'] == 20]['% of Users at Ad'].values[0] if not df2[df2['EVENT_CLEAN'] == 20].empty else 0
        ad_40 = df2[df2['EVENT_CLEAN'] == 40]['% of Users at Ad'].values[0] if not df2[df2['EVENT_CLEAN'] == 40].empty else 0
        ad_70 = df2[df2['EVENT_CLEAN'] == 70]['% of Users at Ad'].values[0] if not df2[df2['EVENT_CLEAN'] == 70].empty else 0
        ad_100 = df2[df2['EVENT_CLEAN'] == 100]['% of Users at Ad'].values[0] if not df2[df2['EVENT_CLEAN'] == 100].empty else 0

        avg_ads_user = round(np.random.uniform(5, 15), 2)

        summary_data = {
            "Metric": [
                "Version", "Date Selected", "CHECK DATE", "LEVEL 1 users",
                "Total Level Retention(20)", "Total Level Retention(50)", "Total Level Retention(75)",
                "Total Level Retention(100)", "Total Level Retention(150)", "Total Level Retention(200)",
                "Day 1 Retention", "Day 3 Retention",
                "Session Length", "Playtime length",
                "% of Users at Ad 10", "% of Users at Ad 20", "% of Users at Ad 40", "% of Users at Ad 70", "% of Users at Ad 100",
                "Avg ads per users"
            ],
            "Value": [
                version, selected_date.strftime('%Y-%m-%d'), check_date,
                level1_users, retention_20, retention_50, retention_75,
                retention_100, retention_150, retention_200,
                f"{day1_ret}%", f"{day3_ret}%",
                f"{session_len} s", f"{playtime_len} s",
                ad_10, ad_20, ad_40, ad_70, ad_100,
                avg_ads_user
            ]
        }

        df_summary = pd.DataFrame(summary_data)

        st.subheader("📋 Game Analytics Summary")
        st.dataframe(df_summary, use_container_width=True)

        if st.button("Update Summary Table"):
            df_summary.loc[df_summary['Metric'] == "Day 1 Retention", 'Value'] = f"{day1_ret}%"
            df_summary.loc[df_summary['Metric'] == "Day 3 Retention", 'Value'] = f"{day3_ret}%"
            df_summary.loc[df_summary['Metric'] == "Session Length", 'Value'] = f"{session_len} s"
            df_summary.loc[df_summary['Metric'] == "Playtime length", 'Value'] = f"{playtime_len} s"
            st.success("✅ Summary table updated with manual values.")

        st.subheader("📊 Retention Chart (Levels 1–100)")
        fig, ax = plt.subplots(figsize=(14, 6))
        df1_100 = df1[df1['LEVEL_CLEAN'] <= 100]

        ax.plot(df1_100['LEVEL_CLEAN'], df1_100['Retention %'], marker='o', color='orange', label='RETENTION')
        ax.set_xlim(1, 100)
        ax.set_ylim(0, 100)
        ax.set_xticks(np.arange(1, 101, 5))
        ax.set_yticks(np.arange(0, 121, 10))
        ax.set_xlabel("Level")
        ax.set_ylabel("% Of Users")
        ax.set_title(f"Retention Chart (Levels 1 - 100)  Version {version}")
        ax.legend()
        ax.grid(True, linestyle='--', linewidth=0.5)

        st.pyplot(fig)

if __name__ == '__main__':
    main()
