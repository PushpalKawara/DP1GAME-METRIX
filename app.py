import streamlit as st
import pandas as pd
import numpy as np
import re
import datetime
import matplotlib.pyplot as plt
from io import BytesIO
import xlsxwriter

# -------------------- STREAMLIT APP SETUP -------------------- #
st.set_page_config(page_title="DP1GAME METRIX", layout="wide")
st.title("📊 DP1GAME METRIX Dashboard")

# -------------------- FUNCTION TO EXPORT EXCEL -------------------- #

def generate_excel(df_summary, df_summary_Progression, retention_fig, drop_fig):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_summary.to_excel(writer, index=False, sheet_name='Summary', startrow=0, startcol=0)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_summary_Progression.to_excel(writer, index=False, sheet_name='Summary', startrow=1, startcol=5)

        workbook = writer.book
        worksheet = writer.sheets['Summary']

        # Adjust column width for table (A to E)
        worksheet.set_column('A:E', 18)

        # Insert Retention Chart at column K (11th col), row 5
        retention_img = BytesIO()
        retention_fig.savefig(retention_img, format='png')
        retention_img.seek(0)
        worksheet.insert_image('K5', 'retention_chart.png', {'image_data': retention_img})

        # Insert Drop Chart at column K, row 27 (gap of ~2 rows below previous chart)
        drop_img = BytesIO()
        drop_fig.savefig(drop_img, format='png')
        drop_img.seek(0)
        worksheet.insert_image('K27', 'drop_chart.png', {'image_data': drop_img})

    output.seek(0)
    return output




# -------------------- MAIN FUNCTION -------------------- #
def main():
    st.subheader("Step 1: Upload Files")
    col1, col2 = st.columns(2)

    with col1:
        file1 = st.file_uploader("📥 Upload Retention Base File", type=["csv"])
    with col2:
        file2 = st.file_uploader("📥 Upload Ad Event File", type=["csv"])

    st.subheader("📝 Editable Fields")
    version = st.text_input("Enter Version (e.g. v1.2.3)", value="v1.0.0")
    date_selected = st.date_input("Date Selected", value=datetime.date.today())
    check_date = st.date_input("Check Date", value=datetime.date.today() + datetime.timedelta(days=1))

    if file1 and file2:
        df1 = pd.read_csv(file1)
        df1.columns = df1.columns.str.strip().str.upper()

        level_columns = ['LEVEL', 'LEVEL PLAYED', 'TOTALLEVEL', 'TOTALLEVELPLAYED']
        level_col = next((col for col in df1.columns if col in level_columns), None)

        if level_col and 'USERS' in df1.columns:
            df1 = df1[[level_col, 'USERS']]

            def clean_level(x):
                try:
                    return int(re.search(r"(\d+)", str(x)).group(1))
                except:
                    return None

            df1['LEVEL_CLEAN'] = df1[level_col].apply(clean_level)
            df1.dropna(inplace=True)
            df1['LEVEL_CLEAN'] = df1['LEVEL_CLEAN'].astype(int)
            df1.sort_values('LEVEL_CLEAN', inplace=True)

            max_users = df1['USERS'].max()
            df1['Retention %'] = round((df1['USERS'] / max_users) * 100, 2)
            df1['Drop'] = ((df1['USERS'] - df1['USERS'].shift(-1)) / df1['USERS']).fillna(0) * 100
            df1['Drop'] = df1['Drop'].round(2)

            retention_20 = round(df1[df1['LEVEL_CLEAN'] == 20]['Retention %'].values[0], 2) if 20 in df1['LEVEL_CLEAN'].values else 0
            retention_50 = round(df1[df1['LEVEL_CLEAN'] == 50]['Retention %'].values[0], 2) if 50 in df1['LEVEL_CLEAN'].values else 0
            retention_75 = round(df1[df1['LEVEL_CLEAN'] == 75]['Retention %'].values[0], 2) if 75 in df1['LEVEL_CLEAN'].values else 0
            retention_100 = round(df1[df1['LEVEL_CLEAN'] == 100]['Retention %'].values[0], 2) if 100 in df1['LEVEL_CLEAN'].values else 0
            retention_150 = round(df1[df1['LEVEL_CLEAN'] == 150]['Retention %'].values[0], 2) if 150 in df1['LEVEL_CLEAN'].values else 0
            retention_200 = round(df1[df1['LEVEL_CLEAN'] == 200]['Retention %'].values[0], 2) if 200 in df1['LEVEL_CLEAN'].values else 0

            st.success("✅ File 1 cleaned and Retention/Drop calculated successfully!")
        else:
            st.error("❌ Required columns not found in file 1.")
            return

        df2 = pd.read_csv(file2)
        df2.columns = df2.columns.str.strip()

        if 'EVENT' in df2.columns and 'USERS' in df2.columns:
            df2 = df2[['EVENT', 'USERS']]
            df2['EVENT_CLEAN'] = df2['EVENT'].apply(
                lambda x: int(re.search(r"_(\d+)", str(x)).group(1)) if re.search(r"_(\d+)", str(x)) else None
            )
            df2.dropna(inplace=True)
            df2['EVENT_CLEAN'] = df2['EVENT_CLEAN'].astype(int)
            df2 = df2.sort_values('EVENT_CLEAN').reset_index(drop=True)

            max_users = df1['USERS'].max()
            first_row = pd.DataFrame({'EVENT': ['Assumed_0'], 'USERS': [max_users], 'EVENT_CLEAN': [0]})
            df2 = pd.concat([first_row, df2], ignore_index=True).sort_values('EVENT_CLEAN').reset_index(drop=True)

            df2['% of Users at Ad'] = round((df2['USERS'] / max_users) * 100, 2)

            ad10 = df2[df2['EVENT_CLEAN'] == 10]['% of Users at Ad'].values[0] if 10 in df2['EVENT_CLEAN'].values else 0
            ad20 = df2[df2['EVENT_CLEAN'] == 20]['% of Users at Ad'].values[0] if 20 in df2['EVENT_CLEAN'].values else 0
            ad40 = df2[df2['EVENT_CLEAN'] == 40]['% of Users at Ad'].values[0] if 40 in df2['EVENT_CLEAN'].values else 0
            ad70 = df2[df2['EVENT_CLEAN'] == 70]['% of Users at Ad'].values[0] if 70 in df2['EVENT_CLEAN'].values else 0
            ad100 = df2[df2['EVENT_CLEAN'] == 100]['% of Users at Ad'].values[0] if 100 in df2['EVENT_CLEAN'].values else 0

            #Step 1: Difference of Ads
            df2['Diff of Ads'] = df2['EVENT_CLEAN'].diff().fillna(df2['EVENT_CLEAN']).astype(int)

            # Step 2: Multi1 = USERS × Diff of Ads
            df2['Multi1'] = df2['USERS'] * df2['Diff of Ads']
            sum1 = df2['Multi1'].sum()

            # Step 3: Avg of Difference of Ads = (Diff of Ads) / 2
            df2['Avg Diff Ads'] = df2['Diff of Ads'] / 2

            # Step 4: Difference of Users = Prev Row - Current Row
            df2['Diff of Users'] = df2['USERS'].shift(1) - df2['USERS']
            df2['Diff of Users'] = df2['Diff of Users'].fillna(0).astype(int)

            # Step 5: Multi2 = Avg Diff Ads × Diff of Users
            df2['Multi2'] = df2['Avg Diff Ads'] * df2['Diff of Users']
            sum2 = df2['Multi2'].sum()

            # Step 6: Final Average Ads Per User
            avg_ads_per_user = round((sum1 + sum2) / max_users, 2)


            st.success(f"✅ Ad data processed successfully! Total Average Ads per User: {avg_ads_per_user}")
        else:
            st.error("❌ Required columns not found in file 2.")
            return

        # -------------------- PLOTS -------------------- #
        st.subheader("📈 Retention Chart (Levels 1–100)")
        retention_fig, ax = plt.subplots(figsize=(15, 6))
        df1_100 = df1[df1['LEVEL_CLEAN'] <= 100]

        ax.plot(df1_100['LEVEL_CLEAN'], df1_100['Retention %'],
                linestyle='-', color='#F57C00', linewidth=2, label='RETENTION')

        ax.set_xlim(1, 100)
        ax.set_ylim(0, 120)
        ax.set_xticks(np.arange(1, 101, 1))
        ax.set_yticks(np.arange(0, 121, 10))
        ax.set_xlabel("Level")
        ax.set_ylabel("% Of Users")
        ax.set_title(f"Retention Chart (Levels 1 - 100) | Version {version} | Date: {date_selected.strftime('%d-%m-%Y')}",
                     fontsize=12, fontweight='bold')

        ax.tick_params(axis='x', labelsize=6)
        ax.grid(True, linestyle='--', linewidth=0.5)

        for x, y in zip(df1_100['LEVEL_CLEAN'], df1_100['Retention %']):
            ax.text(x, -4, f"{int(y)}", ha='center', va='top', fontsize=7)

        ax.legend(loc='lower left', fontsize=8)
        plt.tight_layout()
        st.pyplot(retention_fig)

        st.subheader("📉 Drop Chart (Levels 1–100)")
        drop_fig, ax2 = plt.subplots(figsize=(15, 6))
        bars = ax2.bar(df1_100['LEVEL_CLEAN'], df1_100['Drop'], color='#EF5350', label='DROP RATE')

        ax2.set_xlim(1, 100)
        ax2.set_ylim(0, max(df1_100['Drop'].max(), 10) + 10)
        ax2.set_xticks(np.arange(1, 101, 1))
        ax2.set_yticks(np.arange(0, max(df1_100['Drop'].max(), 10) + 11, 5))
        ax2.set_xlabel("Level")
        ax2.set_ylabel("% Of Users Dropped")
        ax2.set_title(f"Drop Chart (Levels 1 - 100) | Version {version} | Date: {date_selected.strftime('%d-%m-%Y')}",
                      fontsize=12, fontweight='bold')

        ax2.tick_params(axis='x', labelsize=6)
        ax2.grid(True, linestyle='--', linewidth=0.5)

        for bar in bars:
            x = bar.get_x() + bar.get_width() / 2
            y = bar.get_height()
            ax2.text(x, -2, f"{y:.0f}", ha='center', va='top', fontsize=7)

        ax2.legend(loc='upper right', fontsize=8)
        plt.tight_layout()
        st.pyplot(drop_fig)

        # -------------------- STEP 6: MANUAL METRICS SECTION -------------------- #
        st.subheader("📝 Step 6: Pasteable Manual Metrics")
        default_summary_data = {
            "Version": version,
            "Date Selected": date_selected.strftime("%d-%b-%y"),
            "Check Date": check_date.strftime("%d-%b-%y"),
            "Level 1 Users": int(max_users),
            "Total Level Retention (20)": f"{retention_20}%",
            "Total Level Retention (50)": f"{retention_50}%",
            "Total Level Retention (75)": f"{retention_75}%",
            "Total Level Retention (100)": f"{retention_100}%",
            "Total Level Retention (150)": f"{retention_150}%",
            "Total Level Retention (200)": f"{retention_200}%",
            "% of Users at Ad 10": f"{ad10}%",
            "% of Users at Ad 20": f"{ad20}%",
            "% of Users at Ad 40": f"{ad40}%",
            "% of Users at Ad 70": f"{ad70}%",
            "% of Users at Ad 100": f"{ad100}%",
            "Avg Ads per User": avg_ads_per_user
        }

        df_summary = pd.DataFrame(list(default_summary_data.items()), columns=["Metric", "Value"])

        tab1, tab2 = st.tabs(["📥 Manual Input", "📋 Copy Summary"])
        with tab1:
            st.markdown("### 🔧 Enter Manual Metrics Here:")
            day1_retention = st.text_input("Day 1 Retention (%)", value="29.56%")
            day3_retention = st.text_input("Day 3 Retention (%)", value="13.26%")
            session_length = st.text_input("Session Length (in sec)", value="264.5")
            playtime_length = st.text_input("Playtime Length (in sec)", value="936.6")

            if st.button("Update Summary Table"):
                df_summary = df_summary.set_index("Metric")
                df_summary.loc["Day 1 Retention"] = day1_retention
                df_summary.loc["Day 3 Retention"] = day3_retention
                df_summary.loc["Session Length"] = f"{session_length} s"
                df_summary.loc["Playtime Length"] = f"{playtime_length} s"
                df_summary = df_summary.reset_index()

        # -------------------- DOWNLOAD FINAL EXCEL -------------------- #
        df_summary_Progression= df1[['LEVEL_CLEAN', 'USERS', 'Retention %', 'Drop']].rename(columns={'LEVEL_CLEAN': 'Level'})

        st.subheader("⬇️ Download Excel Report")
        # Show summary table
        st.dataframe(df_summary)

        # Generate and offer download button
        excel_data = generate_excel(df_summary, df_summary_Progression, retention_fig, drop_fig)
        st.download_button(
             label="📥 Download Excel Report",
             data=excel_data,
             file_name=f"DP1_METRIX_Report_{version}.xlsx",
             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

if __name__ == "__main__":
    main()
