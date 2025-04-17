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
def generate_excel(df_summary, fig):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_summary.to_excel(writer, index=False, sheet_name='Summary')
        workbook = writer.book
        worksheet = writer.sheets['Summary']
        chart_img = BytesIO()
        fig.savefig(chart_img, format='png')
        chart_img.seek(0)
        worksheet.insert_image('D3', 'chart.png', {'image_data': chart_img})
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
        # -------------------- PROCESS FILE 1 -------------------- #
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

            st.success("✅ File 1 cleaned and Retention/Drop calculated successfully!")
        else:
            st.error("❌ Required columns not found in file 1.")
            return

        # -------------------- PROCESS FILE 2 -------------------- #
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

            max_users = df2['USERS'].max()
            first_row = pd.DataFrame({'EVENT': ['Assumed_0'], 'USERS': [max_users], 'EVENT_CLEAN': [0]})
            df2 = pd.concat([first_row, df2], ignore_index=True).sort_values('EVENT_CLEAN').reset_index(drop=True)

            df2['% of Users at Ad'] = round((df2['USERS'] / max_users) * 100, 2)
            df2['Diff of Ads'] = df2['EVENT_CLEAN'].diff().fillna(df2['EVENT_CLEAN']).astype(int)
            df2['Multi'] = df2['Diff of Ads'] * df2['USERS']

            event_diffs = df2['EVENT_CLEAN'].diff().dropna().tolist()
            avg_diff = round(sum(event_diffs) / len(event_diffs), 2)

            df2['Diff of Users'] = df2['USERS'].diff().fillna(0).astype(int)
            df2['Multi 2'] = avg_diff * df2['Diff of Users']

            first_sum = df2['Multi'].sum()
            second_sum = df2['Multi 2'].sum()

            avg_ads_per_user = round((first_sum + second_sum) / max_users, 2)

            st.success(f"✅ Ad data processed successfully! Total Average Ads per User: {avg_ads_per_user}")
        else:
            st.error("❌ Required columns not found in file 2.")
            return

        # -------------------- PLOTS -------------------- #
        st.subheader("📈 Retention Chart (Levels 1–100)")
        fig, ax = plt.subplots(figsize=(15, 6))
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

        ax.tick_params(axis='x', labelsize=5)
        ax.grid(True, linestyle='--', linewidth=0.5)

        for x, y in zip(df1_100['LEVEL_CLEAN'], df1_100['Retention %']):
            ax.text(x, -4, f"{int(y)}%", ha='center', va='top', fontsize=6)

        ax.legend(loc='lower left', fontsize=8)
        plt.tight_layout()
        st.pyplot(fig)

        st.subheader("📉 Drop Chart (Levels 1–100)")
        fig2, ax2 = plt.subplots(figsize=(15, 6))
        bars = ax2.bar(df1_100['LEVEL_CLEAN'], df1_100['Drop'], color='#EF5350', label='DROP RATE')

        ax2.set_xlim(1, 100)
        ax2.set_ylim(0, max(df1_100['Drop'].max(), 10) + 10)
        ax2.set_xticks(np.arange(1, 101, 1))
        ax2.set_yticks(np.arange(0, max(df1_100['Drop'].max(), 10) + 11, 5))
        ax2.set_xlabel("Level")
        ax2.set_ylabel("% Of Users Dropped")
        ax2.set_title(f"Drop Chart (Levels 1 - 100) | Version {version} | Date: {date_selected.strftime('%d-%m-%Y')}",
                      fontsize=12, fontweight='bold')

        ax2.tick_params(axis='x', labelsize=5)
        ax2.grid(True, linestyle='--', linewidth=0.5)

        for bar in bars:
            x = bar.get_x() + bar.get_width() / 2
            y = bar.get_height()
            ax2.text(x, -2, f"{y:.0f}%", ha='center', va='top', fontsize=6)

        ax2.legend(loc='upper right', fontsize=8)
        plt.tight_layout()
        st.pyplot(fig2)

        # -------------------- FINAL SUMMARY -------------------- #
        st.subheader("📋 Final Summary Table")
        retention_20 = df1[df1['LEVEL_CLEAN'] == 20]['Retention %'].values[0] if 20 in df1['LEVEL_CLEAN'].values else None
        summary_data = {
            "Version": version,
            "Date Selected": date_selected.strftime("%d-%b-%y"),
            "Check Date": check_date.strftime("%d-%b-%y"),
            "Level 1 Users": int(max_users),
            "Retention at Level 20": f"{retention_20}%" if retention_20 else "N/A",
            "Average Ads per User": avg_ads_per_user
        }
        summary_df = pd.DataFrame(list(summary_data.items()), columns=["Metric", "Value"])
        st.dataframe(summary_df)

        # -------------------- DOWNLOAD BUTTON -------------------- #
        excel_data = generate_excel(summary_df, fig)
        st.download_button(label="📥 Download Summary Report", data=excel_data, file_name="DP1_Metrix_Summary.xlsx")

# -------------------- RUN APP -------------------- #
if __name__ == "__main__":
    main()
