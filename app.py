import streamlit as st
import pandas as pd
import numpy as np
import re
import datetime
import matplotlib.pyplot as plt
from io import BytesIO
import xlsxwriter

# Dummy username & password
USERNAME = "Pushpal@2025"
PASSWORD = "Pushpal@202512345"

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    with st.form("login"):
        st.subheader("🔐 Login Required")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login = st.form_submit_button("Login")

        if login:
            if username == USERNAME and password == PASSWORD:
                st.session_state.logged_in = True
                st.success("Logged in successfully!")
            else:
                st.error("Incorrect credentials")
    st.stop()

# -------------------- STREAMLIT APP SETUP -------------------- #
st.set_page_config(page_title="DP1GAME METRIX", layout="wide")
st.title("📊 DP1GAME METRIX Dashboard")

# -------------------- FUNCTION TO EXPORT EXCEL -------------------- #
def generate_excel(df_summary, df_summary_Progression, retention_fig, drop_fig):
    # Step 1: Remove duplicate levels from df_summary_Progression
    df_summary_Progression = df_summary_Progression.drop_duplicates(subset='Level', keep='first').reset_index(drop=True)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Write df_summary from column A (0), df_summary_Progression from column D (3)
        df_summary.to_excel(writer, index=False, sheet_name='Summary', startrow=0, startcol=0)
        df_summary_Progression.to_excel(writer, index=False, sheet_name='Summary', startrow=0, startcol=3)

        workbook = writer.book
        worksheet = writer.sheets['Summary']

        # Header format
        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#D9E1F2',
            'border': 1
        })

        # Cell format
        cell_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter'
        })

        # Red text and yellow fill format for Drop ≥ 3
        highlight_format = workbook.add_format({
            'font_color': 'red',
            'bg_color': 'yellow',
            'align': 'center',
            'valign': 'vcenter'
        })

        # Apply header format for df_summary
        for col_num, value in enumerate(df_summary.columns):
            worksheet.write(0, col_num, value, header_format)

        # Apply header format for df_summary_Progression (start from col 3)
        for col_num, value in enumerate(df_summary_Progression.columns):
            worksheet.write(0, col_num + 3, value, header_format)

        # Apply cell format to df_summary
        for row_num in range(1, len(df_summary) + 1):
            for col_num in range(len(df_summary.columns)):
                worksheet.write(row_num, col_num, df_summary.iloc[row_num - 1, col_num], cell_format)

        # Apply cell format to df_summary_Progression with conditional formatting
        for row_num in range(1, len(df_summary_Progression) + 1):
            for col_num in range(len(df_summary_Progression.columns)):
                value = df_summary_Progression.iloc[row_num - 1, col_num]
                col_name = df_summary_Progression.columns[col_num]

                # Check if this is the Drop column
                if col_name == 'Drop' and pd.notna(value) and value >= 3:
                    worksheet.write(row_num, col_num + 3, value, highlight_format)
                else:
                    worksheet.write(row_num, col_num + 3, value, cell_format)

        # Freeze top row
        worksheet.freeze_panes(1, 0)


        # ---------------------- DYNAMIC COLUMN WIDTH ---------------------- #
        # Set column widths dynamically for df_summary
        for i, col in enumerate(df_summary.columns):
            column_len = max(df_summary[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, column_len)

        # Set column widths dynamically for df_summary_Progression (start at col 3)
        for i, col in enumerate(df_summary_Progression.columns):
            column_len = max(df_summary_Progression[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i + 3, i + 3, column_len)
        # ------------------------------------------------------------------ #

        # # Adjust column width
        # worksheet.set_column('A:Z', 18)

        # Insert Retention Chart
        retention_img = BytesIO()
        retention_fig.savefig(retention_img, format='png')
        retention_img.seek(0)
        worksheet.insert_image('H2', 'retention_chart.png', {'image_data': retention_img})

        # Insert Drop Chart
        drop_img = BytesIO()
        drop_fig.savefig(drop_img, format='png')
        drop_img.seek(0)
        worksheet.insert_image('H37', 'drop_chart.png', {'image_data': drop_img})

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

    # Initialize session state variables
    if 'user_install' not in st.session_state:
        st.session_state.user_install = None

    if file1 and file2:
        # Process files and store base data
        df1 = pd.read_csv(file1)
        df1.columns = df1.columns.str.strip().str.upper()
        level_columns = ['LEVEL','Level' ,  'LEVELPLAYED', 'TOTALLEVELPLAYED', 'TOTALLEVELSPLAYED']
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

            # Store base data for reprocessing
            st.session_state.level_data = df1[['LEVEL_CLEAN', 'USERS']]
            
            # Calculate auto_max_users
            level1_users = df1[df1['LEVEL_CLEAN'] == 1]['USERS'].values[0] if 1 in df1['LEVEL_CLEAN'].values else 0
            level2_users = df1[df1['LEVEL_CLEAN'] == 2]['USERS'].values[0] if 2 in df1['LEVEL_CLEAN'].values else 0
            st.session_state.auto_max_users = level2_users if level2_users > level1_users else level1_users

        # Process Ad Event file
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
            st.session_state.event_data = df2[['EVENT_CLEAN', 'USERS']]

        # Calculate sum1 and sum2 for ads
        first_row = pd.DataFrame({'EVENT': ['Assumed_0'], 'USERS': [st.session_state.auto_max_users], 'EVENT_CLEAN': [0]})
        df2_full = pd.concat([first_row, df2], ignore_index=True).sort_values('EVENT_CLEAN').reset_index(drop=True)
        
        df2_full['Diff of Ads'] = df2_full['EVENT_CLEAN'].diff().fillna(df2_full['EVENT_CLEAN']).astype(int)
        df2_full['Multi1'] = df2_full['USERS'] * df2_full['Diff of Ads']
        sum1 = df2_full['Multi1'].sum()
        
        df2_full['Avg Diff Ads'] = df2_full['Diff of Ads'] / 2
        df2_full['Diff of Users'] = df2_full['USERS'].shift(1) - df2_full['USERS']
        df2_full['Diff of Users'] = df2_full['Diff of Users'].fillna(0).astype(int)
        df2_full['Multi2'] = df2_full['Avg Diff Ads'] * df2_full['Diff of Users']
        sum2 = df2_full['Multi2'].sum()
        
        st.session_state.sum1 = sum1
        st.session_state.sum2 = sum2

    # User Install Manual Input Tab
    st.subheader("👥 User Install Configuration")
    current_max_users = st.session_state.user_install if st.session_state.user_install else st.session_state.get('auto_max_users', 0)
    
    col1, col2 = st.columns(2)
    with col1:
        new_install = st.number_input("Enter Manual User Install Count", 
                                    min_value=0, 
                                    value=int(current_max_users))
    with col2:
        if st.button("Update User Install"):
            st.session_state.user_install = new_install
            st.success("User Install Count Updated!")

    # if 'level_data' in st.session_state and 'event_data' in st.session_state:
    #     # Get current max users
    #     current_max_users = st.session_state.user_install if st.session_state.user_install else st.session_state.auto_max_users

    #     # Recalculate metrics with current_max_users
    #     df1 = st.session_state.level_data.copy()
    #     df1['Retention %'] = round((df1['USERS'] / current_max_users) * 100, 2)
    #     df1['Drop'] = ((df1['USERS'] - df1['USERS'].shift(-1)) / df1['USERS']).fillna(0) * 100
    #     df1['Drop'] = df1['Drop'].round(2)

    #     # Recalculate retention milestones
    #     retention_20 = round(df1[df1['LEVEL_CLEAN'] == 20]['Retention %'].values[0], 2) if 20 in df1['LEVEL_CLEAN'].values else 0
    #     retention_50 = round(df1[df1['LEVEL_CLEAN'] == 50]['Retention %'].values[0], 2) if 50 in df1['LEVEL_CLEAN'].values else 0
    #     retention_75 = round(df1[df1['LEVEL_CLEAN'] == 75]['Retention %'].values[0], 2) if 75 in df1['LEVEL_CLEAN'].values else 0
    #     retention_100 = round(df1[df1['LEVEL_CLEAN'] == 100]['Retention %'].values[0], 2) if 100 in df1['LEVEL_CLEAN'].values else 0
    #     retention_150 = round(df1[df1['LEVEL_CLEAN'] == 150]['Retention %'].values[0], 2) if 150 in df1['LEVEL_CLEAN'].values else 0
    #     retention_200 = round(df1[df1['LEVEL_CLEAN'] == 200]['Retention %'].values[0], 2) if 200 in df1['LEVEL_CLEAN'].values else 0

    #     # Recalculate ad metrics
    #     df2 = st.session_state.event_data.copy()
    #     first_row = pd.DataFrame({'EVENT': ['Assumed_0'], 'USERS': [current_max_users], 'EVENT_CLEAN': [0]})
    #     df2_full = pd.concat([first_row, df2], ignore_index=True).sort_values('EVENT_CLEAN').reset_index(drop=True)
    #     df2_full['% of Users at Ad'] = round((df2_full['USERS'] / current_max_users) * 100, 2)
        
    #     ad10 = df2_full[df2_full['EVENT_CLEAN'] == 10]['% of Users at Ad'].values[0] if 10 in df2_full['EVENT_CLEAN'].values else 0
    #     ad20 = df2_full[df2_full['EVENT_CLEAN'] == 20]['% of Users at Ad'].values[0] if 20 in df2_full['EVENT_CLEAN'].values else 0
    #     ad40 = df2_full[df2_full['EVENT_CLEAN'] == 40]['% of Users at Ad'].values[0] if 40 in df2_full['EVENT_CLEAN'].values else 0
    #     ad70 = df2_full[df2_full['EVENT_CLEAN'] == 70]['% of Users at Ad'].values[0] if 70 in df2_full['EVENT_CLEAN'].values else 0
    #     ad100 = df2_full[df2_full['EVENT_CLEAN'] == 100]['% of Users at Ad'].values[0] if 100 in df2_full['EVENT_CLEAN'].values else 0

        
        
    #     # Recalculate average ads
    #     avg_ads_per_user = round((st.session_state.sum1 + st.session_state.sum2) / current_max_users, 2)
    if 'level_data' in st.session_state and 'event_data' in st.session_state:
        # Get current max users
        current_max_users = st.session_state.user_install if st.session_state.user_install else st.session_state.get('auto_max_users', 0)

        # Recalculate metrics with current_max_users
        df1 = st.session_state.level_data.copy()
        df1['Retention %'] = round((df1['USERS'] / current_max_users) * 100, 2)
        df1['Drop'] = ((df1['USERS'] - df1['USERS'].shift(-1)) / df1['USERS']).fillna(0) * 100
        df1['Drop'] = df1['Drop'].round(2)

        # ... [Retention milestone calculations remain the same] ...
        # Recalculate retention milestones
        retention_20 = round(df1[df1['LEVEL_CLEAN'] == 20]['Retention %'].values[0], 2) if 20 in df1['LEVEL_CLEAN'].values else 0
        retention_50 = round(df1[df1['LEVEL_CLEAN'] == 50]['Retention %'].values[0], 2) if 50 in df1['LEVEL_CLEAN'].values else 0
        retention_75 = round(df1[df1['LEVEL_CLEAN'] == 75]['Retention %'].values[0], 2) if 75 in df1['LEVEL_CLEAN'].values else 0
        retention_100 = round(df1[df1['LEVEL_CLEAN'] == 100]['Retention %'].values[0], 2) if 100 in df1['LEVEL_CLEAN'].values else 0
        retention_150 = round(df1[df1['LEVEL_CLEAN'] == 150]['Retention %'].values[0], 2) if 150 in df1['LEVEL_CLEAN'].values else 0
        retention_200 = round(df1[df1['LEVEL_CLEAN'] == 200]['Retention %'].values[0], 2) if 200 in df1['LEVEL_CLEAN'].values else 0
        
        ad10 = df2_full[df2_full['EVENT_CLEAN'] == 10]['% of Users at Ad'].values[0] if 10 in df2_full['EVENT_CLEAN'].values else 0
        ad20 = df2_full[df2_full['EVENT_CLEAN'] == 20]['% of Users at Ad'].values[0] if 20 in df2_full['EVENT_CLEAN'].values else 0
        ad40 = df2_full[df2_full['EVENT_CLEAN'] == 40]['% of Users at Ad'].values[0] if 40 in df2_full['EVENT_CLEAN'].values else 0
        ad70 = df2_full[df2_full['EVENT_CLEAN'] == 70]['% of Users at Ad'].values[0] if 70 in df2_full['EVENT_CLEAN'].values else 0
        ad100 = df2_full[df2_full['EVENT_CLEAN'] == 100]['% of Users at Ad'].values[0] if 100 in df2_full['EVENT_CLEAN'].values else 0


    

        # Recalculate ad metrics with current_max_users
        df2 = st.session_state.event_data.copy()
        first_row = pd.DataFrame({'EVENT': ['Assumed_0'], 'USERS': [current_max_users], 'EVENT_CLEAN': [0]})
        df2_full = pd.concat([first_row, df2], ignore_index=True).sort_values('EVENT_CLEAN').reset_index(drop=True)
        
        # Recalculate ad sums with current user install
        df2_full['Diff of Ads'] = df2_full['EVENT_CLEAN'].diff().fillna(df2_full['EVENT_CLEAN']).astype(int)
        df2_full['Multi1'] = df2_full['USERS'] * df2_full['Diff of Ads']
        sum1 = df2_full['Multi1'].sum()
        
        df2_full['Avg Diff Ads'] = df2_full['Diff of Ads'] / 2
        df2_full['Diff of Users'] = df2_full['USERS'].shift(1) - df2_full['USERS']
        df2_full['Diff of Users'] = df2_full['Diff of Users'].fillna(0).astype(int)
        df2_full['Multi2'] = df2_full['Avg Diff Ads'] * df2_full['Diff of Users']
        sum2 = df2_full['Multi2'].sum()
        
        # Calculate average ads with current user install
        avg_ads_per_user = round((sum1 + sum2) / current_max_users, 2)  # Corrected line
    

        

        # -------------------- Retention Chart -------------------- #

        st.subheader("📈 Retention Chart (Levels 1–100)")
        retention_fig, ax = plt.subplots(figsize=(15, 7))
        df1_100 = df1[df1['LEVEL_CLEAN'] <= 100]

        ax.plot(df1_100['LEVEL_CLEAN'], df1_100['Retention %'],
                linestyle='-', color='#F57C00', linewidth=2, label='RETENTION')

        ax.set_xlim(1, 100)
        ax.set_ylim(0, 120)
        ax.set_xticks(np.arange(1, 101, 1))
        ax.set_yticks(np.arange(0, 121, 10))

        # Set x and y labels with padding
        ax.set_xlabel("Level", labelpad=15)  # space between x-label and ticks
        ax.set_ylabel("% Of Users", labelpad=15)  # space between y-label and ticks

        ax.set_title(f"Retention Chart (Levels 1 - 100) | Version {version} | Date: {date_selected.strftime('%d-%m-%Y')}",
                     fontsize=12, fontweight='bold')

        # Customizing x tick labels: bold if multiple of 5
        xtick_labels = []
        for val in np.arange(1, 101, 1):
            if val % 5 == 0:
                xtick_labels.append(f"$\\bf{{{val}}}$")  # Bold using LaTeX formatting
            else:
                xtick_labels.append(str(val))
        ax.set_xticklabels(xtick_labels, fontsize=6)

        ax.tick_params(axis='x', labelsize=6)
        ax.grid(True, linestyle='--', linewidth=0.5)

        #  Annotate data points BELOW x-axis without overlap
        for x, y in zip(df1_100['LEVEL_CLEAN'], df1_100['Retention %']):
            ax.text(x, -5, f"{int(y)}", ha='center', va='top', fontsize=7)

        ax.legend(loc='lower left', fontsize=8)
        # Add space around plot to prevent label clipping
        # Fix clipping
        plt.tight_layout(rect=[0, 0.03, 1, 0.97])
        # plt.tight_layout()
        st.pyplot(retention_fig)

        # -------------------- Drop Chart -------------------- #
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

        # Customizing x tick labels: bold if multiple of 5
        xtick_labels = []
        for val in np.arange(1, 101, 1):
            if val % 5 == 0:
                xtick_labels.append(f"$\\bf{{{val}}}$")  # Bold using LaTeX formatting
            else:
                xtick_labels.append(str(val))
        ax2.set_xticklabels(xtick_labels, fontsize=6)

        ax2.tick_params(axis='x', labelsize=6)
        ax2.grid(True, linestyle='--', linewidth=0.5)


        ax2.tick_params(axis='x', labelsize=6)
        ax2.grid(True, linestyle='--', linewidth=0.5)


        # Annotate data points below x-axis
        for bar in bars:
            x = bar.get_x() + bar.get_width() / 2
            y = bar.get_height()
            ax2.text(x, -2, f"{y:.0f}", ha='center', va='top', fontsize=7)

        ax2.legend(loc='upper right', fontsize=8)
        plt.tight_layout()
        st.pyplot(drop_fig)

        # -------------------- STEP 6: MANUAL METRICS SECTION -------------------- #
        st.subheader("📝 Step 6: Pasteable Manual Metrics")
        # Update summary data with current_max_users
        default_summary_data = {
            "Version": version,
            "Date Selected": date_selected.strftime("%d-%b-%y"),
            "Check Date": check_date.strftime("%d-%b-%y"),
            "User Install Count": int(current_max_users),
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
