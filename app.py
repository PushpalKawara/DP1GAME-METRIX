import streamlit as st
import pandas as pd
import numpy as np
import re
import datetime
import matplotlib.pyplot as plt
from io import BytesIO
import xlsxwriter


 Streamlit App Setup
st.set_page_config(page_title="DP1GAME METRIX", layout="wide")
st.title("📊 DP1GAME METRIX Dashboard")

# Excel generation function with chart
def generate_excel(df_summary, fig):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_summary.to_excel(writer, index=False, sheet_name='Summary')
        workbook = writer.book
        worksheet = writer.sheets['Summary']

        # Insert chart image
        chart_img = BytesIO()
        fig.savefig(chart_img, format='png')
        chart_img.seek(0)
        worksheet.insert_image('D3', 'chart.png', {'image_data': chart_img})
    output.seek(0)
    return output


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

    st.subheader("📝 Editable Fields")
    version = st.text_input("Enter Version (e.g. v1.2.3)", value="v1.0.0")
    date_selected = st.date_input("Date Selected", value=datetime.date.today())
    check_date = st.date_input("Check Date", value=datetime.date.today() + datetime.timedelta(days=1))



    if file1 and file2:
        # -------------------- STEP 2: CLEAN FILE 1 -------------------- #
df1 = pd.read_csv(file1)
df1.columns = df1.columns.str.strip().str.upper()  # Normalize column names

# Possible LEVEL column names
level_columns = ['LEVEL', 'LEVEL PLAYED', 'TOTALLEVEL', 'TOTALLEVELPLAYED']
level_col = next((col for col in df1.columns if col in level_columns), None)

if level_col and 'USERS' in df1.columns:
    df1 = df1[[level_col, 'USERS']]

    # Clean level column using regex
    def clean_level(x):
        try:
            return int(re.search(r"(\d+)", str(x)).group(1))
        except:
            return None

    df1['LEVEL_CLEAN'] = df1[level_col].apply(clean_level)
    df1.dropna(inplace=True)
    df1['LEVEL_CLEAN'] = df1['LEVEL_CLEAN'].astype(int)
    df1.sort_values('LEVEL_CLEAN', inplace=True)

    # Retention Calculation
    max_users = df1['USERS'].max()
    df1['Retention %'] = round((df1['USERS'] / max_users) * 100, 2)

    # Drop Calculation
    df1['Drop'] = ((df1['USERS'] - df1['USERS'].shift(-1)) / df1['USERS']).fillna(0) * 100
    df1['Drop'] = df1['Drop'].round(2)

    st.success("✅ File 1 cleaned and Retention/Drop calculated successfully!")
else:
    st.error("❌ Required columns not found in file 1.")
    return


      # -------------------- STEP 3: CLEAN FILE 2 -------------------- #
df2 = pd.read_csv(file2)
df2.columns = df2.columns.str.strip()  # Remove extra spaces from column names

if 'EVENT' in df2.columns and 'USERS' in df2.columns:
    df2 = df2[['EVENT', 'USERS']]  # Keep only 'EVENT' and 'USERS' columns

    # Extract the ad number from the EVENT column
    df2['EVENT_CLEAN'] = df2['EVENT'].apply(
        lambda x: int(re.search(r"_(\d+)", str(x)).group(1)) if re.search(r"_(\d+)", str(x)) else None
    )

       # Drop rows where 'EVENT_CLEAN' is NaN
    df2.dropna(inplace=True)
    df2['EVENT_CLEAN'] = df2['EVENT_CLEAN'].astype(int)
    df2 = df2.sort_values('EVENT_CLEAN').reset_index(drop=True)

    # Add starting row for 0 ad and max users
    max_users = df2['USERS'].max()
    first_row = pd.DataFrame({'EVENT': ['Assumed_0'], 'USERS': [max_users], 'EVENT_CLEAN': [0]})
    df2 = pd.concat([first_row, df2], ignore_index=True).sort_values('EVENT_CLEAN').reset_index(drop=True)

    # % of Users at Ad
    df2['% of Users at Ad'] = round((df2['USERS'] / max_users) * 100, 2)

    # Difference in Ads
    df2['Diff of Ads'] = df2['EVENT_CLEAN'].diff().fillna(df2['EVENT_CLEAN']).astype(int)
    df2['Multi'] = df2['Diff of Ads'] * df2['USERS']

    # Average difference of ads (from event steps, e.g., (10 - 0), (20 - 10), ...)
    event_diffs = df2['EVENT_CLEAN'].diff().dropna().tolist()
    avg_diff = round(sum(event_diffs) / len(event_diffs), 2)

    # Difference in Users
    df2['Diff of Users'] = df2['USERS'].diff().fillna(0).astype(int)
    df2['Multi 2'] = avg_diff * df2['Diff of Users']

    # Sum of both calculations
    first_sum = df2['Multi'].sum()
    second_sum = df2['Multi 2'].sum()

    # Calculate average ads per user
    avg_ads_per_user = round((first_sum + second_sum) / max_users, 2)

    # Show success
    st.success(f"✅ Ad data processed successfully! Total Average Ads per User: {avg_ads_per_user}")

else:
    st.error("❌ Required columns not found in file 2.")	 


    # -------------------- STEP 4: CHARTS -------------------- #

# Chart Plot 1 (Levels 1–100)
st.subheader("📈 Retention Chart (Levels 1–100)")

# Auto version and date
version = "0.59"
today = date.today().strftime("%d-%m-%Y")

fig, ax = plt.subplots(figsize=(15, 6))
df1_100 = df1[df1['LEVEL_CLEAN'] <= 100]

# Plot Retention Line
ax.plot(df1_100['LEVEL_CLEAN'], df1_100['Retention %'],
        linestyle='-', color='#F57C00', linewidth=2, label='RETENTION')

# Customize axes
ax.set_xlim(1, 100)
ax.set_ylim(0, 120)
ax.set_yticks(np.arange(0, 121, 10))  # Y-axis ticks from 0% to 120%
ax.set_xticks(np.arange(1, 101, 1))
ax.set_xlabel("Level")
ax.set_ylabel("% Of Users")
ax.set_title(f"Retention Chart (Levels 1 - 100)  | Version {version} | Date: {today}",
             fontsize=12, fontweight='bold', loc='center')

# Reduce x-axis tick label size
ax.tick_params(axis='x', labelsize=5)
ax.grid(True, which='both', linestyle='--', linewidth=0.5)

# Show retention % below each level
for x, y in zip(df1_100['LEVEL_CLEAN'], df1_100['Retention %']):
    ax.text(x, -4, f"{int(y)}%", ha='center', va='top', fontsize=6, rotation=0)

# Add legend
ax.legend(loc='lower left', fontsize=8)

plt.tight_layout()
st.pyplot(fig)


# Chart Plot 2: Drop Chart (Levels 1–100)
st.subheader("📉 Drop Chart (Levels 1–100)")

# Calculate Drop Percentage
df1['Drop'] = ((df1['USERS'] - df1['USERS'].shift(-1)) / df1['USERS']).fillna(0) * 100
df1['Drop'] = df1['Drop'].round(2)

# Filter data for Levels 1–100
df1_100 = df1[df1['LEVEL_CLEAN'] <= 100]

# Plot Drop Bar Chart
fig2, ax2 = plt.subplots(figsize=(15, 6))
bars = ax2.bar(df1_100['LEVEL_CLEAN'], df1_100['Drop'], color='#EF5350', label='DROP RATE')

# Customize axes
ax2.set_xlim(1, 100)
ax2.set_ylim(0, max(df1_100['Drop'].max(), 10) + 10)  # Dynamic height
ax2.set_xticks(np.arange(1, 101, 1))
ax2.set_yticks(np.arange(0, max(df1_100['Drop'].max(), 10) + 11, 5))
ax2.set_xlabel("Level")
ax2.set_ylabel("% Of Users Dropped")
ax2.set_title(f"Drop Chart (Levels 1 - 100) | Version {version} | Date: {today}",
              fontsize=12, fontweight='bold', loc='center')

# Reduce x-axis tick label size
ax2.tick_params(axis='x', labelsize=5)
ax2.grid(True, which='both', linestyle='--', linewidth=0.5)

# Show drop % below each bar
for bar in bars:
    x = bar.get_x() + bar.get_width() / 2
    y = bar.get_height()
    ax2.text(x, -2, f"{y:.0f}%", ha='center', va='top', fontsize=6)

# Add legend
ax2.legend(loc='upper right', fontsize=8)

plt.tight_layout()
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

# Default summary metrics shown before manual update
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

# Store in dataframe
df_summary = pd.DataFrame(list(default_summary_data.items()), columns=["Metric", "Value"])

# UI Tabs
tab1, tab2 = st.tabs(["📥 Manual Input", "📋 Copy Summary"])

# Flag for manual update
manual_updated = False

with tab1:
    st.markdown("### 🔧 Enter Manual Metrics Here:")
    day1_retention = st.text_input("Day 1 Retention (%)", value="29.56%")
    day3_retention = st.text_input("Day 3 Retention (%)", value="13.26%")
    session_length = st.text_input("Session Length (in sec)", value="264.5")
    playtime_length = st.text_input("Playtime Length (in sec)", value="936.6")

    if st.button("Update Summary Table"):
        # Add manual metrics to dataframe
        df_summary = df_summary.set_index("Metric")

        df_summary.loc["Day 1 Retention"] = day1_retention
        df_summary.loc["Day 3 Retention"] = day3_retention
        df_summary.loc["Session Length"] = f"{session_length} s"
        df_summary.loc["Playtime length"] = f"{playtime_length} s"

        df_summary = df_summary.reset_index()
        st.success("Summary table updated with manual values.")
        manual_updated = True

with tab2:
    st.markdown("### 📋 Final Summary Table (Paste Anywhere)")
    st.dataframe(df_summary, use_container_width=True)

# Export section
st.subheader("📥 Export Excel Report")
if st.button("Generate & Download Excel"):
    excel_output = generate_excel(df_summary, fig)
    st.download_button(
        label="📩 Download Excel File",
        data=excel_output.getvalue(),
        file_name=f"DP1GAME_METRIX_{version}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


    else:
        st.warning("⬆️ Please upload both files to continue.")

if __name__ == "__main__":
    main()
