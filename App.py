import streamlit as st
import datetime
import time

# Page Layout Configuration
st.set_page_config(page_title="HyperCustom Fit", layout="wide", page_icon="🏋️‍♂️")
st.title("🏋️‍♂️ HyperCustom Fit Tracker")

# App Database Buffering
if "history" not in st.session_state:
    st.session_state.history = []

# Navigation Sidebar
menu = st.sidebar.radio("Menu", ["📝 Log Today's Lift", "📈 View Training Logs"])

# Programming Schedule Matched to your Home Setup
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
    
    # PREMIUM FEATURE: REST TIMER
    st.sidebar.markdown("---")
    st.sidebar.subheader("⏱️ Rest Break Timer")
    duration = st.sidebar.selectbox("Select Break Length:", [60, 90, 45], format_func=lambda x: f"{x} Seconds")
    
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
    
    logged_data = []
    for ex in routine[selected_day]:
        st.markdown(f"#### 🔹 {ex['name']} *({ex['range']})*")
        cols = st.columns(ex['sets'])
        
        ex_sets = []
        for i in range(ex['sets']):
            with cols[i]:
                st.caption(f"Set {i+1}")
                weight = st.number_input(f"Wt (lbs)", min_value=0.0, step=2.5, key=f"{ex['name']}_w_{i}")
                reps = st.number_input(f"Reps", min_value=0, step=1, key=f"{ex['name']}_r_{i}")
                ex_sets.append({"set": i+1, "weight": weight, "reps": reps})
        logged_data.append({"exercise": ex['name'], "sets": ex_sets})
        st.write("---")
        
    if st.button("Save Workout to History", type="primary"):
        log_entry = {
            "date": datetime.date.today().strftime("%b %d, %Y"),
            "routine": selected_day,
            "data": logged_data
        }
        st.session_state.history.append(log_entry)
        st.success("💪 Workout logged! Go to 'View Training Logs' to check progress.")

# --- SCREEN 2: PROGRESS LOGS ---
elif menu == "📈 View Training Logs":
    st.header("Your Completed Workouts")
    if not st.session_state.history:
        st.warning("No logged sessions found. Try completing a workout row under the log page first!")
    else:
        for entry in reversed(st.session_state.history):
            with st.expander(f"📅 {entry['date']} — {entry['routine']}"):
                for ex in entry['data']:
                    st.write(f"**{ex['exercise']}**")
                    set_str = " | ".join([f"Set {s['set']}: {s['weight']}lbs x {s['reps']} reps" for s in ex['sets']])
                    st.caption(set_str)