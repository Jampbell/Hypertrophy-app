import streamlit as st
import datetime
import time
import os
import pandas as pd
import requests

# Page Layout Configuration
st.set_page_config(page_title="HyperCustom Fit", layout="wide", page_icon="🏋️‍♂️")
st.title("🏋️‍♂️ HyperCustom Fit Tracker")

# ────────────────────────────────────────────────────────
# PERSISTENT DATABASE SYSTEM
# ────────────────────────────────────────────────────────
DB_FILE = "workout_database.csv"

def save_set_to_csv(date_str, routine_name, exercise_name, set_num, weight, reps):
    new_row = pd.DataFrame([{
        "Date": date_str,
        "Routine": routine_name,
        "Exercise": exercise_name,
        "Set": set_num,
        "Weight_lbs": weight,
        "Reps": reps
    }])
    if not os.path.exists(DB_FILE):
        new_row.to_csv(DB_FILE, index=False)
    else:
        new_row.to_csv(DB_FILE, mode='a', header=False, index=False)

def load_workout_history():
    if os.path.exists(DB_FILE):
        try:
            return pd.read_csv(DB_FILE)
        except:
            return pd.DataFrame()
    return pd.DataFrame()

# Navigation Sidebar
menu = st.sidebar.radio("Menu", ["📝 Log Today's Lift", "📈 View Training Logs", "🤖 Chat with AI Coach"])

# Training Program Matrix
routine = {
    "Day 1: Upper Focus": [
        {"name": "Barbell Bench Press", "range": "8-10 reps", "sets": 3},
        {"name": "Barbell Row", "range": "8-12 reps", "sets": 3},
        {"name": "Overhead Barbell Press", "range": "8-10 reps", "sets": 3},
        {"name": "Lat Pulldowns (Cable Combo)", "range": "10-12 reps", "sets": 3},
        {"name": "Dumbbell Bicep Curls", "range": "10-12 reps", "sets": 3},
        {"name": "Tricep Cable Pushdowns", "range": "12-15 reps", "sets": 3}
    ],
    "Day 2: Lower Focus": [
        {"name": "Safety Squat Bar (SSB) Squats", "range": "8-10 reps", "sets": 3},
        {"name": "Barbell Deadlift", "range": "6-8 reps", "sets": 2},
        {"name": "Dumbbell Romanian Deadlift", "range": "10-12 reps", "sets": 3},
        {"name": "35lb Kettlebell Goblet Squats", "range": "12-15 reps", "sets": 3},
        {"name": "Calf Raises (Bench Edge)", "range": "15 reps", "sets": 4}
    ],
    "Day 3: Full Body Blend": [
        {"name": "Incline Dumbbell Press", "range": "10-12 reps", "sets": 3},
        {"name": "Chest-Supported DB Row", "range": "10-12 reps", "sets": 3},
        {"name": "35lb Kettlebell Swings", "range": "15-20 reps", "sets": 3},
        {"name": "Dumbbell Lateral Raises", "range": "12-15 reps", "sets": 4},
        {"name": "Hammer Curls", "range": "10-12 reps", "sets": 3}
    ]
}

# --- SCREEN 1: LOGGING & BREAK TIMER ---
if menu == "📝 Log Today's Lift":
    st.header("Log Today's Workout")
    selected_day = st.selectbox("Choose Routine:", list(routine.keys()))
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("⏱️ Rest Break Timer")
    duration = st.sidebar.selectbox("Select Break Length:", [45, 60, 90, 120], index=1, format_func=lambda x: f"{x} Seconds")
    
    if st.sidebar.button("▶️ Start Rest Timer", use_container_width=True):
        progress_bar = st.sidebar.progress(0)
        status_text = st.sidebar.empty()
        for percent_complete in range(100):
            time.sleep(duration / 100)
            progress_bar.progress(percent_complete + 1)
            remaining = int(duration - (duration * (percent_complete / 100)))
            status_text.caption(f"⏳ {remaining}s remaining... Rest!")
        status_text.success("🚨 Time's Up! Begin your next set.")
        st.sidebar.balloons()
    
    workout_inputs = {}
    for ex in routine[selected_day]:
        st.markdown(f"#### 🔹 {ex['name']} *({ex['range']})*")
        cols = st.columns(ex['sets'])
        
        ex_inputs = []
        for i in range(ex['sets']):
            with cols[i]:
                st.caption(f"Set {i+1}")
                weight = st.number_input(f"Wt (lbs)", min_value=0.0, step=2.5, key=f"{ex['name']}_w_{i}")
                reps = st.number_input(f"Reps", min_value=0, step=1, key=f"{ex['name']}_r_{i}")
                ex_inputs.append((i+1, weight, reps))
        workout_inputs[ex['name']] = ex_inputs
        st.write("---")
        
    if st.button("Save Workout to History", type="primary"):
        today_str = datetime.date.today().strftime("%b %d, %Y")
        for ex_name, sets_data in workout_inputs.items():
            for set_num, weight, reps in sets_data:
                save_set_to_csv(today_str, selected_day, ex_name, set_num, weight, reps)
        st.success("💪 Workout securely written to permanent database memory!")

# --- SCREEN 2: PROGRESS LOGS ---
elif menu == "📈 View Training Logs":
    st.header("Your Completed Workouts")
    history_df = load_workout_history()
    
    if history_df.empty:
        st.warning("No logged sessions found in your permanent storage file yet.")
    else:
        unique_dates = history_df["Date"].unique()[::-1]
        for target_date in unique_dates:
            date_df = history_df[history_df["Date"] == target_date]
            routine_name = date_df["Routine"].iloc[0]
            
            with st.expander(f"📅 {target_date} — {routine_name}"):
                for ex_name in date_df["Exercise"].unique():
                    st.write(f"**{ex_name}**")
                    ex_df = date_df[date_df["Exercise"] == ex_name]
                    set_strings = []
                    for _, row in ex_df.iterrows():
                        set_strings.append(f"Set {int(row['Set'])}: {row['Weight_lbs']}lbs x {int(row['Reps'])} reps")
                    st.caption(" | ".join(set_strings))

# --- SCREEN 3: HIGH-SPEED NATIVE GOOGLE AI ASSISTANT ---
elif menu == "🤖 Chat with AI Coach":
    st.header("🤖 Native Google AI Hypertrophy Coach")
    
    st.sidebar.markdown("---")
    raw_key = st.sidebar.text_input("🔑 Enter Gemini API Key:", type="password", help="Paste your key from aistudio.google.com")
    api_key = raw_key.strip()
    
    if not api_key:
        st.info("👈 Please paste your free Google Gemini API Key into the sidebar slot to open the live chat channel.")
    else:
        st.caption("Ask anything about your home gym gear, form adjustments, or muscle building tactics.")
        
        if "messages" not in st.session_state:
            st.session_state.messages = [
                {"role": "assistant", "content": "Hey! I am connected natively now. Ask me anything about your 3-day split, working around home gym issues, or mapping out fatigue!"}
            ]
            
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                
        if prompt := st.chat_input("Ex: What can I use my 35lb kettlebell for on leg day?"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)
                
            with st.chat_message("assistant"):
                with st.spinner("Connecting with Google AI Engines..."):
                    try:
                        # MODIFIED MODEL ENTRY: Migrated route name from 1.5-flash to 2.5-flash to stop 404 blockages
                        url = "https://googleapis.com"
                        params = {"key": api_key}
                        headers = {"Content-Type": "application/json"}
                        
                        system_context = "You are an elite fitness coach specializing in bodybuilding and hypertrophy training for home gym lifters. Keep answers concise, clear, and action-focused."
                        payload = {
                            "contents": [
                                {
                                    "parts": [
                                        {"text": f"Context: {system_context}\n\nUser Question: {prompt}"}
                                    ]
                                }
                            ]
                        }
                        
                        response = requests.post(url, params=params, json=payload, headers=headers)
                        
                        if response.status_code != 200:
                            ai_reply = f"Google Server Error ({response.status_code}). Please confirm your API key is correctly pasted and active at aistudio.google.com. Error detail: {response.text}"
                        else:
                            res_data = response.json()
                            ai_reply = res_data["candidates"][0]["content"]["parts"][0]["text"]
                        
                    except Exception as e:
                        ai_reply = f"Connection failed. Please confirm your API key is active. Error diagnostic code: {str(e)}"
                    
                    st.write(ai_reply)
                    st.session_state.messages.append({"role": "assistant", "content": ai_reply})
