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

EQUIPMENT_PROFILE = {
    "Marcy Smith MD-9010G": True,
    "Dumbbells (5-25 lb pairs)": True,
    "Kettlebells (15 lb, 35 lb)": True,
    "Safety Squat Bar": True,
    "Curl Bar": True,
    "Air Rower": True,
    "Power Tower (pull-up/dip station)": True,
    "Olympic Barbell": False,
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
        "equipment": ["Marcy Smith MD-9010G"],
        "fallback": ["Dumbbell Flat Press", "Power Tower Push-Ups"],
        "cues": ["Set safeties one notch below chest", "Control eccentric", "Press with stacked wrists"],
        "mistakes": ["Bench too far forward", "Partial range only", "Wrists bent backward"],
        "url": "https://www.youtube.com/watch?v=9R4fQv1U8b0",
    },
    "Barbell Row": {
        "muscle": "Back",
        "movement": "Horizontal Pull",
        "equipment": ["Olympic Barbell"],
        "fallback": ["Chest-Supported DB Row", "Smith Machine Bent Row", "Air Rower Intervals"],
        "cues": ["Hinge first", "Pull elbows toward hips", "Pause at torso"],
        "mistakes": ["Jerking from lower back", "Neck craning", "Too upright torso"],
        "url": "https://www.youtube.com/watch?v=vT2GjY_Umpw",
    },
    "Overhead Barbell Press": {
        "muscle": "Shoulders",
        "movement": "Vertical Push",
        "equipment": ["Olympic Barbell"],
        "fallback": ["Smith Machine Overhead Press", "Dumbbell Seated Press"],
        "cues": ["Brace abs and glutes", "Head moves through at top", "Bar close to face"],
        "mistakes": ["Overarching lower back", "Pressing out in front", "Loose bar path"],
        "url": "https://www.youtube.com/watch?v=2yjwXTZQDDI",
    },
    "Lat Pulldown / Pull-up": {
        "muscle": "Back",
        "movement": "Vertical Pull",
        "equipment": ["Marcy Smith MD-9010G", "Power Tower (pull-up/dip station)"],
        "fallback": ["Band-Assisted Pull-Up", "Inverted Row on Smith Bar"],
        "cues": ["Lead with elbows", "Keep chest lifted", "Full stretch at top"],
        "mistakes": ["Pulling behind neck", "Using momentum", "Shrugging shoulders"],
        "url": "https://www.youtube.com/watch?v=CAwf7n6Luuc",
    },
    "Safety Squat Bar Squat": {
        "muscle": "Quads",
        "movement": "Squat",
        "equipment": ["Safety Squat Bar"],
        "fallback": ["Smith Machine Squat", "Goblet Squat (35 lb KB)"],
        "cues": ["Brace before descent", "Knees track toes", "Drive mid-foot"],
        "mistakes": ["Chest collapsing", "Heels lifting", "Knees caving"],
        "url": "https://www.youtube.com/shorts/1oed-UmAxFs",
    },
    "Dumbbell Romanian Deadlift": {
        "muscle": "Hamstrings",
        "movement": "Hinge",
        "equipment": ["Dumbbells (5-25 lb pairs)"],
        "fallback": ["Curl Bar RDL", "Kettlebell RDL"],
        "cues": ["Soft knees", "Hips back", "Keep dumbbells close"],
        "mistakes": ["Squatting instead of hinging", "Rounding back", "Losing lats"],
        "url": "https://www.youtube.com/shorts/7j-2m8M1M90",
    },
    "Goblet Squat (35 lb KB)": {
        "muscle": "Quads",
        "movement": "Squat",
        "equipment": ["Kettlebells (15 lb, 35 lb)"],
        "fallback": ["Smith Machine Squat", "Split Squat (DB)"],
        "cues": ["Hold bell high", "Elbows inside knees", "Stay tall"],
        "mistakes": ["Dropping chest", "Weight on toes", "Cutting depth"],
        "url": "https://www.youtube.com/shorts/sz0S9V5nXJ0",
    },
}

ROUTINES = {
    "3-Day Full Blend": {
        "Day 1: Upper Focus": [
            {"name": "Barbell Bench Press", "range": "8-10", "sets": 3},
            {"name": "Barbell Row", "range": "8-12", "sets": 3},
            {"name": "Overhead Barbell Press", "range": "8-10", "sets": 3},
            {"name": "Lat Pulldown / Pull-up", "range": "10-12", "sets": 3},
        ],
        "Day 2: Lower Focus": [
            {"name": "Safety Squat Bar Squat", "range": "8-10", "sets": 3},
            {"name": "Dumbbell Romanian Deadlift", "range": "10-12", "sets": 3},
            {"name": "Goblet Squat (35 lb KB)", "range": "12-15", "sets": 3},
        ],
        "Day 3: Full Body Blend": [
            {"name": "Smith Machine Flat Press", "range": "8-12", "sets": 3},
            {"name": "Lat Pulldown / Pull-up", "range": "8-12", "sets": 3},
            {"name": "Dumbbell Romanian Deadlift", "range": "10-12", "sets": 3},
        ],
    },
    "4-Day Upper/Lower Split": {
        "Day 1: Upper A": [
            {"name": "Smith Machine Flat Press", "range": "8-10", "sets": 3},
            {"name": "Barbell Row", "range": "8-12", "sets": 3},
            {"name": "Lat Pulldown / Pull-up", "range": "10-12", "sets": 3},
        ],
        "Day 2: Lower A": [
            {"name": "Safety Squat Bar Squat", "range": "8-10", "sets": 3},
            {"name": "Dumbbell Romanian Deadlift", "range": "10-12", "sets": 3},
        ],
        "Day 3: Upper B": [
            {"name": "Overhead Barbell Press", "range": "8-10", "sets": 3},
            {"name": "Lat Pulldown / Pull-up", "range": "8-12", "sets": 3},
            {"name": "Smith Machine Flat Press", "range": "8-12", "sets": 3},
        ],
        "Day 4: Lower B": [
            {"name": "Goblet Squat (35 lb KB)", "range": "12-15", "sets": 3},
            {"name": "Dumbbell Romanian Deadlift", "range": "10-12", "sets": 3},
        ],
    },
}


def save_set_to_csv(date_str, routine_name, exercise_name, set_num, weight, reps, rir):
    new_row = pd.DataFrame(
        [
            {
                "Date": date_str,
                "Routine": routine_name,
                "Exercise": exercise_name,
                "Set": set_num,
                "Weight_lbs": weight,
                "Reps": reps,
                "RIR": rir,
                "Volume": weight * reps,
            }
        ]
    )
    if not os.path.exists(DB_FILE):
        new_row.to_csv(DB_FILE, index=False)
    else:
        new_row.to_csv(DB_FILE, mode="a", header=False, index=False)


def load_workout_history():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            for col in ["Weight_lbs", "Reps", "Volume", "RIR"]:
                if col not in df.columns:
                    df[col] = 0
            return df
        except (pd.errors.EmptyDataError, pd.errors.ParserError):
            return pd.DataFrame()
    return pd.DataFrame()


def youtube_embed_url(url: str) -> str:
    if "youtube.com/watch?v=" in url:
        video_id = url.split("watch?v=")[-1].split("&")[0]
        return f"https://www.youtube.com/embed/{video_id}"
    if "youtu.be/" in url:
        video_id = url.split("youtu.be/")[-1].split("?")[0]
        return f"https://www.youtube.com/embed/{video_id}"
    return url


def parse_rep_range(rep_range):
    low, high = rep_range.split("-")
    return int(low.strip()), int(high.strip())


def suggest_progression(exercise_name, rep_range, history_df):
    ex_df = history_df[history_df["Exercise"] == exercise_name] if not history_df.empty else pd.DataFrame()
    if ex_df.empty:
        return "No prior data yet. Start conservative and aim for clean reps.", 0.0

    latest_date = ex_df["Date"].iloc[-1]
    latest = ex_df[ex_df["Date"] == latest_date]
    avg_weight = latest["Weight_lbs"].mean()
    avg_reps = latest["Reps"].mean()
    avg_rir = latest["RIR"].mean()
    _, rep_high = parse_rep_range(rep_range)

    if avg_reps >= rep_high and avg_rir >= 1:
        return f"You hit the top of range. Add +5 lb next session (target ~{avg_weight + 5:.1f} lb).", 5.0
    if avg_reps >= rep_high:
        return f"Hold weight ({avg_weight:.1f} lb) and improve control at this range.", 0.0
    return f"Keep weight near {avg_weight:.1f} lb and add 1 rep total across sets.", 0.0


def help_tip(label: str, tip: str):
    with st.popover(f"❓ {label}"):
        st.caption(tip)


def demo_link(url: str):
    embed = youtube_embed_url(url)
    if "youtube.com/embed/" in embed and "?" not in embed:
        return f"{embed}?start=5&end=65"
    return embed


def equipment_ready(exercise_name):
    data = EXERCISE_LIBRARY.get(exercise_name, {})
    needs = data.get("equipment", [])
    return all(EQUIPMENT_PROFILE.get(item, False) or item == "Bench" for item in needs)


def weekly_muscle_volume(history_df):
    if history_df.empty:
        return pd.DataFrame(columns=["Muscle", "Volume"])
    map_muscle = {name: meta["muscle"] for name, meta in EXERCISE_LIBRARY.items()}
    history_df = history_df.copy()
    history_df["Muscle"] = history_df["Exercise"].map(map_muscle).fillna("Other")
    return history_df.groupby("Muscle", as_index=False)["Volume"].sum().sort_values("Volume", ascending=False)


def fatigue_signal(history_df):
    if history_df.empty:
        return "No fatigue signal yet; log at least 2 sessions."
    recent = history_df.tail(30)
    low_rir_ratio = (recent["RIR"] <= 1).mean()
    if low_rir_ratio >= 0.6:
        return "High fatigue trend detected. Plan a deload: -30% volume for 1 week."
    return "Fatigue looks manageable. Continue progressing."


st.sidebar.header("⚙️ Preferences")
split_type = st.sidebar.selectbox("Program Layout", list(ROUTINES.keys()))
menu = st.sidebar.radio(
    "Navigation",
    ["🏠 Dashboard", "📝 Today’s Workout", "📈 History & Analytics", "📚 Exercise Library", "🤖 AI Coach", "⚙️ Settings"],
)

active_routine = ROUTINES[split_type]
history_df = load_workout_history()

if menu == "🏠 Dashboard":
    st.subheader("Training Dashboard")
    c1, c2, c3 = st.columns(3)
    c1.metric("Logged Sets", int(history_df.shape[0]))
    c2.metric("Total Volume", f"{history_df['Volume'].sum():.0f} lb" if not history_df.empty else "0 lb")
    c3.metric("Unique Exercises", int(history_df["Exercise"].nunique()) if not history_df.empty else 0)
    st.info(fatigue_signal(history_df))
    help_tip(
        "Fatigue Signal",
        "Uses recent low-RIR and completion trends. If high fatigue is flagged, reduce volume for ~1 week.",
    )

    vol_df = weekly_muscle_volume(history_df)
    if not vol_df.empty:
        st.markdown("#### Weekly Volume by Muscle")
        st.bar_chart(vol_df.set_index("Muscle")["Volume"])

elif menu == "📝 Today’s Workout":
    st.subheader(f"Today’s Workout · {split_type}")
    selected_day = st.selectbox("Routine day", list(active_routine.keys()))

    st.sidebar.markdown("---")
    duration = st.sidebar.selectbox("Rest timer", [60, 90, 120, 180], index=1)
    if st.sidebar.button("Start rest timer", use_container_width=True):
        progress_bar = st.sidebar.progress(0)
        for i in range(100):
            time.sleep(duration / 100)
            progress_bar.progress(i + 1)
        st.sidebar.success("Rest complete. Next set.")

    st.markdown("### Session Flow")
    workout_inputs = {}
    for ex in active_routine[selected_day]:
        ex_name = ex["name"]
        meta = EXERCISE_LIBRARY[ex_name]
        reps = ex["range"]

        st.markdown(f"#### {ex_name} · {reps} reps")
        if equipment_ready(ex_name):
            st.success("Equipment ready for this movement.")
        else:
            st.warning("Primary equipment missing. Use substitution below.")

        suggestion, _ = suggest_progression(ex_name, reps, history_df)
        st.caption(f"Progression: {suggestion}")
        help_tip("Progression", "If you hit top-end reps with ~1-2 RIR, add a small load next session.")
        st.caption(f"Substitutions: {', '.join(meta['fallback'])}")
        help_tip("RIR", "Reps In Reserve: reps left before failure. 2 RIR means ~2 clean reps left.")

        with st.expander("Form demo + cues"):
            st.video(demo_link(meta["url"]))
            st.write("**Key cues**")
            for cue in meta["cues"]:
                st.write(f"- {cue}")
            st.write("**Common mistakes**")
            for err in meta["mistakes"]:
                st.write(f"- {err}")

        cols = st.columns(ex["sets"])
        ex_inputs = []
        for i in range(ex["sets"]):
            with cols[i]:
                st.caption(f"Set {i+1}")
                wt = st.number_input("Wt (lb)", min_value=0.0, step=2.5, key=f"{ex_name}_w_{i}")
                rp = st.number_input("Reps", min_value=0, step=1, key=f"{ex_name}_r_{i}")
                rir = st.slider("RIR", 0, 4, 2, key=f"{ex_name}_rir_{i}")
                ex_inputs.append((i + 1, wt, rp, rir))
        workout_inputs[ex_name] = ex_inputs
        st.divider()

    if st.button("Save workout", type="primary"):
        today_str = datetime.date.today().strftime("%b %d, %Y")
        for ex_name, sets_data in workout_inputs.items():
            for set_num, weight, reps, rir in sets_data:
                save_set_to_csv(today_str, selected_day, ex_name, set_num, weight, reps, rir)
        st.success("Workout saved.")

elif menu == "📈 History & Analytics":
    st.subheader("History & Analytics")
    if history_df.empty:
        st.warning("No sessions logged yet.")
    else:
        st.dataframe(history_df.sort_index(ascending=False), use_container_width=True)
        st.markdown("#### Volume by Exercise")
        ex_vol = history_df.groupby("Exercise", as_index=False)["Volume"].sum().sort_values("Volume", ascending=False)
        st.bar_chart(ex_vol.set_index("Exercise")["Volume"])

elif menu == "📚 Exercise Library":
    st.subheader("Exercise Library & Substitutions")
    for ex_name, meta in EXERCISE_LIBRARY.items():
        with st.expander(ex_name):
            st.write(f"**Muscle:** {meta['muscle']} | **Pattern:** {meta['movement']}")
            st.write(f"**Required equipment:** {', '.join(meta['equipment'])}")
            st.write(f"**Best substitutions:** {', '.join(meta['fallback'])}")
            st.video(demo_link(meta["url"]))

elif menu == "⚙️ Settings":
    st.subheader("Equipment Settings")
    st.caption("Turn equipment on/off to personalize substitutions.")
    for item, owned in list(EQUIPMENT_PROFILE.items()):
        EQUIPMENT_PROFILE[item] = st.checkbox(item, value=owned)
    if EQUIPMENT_PROFILE["Olympic Barbell"]:
        st.success("Nice upgrade. Olympic-bar movements will stay as primary choices.")
    else:
        st.info("No Olympic bar set. The plan prioritizes Smith/DB/KB/SSB substitutions.")

elif menu == "🤖 AI Coach":
    st.subheader("AI Coach")
    raw_key = st.sidebar.text_input("Gemini API Key", type="password")
    api_key = raw_key.strip()

    if not api_key:
        st.info("Add your Gemini API key in sidebar.")
    else:
        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "assistant", "content": "Ask about your home setup, overload, and form."}]

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        if prompt := st.chat_input("Ask your coach..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        payload = {
                            "contents": [
                                {
                                    "parts": [
                                        {
                                            "text": (
                                                "You are an elite hypertrophy coach for a home gym athlete with Smith machine, "
                                                "dumbbells 5-25, kettlebells 15/35, SSB, curl bar, air rower, and power tower. "
                                                f"Question: {prompt}"
                                            )
                                        }
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
                            ai_reply = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                        st.write(ai_reply)
                        st.session_state.messages.append({"role": "assistant", "content": ai_reply})
                    except requests.RequestException as exc:
                        err = f"Network/API error: {exc}"
                        st.write(err)
                        st.session_state.messages.append({"role": "assistant", "content": err})
