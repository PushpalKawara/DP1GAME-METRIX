import streamlit as st
import pandas as pd
import numpy as np
import re
import datetime
import matplotlib.pyplot as plt
from io import BytesIO
import xlsxwriter

# Streamlit App Setup
st.set_page_config(page_title="DP1GAME METRIX", layout="wide")
st.title("📊 DP1GAME METRIX Dashboard")

def generate_excel(df_summary, fig):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_summary.to_excel(writer, index=False, sheet_name='Summary')
        workbook = writer.book
        worksheet = writer.sheets['Summary']
        
        # Insert the chart image
        chart_img = BytesIO()
        fig.savefig(chart_img, format='png')
        chart_img.seek(0)
        worksheet.insert_image('D3', 'chart.png', {'image_data': chart_img})

    output.seek(0)
    return output

def main():
    st.subheader("📁 Step 1: Upload Files")
    col1, col2 = st.columns(2)

    with col1:
        file1 = st.file_uploader("📥 Upload Retention Base File", type=["csv"])
    with col2:
        file2 = st.file_uploader("📥 Upload Ad Event File", type=["csv"])

    st.subheader("📝 Editable Fields")
    version = st.text_input("Enter Version", value="v0.58")
    date_selected = st.date_input("Date Selected", value=datetime.date.today())
    check_date = st.date_input("Check Date", value=datetime.date.today() + datetime.timedelta(days=1))
    day1_ret = st.text_input("Day 1 Retention (%)", value="29.56%")
    day3_ret = st.text_input("Day 3 Retention (%)", value="13.26%")
    session_len = st.text_input("Session Length (sec)", value="264.5")
    playtime_len = st.text_input("Playtime Length (sec)", value="936.6")

    if st.button("🔁 Update Metrics"):
        st.experimental_rerun()

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

        # Chart plot
        st.subheader("📈 Retention Chart (Levels 1–100)")
        fig, ax = plt.subplots(figsize=(10, 5))
        df1_100 = df1[df1['LEVEL_CLEAN'] <= 100]
        ax.plot(df1_100['LEVEL_CLEAN'], df1_100['Retention %'], linestyle='-', color='blue')
        ax.set_xlim(1, 100)
        ax.set_ylim(0, 100)
        ax.set_yticks(np.arange(0, 101, 5))
        ax.set_xticks(np.arange(1, 101, 5))
        ax.set_xlabel("Level")
        ax.set_ylabel("% Retention")
        ax.set_title(f"Retention Chart (Levels 1–100) | Version: {version}")
        ax.tick_params(axis='x', labelsize=6)
        ax.grid(True, which='both', linestyle='--', linewidth=0.5)
        st.pyplot(fig)

        # Summary Table
        st.subheader("📋 Final Summary Table")
        summary_data = {
            "Metric": [
                "Version", "Date Selected", "CHECK DATE", "LEVEL 1 users",
                "Total Level Retention(20)", "Total Level Retention(50)",
                "Total Level Retention(75)", "Total Level Retention(100)",
                "Total Level Retention(150)", "Total Level Retention(200)",
                "Day 1 Retention", "Day 3 Retention",
                "Session Length", "Playtime length",
                "% of Users at Ad 10", "% of Users at Ad 20",
                "% of Users at Ad 40", "% of Users at Ad 70",
                "% of Users at Ad 100", "Avg ads per users"
            ],
            "Value": [
                version,
                date_selected.strftime("%d-%b-%y"),
                check_date.strftime("%d-%b-%y"),
                max_users,
                f"{df1[df1['LEVEL_CLEAN'] == 20]['Retention %'].values[0]}%" if 20 in df1['LEVEL_CLEAN'].values else "N/A",
                f"{df1[df1['LEVEL_CLEAN'] == 50]['Retention %'].values[0]}%" if 50 in df1['LEVEL_CLEAN'].values else "N/A",
                f"{df1[df1['LEVEL_CLEAN'] == 75]['Retention %'].values[0]}%" if 75 in df1['LEVEL_CLEAN'].values else "N/A",
                f"{df1[df1['LEVEL_CLEAN'] == 100]['Retention %'].values[0]}%" if 100 in df1['LEVEL_CLEAN'].values else "N/A",
                f"{df1[df1['LEVEL_CLEAN'] == 150]['Retention %'].values[0]}%" if 150 in df1['LEVEL_CLEAN'].values else "N/A",
                f"{df1[df1['LEVEL_CLEAN'] == 200]['Retention %'].values[0]}%" if 200 in df1['LEVEL_CLEAN'].values else "N/A",
                day1_ret, day3_ret, session_len, playtime_len,
                f"{df2[df2['EVENT_CLEAN'] == 10]['% of Users at Ad'].values[0]}%" if 10 in df2['EVENT_CLEAN'].values else "N/A",
                f"{df2[df2['EVENT_CLEAN'] == 20]['% of Users at Ad'].values[0]}%" if 20 in df2['EVENT_CLEAN'].values else "N/A",
                f"{df2[df2['EVENT_CLEAN'] == 40]['% of Users at Ad'].values[0]}%" if 40 in df2['EVENT_CLEAN'].values else "N/A",
                f"{df2[df2['EVENT_CLEAN'] == 70]['% of Users at Ad'].values[0]}%" if 70 in df2['EVENT_CLEAN'].values else "N/A",
                f"{df2[df2['EVENT_CLEAN'] == 100]['% of Users at Ad'].values[0]}%" if 100 in df2['EVENT_CLEAN'].values else "N/A",
                total_avg_ads
            ]
        }

        df_summary = pd.DataFrame(summary_data)
        st.dataframe(df_summary, use_container_width=True)

        # Download Buttons
        st.subheader("📤 Export Options")
        st.download_button(
            label="⬇️ Download Table Only (CSV)",
            data=df_summary.to_csv(index=False).encode('utf-8'),
            file_name="summary_table.csv",
            mime='text/csv'
        )

        excel_output = generate_excel(df_summary, fig)
        st.download_button(
            label="⬇️ Download Summary + Chart (Excel)",
            data=excel_output,
            file_name="summary_with_chart.xlsx",
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

if __name__ == "__main__":
    main()
