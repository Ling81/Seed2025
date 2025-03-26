import streamlit as st
import pandas as pd
import gspread
import os
import matplotlib.pyplot as plt
from oauth2client.service_account import ServiceAccountCredentials

# ------------------- GOOGLE SHEETS AUTHENTICATION -------------------
def authenticate_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("google_credentials.json", scope)
    client = gspread.authorize(creds)
    return client

# ------------------- FUNCTION TO SAVE DATA TO GOOGLE SHEETS -------------------
def save_data_to_google_sheets(data, learner_name):
    client = authenticate_google_sheets()
    
    # Link to specific learner's Google Sheet (replace with your actual sheet name)
    sheet_name = f"{learner_name}_Data"
    try:
        sheet = client.open(sheet_name).sheet1  # Open the first sheet
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"Google Sheet '{sheet_name}' not found. Ensure the sheet is created and shared with your service account.")
        return

    row = list(data.values())
    sheet.append_row(row)
    st.success(f"✅ Data saved to Google Sheets: {sheet_name}")

# ------------------- SESSION DETAILS -------------------
st.sidebar.title("📋 Navigation")
menu = st.sidebar.radio("Go to", ["Session Details", "Cold Probe Data", "Trial-by-Trial Data", "Task Analysis", "Behavior Duration", "Progress & Reports"])

if menu == "Session Details":
    st.header("📅 Session Details")
    
    # Inputs for session details
    date = st.date_input("Select Date")
    start_time = st.selectbox("Start Time", [f"{h}:00" for h in range(9, 18)])  # 9 AM - 5 PM
    end_time = st.selectbox("End Time", [f"{h}:00" for h in range(9, 18)])  
    therapist_name = st.text_input("Therapist's Name")
    learner_name = st.text_input("Learner's Name (Used for Google Sheet)")

    # Save button
    if st.button("💾 Save Session Details"):
        session_data = {
            "Date": date,
            "Start Time": start_time,
            "End Time": end_time,
            "Therapist": therapist_name,
            "Learner": learner_name
        }
        save_data_to_google_sheets(session_data, learner_name)

# ------------------- COLD PROBE DATA -------------------
elif menu == "Cold Probe Data":
    st.header("📊 Cold Probe Data")

    targets = st.text_area("Enter targets (comma-separated)").split(",")

    if targets:
        df = pd.DataFrame({"Target": targets, "Response": [""] * len(targets)})
        response_options = ["Y", "N", "NA"]
        for i in range(len(df)):
            df.at[i, "Response"] = st.selectbox(f"Response for {df.at[i, 'Target']}", response_options)

        if st.button("💾 Save Cold Probe Data"):
            save_data_to_google_sheets(df.to_dict(), learner_name)

# ------------------- TRIAL-BY-TRIAL DATA -------------------
elif menu == "Trial-by-Trial Data":
    st.header("🎯 Trial-by-Trial Data")

    targets = st.text_area("Enter up to 10 targets (comma-separated)").split(",")[:10]

    if targets:
        trial_data = {}
        for target in targets:
            st.subheader(target.strip())
            trials = [st.selectbox(f"Trial {i+1}", ["+", "p", "-", "I"], key=f"{target}_{i}") for i in range(10)]
            trial_data[target.strip()] = trials

        # Convert responses to percentage
        trial_results = {}
        for target, trials in trial_data.items():
            correct_count = trials.count("+") + trials.count("I")
            trial_results[target] = round((correct_count / 10) * 100, 2)  # Convert to %

        if st.button("💾 Save Trial Data"):
            save_data_to_google_sheets(trial_results, learner_name)

# ------------------- TASK ANALYSIS -------------------
elif menu == "Task Analysis":
    st.header("📌 Task Analysis")

    steps = st.text_area("Enter steps (comma-separated)").split(",")
    
    if steps:
        df = pd.DataFrame({"Step": steps, "Prompt Level": [""] * len(steps)})
        prompt_options = ["FP", "PP", "MP", "VI", "VP", "GP", "TD", "I"]
        for i in range(len(df)):
            df.at[i, "Prompt Level"] = st.selectbox(f"Prompt for {df.at[i, 'Step']}", prompt_options)
        
        if st.button("💾 Save Task Analysis Data"):
            save_data_to_google_sheets(df.to_dict(), learner_name)

# ------------------- BEHAVIOR DURATION TRACKING -------------------
elif menu == "Behavior Duration":
    st.header("⏳ Behavior Duration Tracking")

    duration_list = []
    if st.button("▶ Start Timer"):
        start_time = pd.Timestamp.now()
        st.session_state["start_time"] = start_time

    if st.button("⏹ Stop Timer"):
        if "start_time" in st.session_state:
            duration = (pd.Timestamp.now() - st.session_state["start_time"]).seconds
            duration_list.append(duration)
            st.success(f"Recorded episode duration: {duration} seconds")

    if st.button("💾 Save Behavior Duration Data"):
        total_duration = sum(duration_list)
        save_data_to_google_sheets({"Total Duration (s)": total_duration}, learner_name)

# ------------------- PROGRESS & REPORTS -------------------
elif menu == "Progress & Reports":
    st.header("📈 Progress & Reports")

    client = authenticate_google_sheets()
    try:
        sheet = client.open(f"{learner_name}_Data").sheet1
        data = pd.DataFrame(sheet.get_all_records())

        if not data.empty:
            fig, ax = plt.subplots(figsize=(8, 4))
            data.plot(kind="line", x="Date", y=[col for col in data.columns if "%" in col], ax=ax)
            plt.title("Cumulative Progress Over Time")
            plt.xlabel("Date")
            plt.ylabel("Performance (%)")
            st.pyplot(fig)

            st.subheader("📄 Auto-Generated Session Notes")
            session_summary = f"""
            **Date:** {data.iloc[-1]['Date']}
            **Therapist:** {data.iloc[-1]['Therapist']}
            **Learner:** {learner_name}
            **Performance Summary:** {data.iloc[-1].to_dict()}
            """
            st.text_area("Session Notes", session_summary, height=200)
    except:
        st.error("No data found! Ensure the learner name is correct and data has been saved.")

