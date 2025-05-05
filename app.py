import streamlit as st
import pandas as pd
import numpy as np
import re
import datetime
import matplotlib.pyplot as plt
from io import BytesIO
import xlsxwriter

# Dummy username & password
USERNAME = "-----"
PASSWORD = "---"

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
    # ... (keep the existing Excel generation code unchanged) ...

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

    if 'level_data' in st.session_state and 'event_data' in st.session_state:
        # Get current max users
        current_max_users = st.session_state.user_install if st.session_state.user_install else st.session_state.auto_max_users

        # Recalculate metrics with current_max_users
        df1 = st.session_state.level_data.copy()
        df1['Retention %'] = round((df1['USERS'] / current_max_users) * 100, 2)
        df1['Drop'] = ((df1['USERS'] - df1['USERS'].shift(-1)) / df1['USERS']).fillna(0) * 100
        df1['Drop'] = df1['Drop'].round(2)

        # Recalculate retention milestones
        retention_20 = round(df1[df1['LEVEL_CLEAN'] == 20]['Retention %'].values[0], 2) if 20 in df1['LEVEL_CLEAN'].values else 0
        retention_50 = round(df1[df1['LEVEL_CLEAN'] == 50]['Retention %'].values[0], 2) if 50 in df1['LEVEL_CLEAN'].values else 0
        retention_75 = round(df1[df1['LEVEL_CLEAN'] == 75]['Retention %'].values[0], 2) if 75 in df1['LEVEL_CLEAN'].values else 0
        retention_100 = round(df1[df1['LEVEL_CLEAN'] == 100]['Retention %'].values[0], 2) if 100 in df1['LEVEL_CLEAN'].values else 0
        retention_150 = round(df1[df1['LEVEL_CLEAN'] == 150]['Retention %'].values[0], 2) if 150 in df1['LEVEL_CLEAN'].values else 0
        retention_200 = round(df1[df1['LEVEL_CLEAN'] == 200]['Retention %'].values[0], 2) if 200 in df1['LEVEL_CLEAN'].values else 0

        # Recalculate ad metrics
        df2 = st.session_state.event_data.copy()
        first_row = pd.DataFrame({'EVENT': ['Assumed_0'], 'USERS': [current_max_users], 'EVENT_CLEAN': [0]})
        df2_full = pd.concat([first_row, df2], ignore_index=True).sort_values('EVENT_CLEAN').reset_index(drop=True)
        df2_full['% of Users at Ad'] = round((df2_full['USERS'] / current_max_users) * 100, 2)
        
        ad10 = df2_full[df2_full['EVENT_CLEAN'] == 10]['% of Users at Ad'].values[0] if 10 in df2_full['EVENT_CLEAN'].values else 0
        ad20 = df2_full[df2_full['EVENT_CLEAN'] == 20]['% of Users at Ad'].values[0] if 20 in df2_full['EVENT_CLEAN'].values else 0
        ad40 = df2_full[df2_full['EVENT_CLEAN'] == 40]['% of Users at Ad'].values[0] if 40 in df2_full['EVENT_CLEAN'].values else 0
        ad70 = df2_full[df2_full['EVENT_CLEAN'] == 70]['% of Users at Ad'].values[0] if 70 in df2_full['EVENT_CLEAN'].values else 0
        ad100 = df2_full[df2_full['EVENT_CLEAN'] == 100]['% of Users at Ad'].values[0] if 100 in df2_full['EVENT_CLEAN'].values else 0

        # Recalculate average ads
        avg_ads_per_user = round((st.session_state.sum1 + st.session_state.sum2) / current_max_users, 2)

        # ... (keep the rest of the plotting and Excel generation code unchanged) ...

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

        # ... (rest of the code remains the same) ...

if __name__ == "__main__":
    main()
