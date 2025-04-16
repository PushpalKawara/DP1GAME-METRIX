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
    with st.expander("📥 Upload Files", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            file1 = st.file_uploader("📁 Upload Retention Base File", type=["csv"])
        with col2:
            file2 = st.file_uploader("📁 Upload Ad Event File", type=["csv"])

    with st.expander("🛠️ Configuration", expanded=True):
        version = st.text_input("🆚 Enter Version (e.g. v1.2.3)", value="v1.0.0")
        col3, col4 = st.columns(2)
        with col3:
            date_selected = st.date_input("📅 Date Selected", value=datetime.date.today())
        with col4:
            check_date = st.date_input("✅ Check Date", value=datetime.date.today() + datetime.timedelta(days=1))

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
            return

        with st.expander("📈 Retention Chart", expanded=True):
            max_level = df1['LEVEL_CLEAN'].max()
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(df1['LEVEL_CLEAN'], df1['Retention %'], linestyle='-', color='blue', marker='o', markersize=4)
            ax.set_xlim(1, max_level)
            ax.set_ylim(0, 100)
            ax.set_yticks(np.arange(0, 101, 5))
            ax.set_xticks(np.arange(1, max_level+1, 5))
            ax.set_xlabel("Level")
            ax.set_ylabel("Retention %")
            ax.set_title(f"➤ Retention Curve | Version: {version}")
            ax.grid(True, linestyle='--', linewidth=0.5)
            st.pyplot(fig)

        with st.expander("📋 Final Summary Table", expanded=True):
            summary_data = {
                "Metric": [
                    "Version", "Date Selected", "CHECK DATE", "LEVEL 1 users",
                    "Total Level Retention(20)", "Total Level Retention(50)",
                    "Total Level Retention(75)", "Total Level Retention(100)",
                    "Total Level Retention(150)", "Total Level Retention(200)",
                    "% of Users at Ad 10", "% of Users at Ad 20", "% of Users at Ad 40",
                    "% of Users at Ad 70", "% of Users at Ad 100", "Avg ads per users",
                    "Day 1 Retention", "Day 3 Retention", "Session Length", "Playtime length"
                ],
                "Value": [
                    version, date_selected.strftime("%d-%b-%y"), check_date.strftime("%d-%b-%y"),
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

        with st.expander("✍️ Manual Metrics Entry"):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                day1_ret = st.text_input("Day 1 Retention (%)", value="29.56%")
            with col2:
                day3_ret = st.text_input("Day 3 Retention (%)", value="13.26%")
            with col3:
                session_len = st.text_input("Session Length (sec)", value="264.5")
            with col4:
                playtime_len = st.text_input("Playtime Length (sec)", value="936.6")

            if st.button("📌 Update Summary Table"):
                df_summary.loc[df_summary['Metric'] == "Day 1 Retention", 'Value'] = day1_ret
                df_summary.loc[df_summary['Metric'] == "Day 3 Retention", 'Value'] = day3_ret
                df_summary.loc[df_summary['Metric'] == "Session Length", 'Value'] = session_len + " s"
                df_summary.loc[df_summary['Metric'] == "Playtime length", 'Value'] = playtime_len + " s"
                st.success("✅ Summary updated with manual metrics.")

        with st.expander("📤 Export Excel Report"):
            if st.button("📥 Generate & Download Excel"):
                output = BytesIO()
                writer = pd.ExcelWriter(output, engine='xlsxwriter')
                df_summary.to_excel(writer, index=False, sheet_name='Summary')
                workbook = writer.book
                worksheet = writer.sheets['Summary']

                # Save chart to buffer
                chart_buffer = BytesIO()
                fig.savefig(chart_buffer, format='png')
                worksheet.insert_image('E2', 'retention_chart.png', {'image_data': chart_buffer})
                writer.close()

                st.download_button(
                    label="📄 Download Excel File",
                    data=output.getvalue(),
                    file_name=f"DP1GAME_METRIX_{version}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

if __name__ == "__main__":
    main()
