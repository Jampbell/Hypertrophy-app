import datetime
import os
import time

import pandas as pd
import requests
import streamlit as st

# Page Layout Configuration
st.set_page_config(page_title="HyperCustom Fit", layout="wide", page_icon="🏋️‍♂️")
st.title("🏋️‍♂️ HyperCustom Fit Tracker")

DB_FILE = "workout_database.csv"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

DEFAULT_EQUIPMENT_PROFILE = {
    "Marcy Smith MD-9010G": True,
    "Dumbbells (5-25 lb pairs)": True,
    "Kettlebells (15 lb, 35 lb)": True,
    "Safety Squat Bar": True,
    "Curl Bar": True,
    "Air Rower": True,
    "Power Tower (pull-up/dip station)": True,
    "Olympic Barbell": False,
    "Bench": True,
}

EXERCISE_LIBRARY = {
    "Barbell Bench Press": {
        "muscle": "Chest",
        "movement": "Horizontal Push",
        "equipment": ["Olympic Barbell", "Bench"],
        "fallback": ["Smith Machine Flat Press", "Dumbbell Flat Press", "Power Tower Push-Ups"],
        "cues": ["Shoulders down and back", "Bar path over mid-chest", "Drive feet into floor"],
        "mistakes": ["Elbows flaring too wide", "Bouncing off chest", "Losing upper-back tightness"],
        "url": "https://www.youtube.com/watch?v=rT7DgCr-3pg",
    },
    "Smith Machine Flat Press": {
        "muscle": "Chest",
        "movement": "Horizontal Push",
        "equipment": ["Marcy Smith MD-9010G", "Bench"],
        "fallback": ["Dumbbell Flat Press", "Power Tower Push-Ups"],
        "cues": ["Set safeties just below chest", "Control eccentric", "Press with stacked wrists"],
        "mistakes": ["Bench too far forward", "Partial range only", "Wrists bent backward"],
        "url": "https://www.youtube.com/watch?v=9R4fQv1U8b0",
    },
    "Dumbbell Flat Press": {
        "muscle": "Chest",
        "movement": "Horizontal Push",
        "equipment": ["Dumbbells (5-25 lb pairs)", "Bench"],
        "fallback": ["Smith Machine Flat Press", "Power Tower Push-Ups"],
        "cues": ["Slight arch is okay", "Lower with control", "Keep forearms vertical"],
        "mistakes": ["Bouncing at bottom", "Elbows too high", "Losing wrist position"],
        "url": "https://www.youtube.com/watch?v=VmB1G1K7v94",
    },
    "Power Tower Push-Ups": {
        "muscle": "Chest",
        "movement": "Horizontal Push",
        "equipment": ["Power Tower (pull-up/dip station)"],
        "fallback": ["Dumbbell Flat Press", "Smith Machine Flat Press"],
        "cues": ["Body in straight line", "Hands under shoulders", "Full lockout"],
        "mistakes": ["Sagging hips", "Short range", "Neck jutting forward"],
        "url": "https://www.youtube.com/watch?v=IODxDxX7oi4",
    },
    "Barbell Row": {
        "muscle": "Back",
        "movement": "Horizontal Pull",
        "equipment": ["Olympic Barbell"],
        "fallback": ["Chest-Supported DB Row", "Smith Machine Bent Row", "Air Rower Intervals"],
        "cues": ["Hinge first", "Pull elbows to hips", "Pause at torso"],
        "mistakes": ["Jerking from lower back", "Neck craning", "Too upright torso"],
        "url": "https://www.youtube.com/watch?v=vT2GjY_Umpw",
    },
    "Smith Machine Bent Row": {
        "muscle": "Back",
        "movement": "Horizontal Pull",
        "equipment": ["Marcy Smith MD-9010G"],
        "fallback": ["Chest-Supported DB Row", "Air Rower Intervals"],
        "cues": ["Set pins safely", "Hinge and brace", "Row to lower ribs"],
        "mistakes": ["Standing too tall", "Rounding low back", "Shrugging shoulders"],
        "url": "https://www.youtube.com/watch?v=roCP6wCXPqo",
    },
    "Chest-Supported DB Row": {
        "muscle": "Back",
        "movement": "Horizontal Pull",
        "equipment": ["Dumbbells (5-25 lb pairs)", "Bench"],
        "fallback": ["Smith Machine Bent Row", "Air Rower Intervals"],
        "cues": ["Chest on bench", "Pull elbow back", "Squeeze shoulder blade"],
        "mistakes": ["Twisting torso", "Yanking weight", "Neck strain"],
        "url": "https://www.youtube.com/watch?v=5PoEksoJNaw",
    },
    "Overhead Barbell Press": {
        "muscle": "Shoulders",
        "movement": "Vertical Push",
        "equipment": ["Olympic Barbell"],
        "fallback": ["Smith Machine Overhead Press", "Dumbbell Seated Press"],
        "cues": ["Brace abs and glutes", "Head through at top", "Bar close to face"],
        "mistakes": ["Overarching back", "Pressing out front", "Loose bar path"],
        "url": "https://www.youtube.com/watch?v=2yjwXTZQDDI",
    },
    "Smith Machine Overhead Press": {
        "muscle": "Shoulders",
        "movement": "Vertical Push",
        "equipment": ["Marcy Smith MD-9010G", "Bench"],
        "fallback": ["Dumbbell Seated Press"],
        "cues": ["Back supported", "Wrists stacked", "Controlled lowering"],
        "mistakes": ["Seat too low", "Flaring elbows", "Rushing reps"],
        "url": "https://www.youtube.com/watch?v=R5JhoUX4hRQ",
    },
    "Dumbbell Seated Press": {
        "muscle": "Shoulders",
        "movement": "Vertical Push",
        "equipment": ["Dumbbells (5-25 lb pairs)", "Bench"],
        "fallback": ["Smith Machine Overhead Press"],
        "cues": ["Feet planted", "Press up and in", "Keep ribs down"],
        "mistakes": ["Overarching back", "Uneven lockout", "Banging DBs together"],
        "url": "https://www.youtube.com/watch?v=qEwKCR5JCog",
    },
    "Lat Pulldown / Pull-up": {
        "muscle": "Back",
        "movement": "Vertical Pull",
        "equipment": ["Marcy Smith MD-9010G", "Power Tower (pull-up/dip station)"],
        "fallback": ["Band-Assisted Pull-Up", "Inverted Row on Smith Bar"],
        "cues": ["Lead with elbows", "Chest up", "Full stretch at top"],
        "mistakes": ["Pulling behind neck", "Using momentum", "Shrugging shoulders"],
        "url": "https://www.youtube.com/watch?v=CAwf7n6Luuc",
    },
    "Band-Assisted Pull-Up": {
        "muscle": "Back",
        "movement": "Vertical Pull",
        "equipment": ["Power Tower (pull-up/dip station)"],
        "fallback": ["Inverted Row on Smith Bar"],
        "cues": ["Pull elbows down", "Core tight", "Full range of motion"],
        "mistakes": ["Kipping", "Half reps", "Forward head posture"],
        "url": "https://www.youtube.com/watch?v=eGo4IYlbE5g",
    },
    "Inverted Row on Smith Bar": {
        "muscle": "Back",
        "movement": "Horizontal Pull",
        "equipment": ["Marcy Smith MD-9010G"],
        "fallback": ["Chest-Supported DB Row"],
        "cues": ["Body rigid", "Pull chest to bar", "Control lowering"],
        "mistakes": ["Hips dropping", "Short ROM", "Shrugging"],
        "url": "https://www.youtube.com/watch?v=2B6aN8P6WwM",
    },
    "Safety Squat Bar Squat": {
        "muscle": "Quads",
        "movement": "Squat",
        "equipment": ["Safety Squat Bar"],
        "fallback": ["Smith Machine Squat", "Goblet Squat (35 lb KB)"],
        "cues": ["Brace before descent", "Knees track toes", "Drive mid-foot"],
        "mistakes": ["Chest collapsing", "Heels lifting", "Knees caving"],
        "url": "https://www.youtube.com/watch?v=5MTEf2hP9PY",
    },
    "Smith Machine Squat": {
        "muscle": "Quads",
        "movement": "Squat",
        "equipment": ["Marcy Smith MD-9010G"],
        "fallback": ["Goblet Squat (35 lb KB)"],
        "cues": ["Feet slightly forward", "Sit between hips", "Drive through whole foot"],
        "mistakes": ["Too narrow stance", "Knees collapse", "Cutting depth"],
        "url": "https://www.youtube.com/watch?v=fEuYM-miK5U",
    },
    "Goblet Squat (35 lb KB)": {
        "muscle": "Quads",
        "movement": "Squat",
        "equipment": ["Kettlebells (15 lb, 35 lb)"],
        "fallback": ["Smith Machine Squat", "Split Squat (DB)"],
        "cues": ["Hold bell high", "Elbows inside knees", "Stay tall"],
        "mistakes": ["Dropping chest", "Weight on toes", "Cutting depth"],
        "url": "https://www.youtube.com/watch?v=6xwGFn-J_QM",
    },
    "Dumbbell Romanian Deadlift": {
        "muscle": "Hamstrings",
        "movement": "Hinge",
        "equipment": ["Dumbbells (5-25 lb pairs)"],
        "fallback": ["Curl Bar RDL", "Kettlebell RDL"],
        "cues": ["Soft knees", "Hips back", "Keep weights close"],
        "mistakes": ["Squatting instead of hinging", "Rounding back", "Losing lats"],
        "url": "https://www.youtube.com/watch?v=0zG7o6hR0dQ",
    },
    "Curl Bar RDL": {
        "muscle": "Hamstrings",
        "movement": "Hinge",
        "equipment": ["Curl Bar"],
        "fallback": ["Dumbbell Romanian Deadlift", "Kettlebell RDL"],
        "cues": ["Lats tight", "Hips back", "Shins mostly vertical"],
        "mistakes": ["Bar drifting away", "Over-bending knees", "Rounding back"],
        "url": "https://www.youtube.com/watch?v=jEy_czb3RKA",
    },
    "Kettlebell RDL": {
        "muscle": "Hamstrings",
        "movement": "Hinge",
        "equipment": ["Kettlebells (15 lb, 35 lb)"],
        "fallback": ["Dumbbell Romanian Deadlift", "Curl Bar RDL"],
        "cues": ["Hips back", "Core braced", "Neutral spine"],
        "mistakes": ["Squatting the rep", "Neck extension", "Loose lockout"],
        "url": "https://www.youtube.com/watch?v=0zG7o6hR0dQ",
    },
    "Air Rower Intervals": {
        "muscle": "Back",
        "movement": "Conditioning",
        "equipment": ["Air Rower"],
        "fallback": ["Power Tower Knee Raise Conditioning"],
        "cues": ["Leg drive first", "Then hip swing", "Then arm pull"],
        "mistakes": ["Early arm bend", "Rounding lumbar", "Rushing recovery"],
        "url": "https://www.youtube.com/watch?v=zQ82RYIFLN8",
    },
    "Power Tower Knee Raise Conditioning": {
        "muscle": "Core",
        "movement": "Conditioning",
        "equipment": ["Power Tower (pull-up/dip station)"],
        "fallback": ["Air Rower Intervals"],
        "cues": ["Posterior pelvic tilt", "Slow control", "No swinging"],
        "mistakes": ["Leg swing momentum", "Shrugged shoulders", "Short ROM"],
        "url": "https://www.youtube.com/watch?v=JB2oyawG9KI",
    },
}

ROUTINES = {
    "3-Day Full Blend": {
        "Day 1: Upper Focus": [
            {"name": "Barbell Bench Press", "range": "8-10", "sets": 3},
            {"name": "Barbell Row", "range": "8-12", "sets": 3},
            {"name": "Overhead Barbell Press", "range": "8-10", "sets": 3},
            {"name": "Lat Pulldown / Pull-up", "range": "8-12", "sets": 3},
            {"name": "Air Rower Intervals", "range": "10-15", "sets": 2},
        ],
        "Day 2: Lower Focus": [
            {"name": "Safety Squat Bar Squat", "range": "8-10", "sets": 3},
            {"name": "Dumbbell Romanian Deadlift", "range": "10-12", "sets": 3},
            {"name": "Goblet Squat (35 lb KB)", "range": "12-15", "sets": 3},
            {"name": "Power Tower Knee Raise Conditioning", "range": "12-20", "sets": 2},
        ],
        "Day 3: Full Body Blend": [
            {"name": "Smith Machine Flat Press", "range": "8-12", "sets": 3},
            {"name": "Chest-Supported DB Row", "range": "10-12", "sets": 3},
            {"name": "Kettlebell RDL", "range": "10-15", "sets": 3},
            {"name": "Lat Pulldown / Pull-up", "range": "8-12", "sets": 2},
        ],
    },
    "4-Day Upper/Lower Split": {
        "Day 1: Upper A": [
            {"name": "Smith Machine Flat Press", "range": "8-10", "sets": 3},
            {"name": "Barbell Row", "range": "8-12", "sets": 3},
            {"name": "Lat Pulldown / Pull-up", "range": "10-12", "sets": 3},
            {"name": "Dumbbell Seated Press", "range": "10-12", "sets": 3},
        ],
        "Day 2: Lower A": [
            {"name": "Safety Squat Bar Squat", "range": "8-10", "sets": 3},
            {"name": "Dumbbell Romanian Deadlift", "range": "10-12", "sets": 3},
            {"name": "Goblet Squat (35 lb KB)", "range": "12-15", "sets": 2},
        ],
        "Day 3: Upper B": [
            {"name": "Overhead Barbell Press", "range": "8-10", "sets": 3},
            {"name": "Chest-Supported DB Row", "range": "10-12", "sets": 3},
            {"name": "Dumbbell Flat Press", "range": "10-12", "sets": 3},
            {"name": "Lat Pulldown / Pull-up", "range": "8-12", "sets": 2},
        ],
        "Day 4: Lower B": [
            {"name": "Smith Machine Squat", "range": "8-12", "sets": 3},
            {"name": "Curl Bar RDL", "range": "10-12", "sets": 3},
            {"name": "Power Tower Knee Raise Conditioning", "range": "12-20", "sets": 3},
            {"name": "Air Rower Intervals", "range": "10-15", "sets": 2},
        ],
    },
}


def ensure_session_state():
    if "equipment_profile" not in st.session_state:
        st.session_state.equipment_profile = DEFAULT_EQUIPMENT_PROFILE.copy()
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Ask about your home setup, progression, form, or substitutions."}
        ]


def save_set_to_csv(date_str, routine_name, exercise_name, set_num, weight, reps, rir, completed):
    new_row = pd.DataFrame(
        [
            {
                "Date": date_str,
                "Routine": routine_name,
                "Exercise": exercise_name,
                "Set": set_num,
                "Weight_lbs": float(weight),
                "Reps": int(reps),
                "RIR": int(rir),
                "Completed": int(completed),
                "Volume": float(weight) * int(reps),
            }
        ]
    )
    if not os.path.exists(DB_FILE):
        new_row.to_csv(DB_FILE, index=False)
    else:
        new_row.to_csv(DB_FILE, mode="a", header=False, index=False)


def load_workout_history():
    if not os.path.exists(DB_FILE):
        return pd.DataFrame()

    try:
        df = pd.read_csv(DB_FILE)
    except (pd.errors.EmptyDataError, pd.errors.ParserError):
        return pd.DataFrame()

    expected_defaults = {
        "Weight_lbs": 0.0,
        "Reps": 0,
        "RIR": 0,
        "Completed": 1,
        "Volume": 0.0,
    }

    for col, default in expected_defaults.items():
        if col not in df.columns:
            df[col] = default

    df["Weight_lbs"] = pd.to_numeric(df["Weight_lbs"], errors="coerce").fillna(0.0)
    df["Reps"] = pd.to_numeric(df["Reps"], errors="coerce").fillna(0).astype(int)
    df["RIR"] = pd.to_numeric(df["RIR"], errors="coerce").fillna(0).astype(int)
    df["Completed"] = pd.to_numeric(df["Completed"], errors="coerce").fillna(1).astype(int)
    df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce")
    missing_volume = df["Volume"].isna() | (df["Volume"] == 0)
    df.loc[missing_volume, "Volume"] = df.loc[missing_volume, "Weight_lbs"] * df.loc[missing_volume, "Reps"]

    return df


def youtube_embed_url(url: str) -> str:
    if "youtube.com/watch?v=" in url:
        video_id = url.split("watch?v=")[-1].split("&")[0]
        return f"https://www.youtube.com/embed/{video_id}"
    if "youtu.be/" in url:
        video_id = url.split("youtu.be/")[-1].split("?")[0]
        return f"https://www.youtube.com/embed/{video_id}"
    return url


def parse_rep_range(rep_range: str):
    if "-" in rep_range:
        low, high = rep_range.split("-")
        return int(low.strip()), int(high.strip())
    value = int(rep_range.strip())
    return value, value


def equipment_ready(exercise_name: str):
    needs = EXERCISE_LIBRARY.get(exercise_name, {}).get("equipment", [])
    profile = st.session_state.equipment_profile
    return all(profile.get(item, False) for item in needs)


def best_substitution(exercise_name: str):
    profile = st.session_state.equipment_profile
    for candidate in EXERCISE_LIBRARY.get(exercise_name, {}).get("fallback", []):
        if candidate in EXERCISE_LIBRARY:
            needs = EXERCISE_LIBRARY[candidate].get("equipment", [])
            if all(profile.get(item, False) for item in needs):
                return candidate
    return None


def suggest_progression(exercise_name: str, rep_range: str, history_df: pd.DataFrame):
    if history_df.empty:
        return "No prior data yet. Start conservative and focus clean form."

    ex_df = history_df[(history_df["Exercise"] == exercise_name) & (history_df["Completed"] == 1)]
    if ex_df.empty:
        return "No prior completed sets for this movement yet."

    latest_date = ex_df["Date"].iloc[-1]
    latest = ex_df[ex_df["Date"] == latest_date]
    avg_weight = latest["Weight_lbs"].mean()
    avg_reps = latest["Reps"].mean()
    avg_rir = latest["RIR"].mean()
    _, rep_high = parse_rep_range(rep_range)

    if avg_reps >= rep_high and avg_rir >= 1:
        return f"Progression target: add +5 lb next session (around {avg_weight + 5:.1f} lb)."
    if avg_reps >= rep_high and avg_rir < 1:
        return f"Hold at ~{avg_weight:.1f} lb; keep top-range reps with better control."
    return f"Keep ~{avg_weight:.1f} lb and aim +1 total rep across sets."


def weekly_muscle_volume(history_df: pd.DataFrame):
    if history_df.empty:
        return pd.DataFrame(columns=["Muscle", "Volume"])

    map_muscle = {name: meta["muscle"] for name, meta in EXERCISE_LIBRARY.items()}
    copy_df = history_df.copy()
    copy_df["Muscle"] = copy_df["Exercise"].map(map_muscle).fillna("Other")
    return (
        copy_df.groupby("Muscle", as_index=False)["Volume"]
        .sum()
        .sort_values("Volume", ascending=False)
    )


def fatigue_signal(history_df: pd.DataFrame):
    if history_df.empty or history_df.shape[0] < 12:
        return "No fatigue signal yet; log a few sessions first."

    recent = history_df.tail(30)
    low_rir_ratio = float((recent["RIR"] <= 1).mean())
    completion_ratio = float((recent["Completed"] == 1).mean())

    if low_rir_ratio >= 0.60:
        return "High fatigue trend: consider a 1-week deload at ~70% normal volume."
    if completion_ratio < 0.85:
        return "Completion trend dipped. Reduce set count 10-20% for one week and recover."
    return "Fatigue looks manageable. Continue progressing."


def movement_volume_breakdown(history_df: pd.DataFrame):
    if history_df.empty:
        return pd.DataFrame(columns=["Movement", "Volume"])
    map_move = {name: meta["movement"] for name, meta in EXERCISE_LIBRARY.items()}
    copy_df = history_df.copy()
    copy_df["Movement"] = copy_df["Exercise"].map(map_move).fillna("Other")
    return (
        copy_df.groupby("Movement", as_index=False)["Volume"]
        .sum()
        .sort_values("Volume", ascending=False)
    )


ensure_session_state()
history_df = load_workout_history()

# Sidebar
st.sidebar.header("⚙️ Preferences")
split_type = st.sidebar.selectbox("Program Layout", list(ROUTINES.keys()))
goal_mode = st.sidebar.selectbox("Goal Mode", ["Hypertrophy", "Strength", "Fat Loss"])
menu = st.sidebar.radio(
    "Navigation",
    ["🏠 Dashboard", "📝 Today’s Workout", "📈 History & Analytics", "📚 Exercise Library", "🤖 AI Coach", "⚙️ Settings"],
)
active_routine = ROUTINES[split_type]

if menu == "🏠 Dashboard":
    st.subheader("Training Dashboard")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Logged Sets", int(history_df.shape[0]))
    c2.metric("Total Volume", f"{history_df['Volume'].sum():.0f} lb" if not history_df.empty else "0 lb")
    c3.metric("Unique Exercises", int(history_df["Exercise"].nunique()) if not history_df.empty else 0)
    c4.metric("Goal Mode", goal_mode)

    st.info(fatigue_signal(history_df))

    vol_df = weekly_muscle_volume(history_df)
    if not vol_df.empty:
        st.markdown("#### Volume by Muscle")
        st.bar_chart(vol_df.set_index("Muscle")["Volume"])

    move_df = movement_volume_breakdown(history_df)
    if not move_df.empty:
        st.markdown("#### Volume by Movement Pattern")
        st.bar_chart(move_df.set_index("Movement")["Volume"])

elif menu == "📝 Today’s Workout":
    st.subheader(f"Today’s Workout · {split_type}")
    selected_day = st.selectbox("Routine day", list(active_routine.keys()))
    day_work = active_routine[selected_day]

    st.sidebar.markdown("---")
    duration = st.sidebar.selectbox("Rest timer (seconds)", [60, 90, 120, 180], index=1)
    if st.sidebar.button("Start rest timer", use_container_width=True):
        progress_bar = st.sidebar.progress(0)
        for i in range(100):
            time.sleep(duration / 100)
            progress_bar.progress(i + 1)
        st.sidebar.success("Rest complete. Next set.")

    total_exercises = len(day_work)
    completed_exercises = 0
    workout_inputs = {}

    st.markdown("### Session Flow")
    for idx, ex in enumerate(day_work, start=1):
        ex_name = ex["name"]
        rep_range = ex["range"]
        sets_count = ex["sets"]

        # Auto-swap if needed
        active_name = ex_name
        if not equipment_ready(ex_name):
            sub = best_substitution(ex_name)
            if sub:
                active_name = sub
                st.warning(f"{ex_name}: primary setup unavailable. Auto-substituted with **{sub}**.")
            else:
                st.error(f"{ex_name}: no valid substitution available with current equipment.")
                continue

        meta = EXERCISE_LIBRARY[active_name]
        st.markdown(f"#### {idx}/{total_exercises} · {active_name} · {rep_range} reps")
        if active_name == ex_name:
            st.success("Equipment ready.")
        suggestion = suggest_progression(active_name, rep_range, history_df)
        st.caption(f"Progression: {suggestion}")
        st.caption(f"Substitutions: {', '.join(meta['fallback'])}")

        with st.expander("Form demo + cues + mistakes"):
            st.video(youtube_embed_url(meta["url"]))
            st.write("**Key cues**")
            for cue in meta["cues"]:
                st.write(f"- {cue}")
            st.write("**Common mistakes**")
            for err in meta["mistakes"]:
                st.write(f"- {err}")

        cols = st.columns(sets_count)
        ex_inputs = []
        set_completion_flags = []

        for set_idx in range(sets_count):
            with cols[set_idx]:
                st.caption(f"Set {set_idx + 1}")
                wt = st.number_input("Wt (lb)", min_value=0.0, step=2.5, key=f"{selected_day}_{active_name}_w_{set_idx}")
                rp = st.number_input("Reps", min_value=0, step=1, key=f"{selected_day}_{active_name}_r_{set_idx}")
                rir = st.slider("RIR", 0, 4, 2, key=f"{selected_day}_{active_name}_rir_{set_idx}")
                done = st.checkbox("Done", key=f"{selected_day}_{active_name}_done_{set_idx}")
                ex_inputs.append((set_idx + 1, wt, rp, rir, done))
                set_completion_flags.append(done)

        if all(set_completion_flags):
            completed_exercises += 1

        workout_inputs[active_name] = ex_inputs
        st.divider()

    completion_pct = int((completed_exercises / total_exercises) * 100) if total_exercises else 0
    st.progress(completion_pct / 100)
    st.caption(f"Workout completion: {completion_pct}%")

    if st.button("Save workout", type="primary"):
        today_str = datetime.date.today().strftime("%b %d, %Y")
        for ex_name, sets_data in workout_inputs.items():
            for set_num, weight, reps, rir, done in sets_data:
                if done:
                    save_set_to_csv(today_str, selected_day, ex_name, set_num, weight, reps, rir, done)
        st.success("Workout saved.")

elif menu == "📈 History & Analytics":
    st.subheader("History & Analytics")
    if history_df.empty:
        st.warning("No sessions logged yet.")
    else:
        st.dataframe(history_df.sort_index(ascending=False), use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Volume by Exercise")
            ex_vol = (
                history_df.groupby("Exercise", as_index=False)["Volume"]
                .sum()
                .sort_values("Volume", ascending=False)
            )
            st.bar_chart(ex_vol.set_index("Exercise")["Volume"])
        with col2:
            st.markdown("#### Average RIR by Exercise")
            rir_avg = (
                history_df.groupby("Exercise", as_index=False)["RIR"]
                .mean()
                .sort_values("RIR", ascending=True)
            )
            st.bar_chart(rir_avg.set_index("Exercise")["RIR"])

elif menu == "📚 Exercise Library":
    st.subheader("Exercise Library & Substitutions")
    for ex_name, meta in EXERCISE_LIBRARY.items():
        with st.expander(ex_name):
            st.write(f"**Muscle:** {meta['muscle']} | **Pattern:** {meta['movement']}")
            st.write(f"**Required equipment:** {', '.join(meta['equipment'])}")
            st.write(f"**Best substitutions:** {', '.join(meta['fallback'])}")
            st.video(youtube_embed_url(meta["url"]))

elif menu == "⚙️ Settings":
    st.subheader("Equipment Settings")
    st.caption("Toggle your available equipment so substitutions are personalized.")
    for item in list(st.session_state.equipment_profile.keys()):
        st.session_state.equipment_profile[item] = st.checkbox(item, value=st.session_state.equipment_profile[item])

    if st.session_state.equipment_profile.get("Olympic Barbell"):
        st.success("Olympic bar enabled: barbell movements remain primary.")
    else:
        st.info("Olympic bar disabled: app will prioritize Smith/DB/KB/SSB alternatives.")

elif menu == "🤖 AI Coach":
    st.subheader("AI Coach")
    raw_key = st.sidebar.text_input("Gemini API Key", type="password")
    api_key = raw_key.strip()

    if not api_key:
        st.info("Add your Gemini API key in the sidebar.")
    else:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        if prompt := st.chat_input("Ask your coach..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        equipment_on = [k for k, v in st.session_state.equipment_profile.items() if v]
                        system_context = (
                            "You are an elite hypertrophy coach for a home gym athlete. "
                            f"Available equipment: {', '.join(equipment_on)}. "
                            f"Current goal mode: {goal_mode}. "
                            "Keep responses concise, specific, and actionable."
                        )

                        payload = {
                            "contents": [
                                {
                                    "parts": [
                                        {"text": f"{system_context}\nUser question: {prompt}"}
                                    ]
                                }
                            ]
                        }

                        response = requests.post(
                            GEMINI_API_URL,
                            json=payload,
                            headers={"Content-Type": "application/json"},
                            params={"key": api_key},
                            timeout=20,
                        )

                        if response.status_code != 200:
                            ai_reply = f"Connection rejected ({response.status_code})."
                        else:
                            data = response.json()
                            ai_reply = data["candidates"][0]["content"]["parts"][0]["text"]

                        st.write(ai_reply)
                        st.session_state.messages.append({"role": "assistant", "content": ai_reply})

                    except requests.RequestException as exc:
                        err = f"Network/API error: {exc}"
                        st.write(err)
                        st.session_state.messages.append({"role": "assistant", "content": err})
