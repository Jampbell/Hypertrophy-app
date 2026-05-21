import datetime
import os
import time

import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="HyperCustom Fit", layout="wide", page_icon="🏋️")

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
    "Bench": True,
}

EXERCISE_LIBRARY = {
    "Smith Machine Flat Press": {
        "muscle": "Chest", "movement": "Horizontal Push", "equipment": ["Marcy Smith MD-9010G", "Bench"],
        "fallback": ["Dumbbell Flat Press", "Power Tower Push-Ups"],
        "cues": ["Scaps back/down", "Lower with control", "Drive evenly"],
        "mistakes": ["Short ROM", "Wrists bent", "Bench misaligned"],
        "url": "https://www.youtube.com/watch?v=9R4fQv1U8b0",
    },
    "Dumbbell Flat Press": {
        "muscle": "Chest", "movement": "Horizontal Push", "equipment": ["Dumbbells (5-25 lb pairs)", "Bench"],
        "fallback": ["Smith Machine Flat Press", "Power Tower Push-Ups"],
        "cues": ["Forearms vertical", "Control eccentric", "Feet planted"],
        "mistakes": ["Elbows too high", "Bouncing", "Shoulder shrug"],
        "url": "https://www.youtube.com/watch?v=VmB1G1K7v94",
    },
    "Chest-Supported DB Row": {
        "muscle": "Back", "movement": "Horizontal Pull", "equipment": ["Dumbbells (5-25 lb pairs)", "Bench"],
        "fallback": ["Smith Machine Bent Row", "Air Rower Intervals"],
        "cues": ["Chest glued to bench", "Elbows to hips", "Pause squeeze"],
        "mistakes": ["Torso twisting", "Neck strain", "Yanking"],
        "url": "https://www.youtube.com/watch?v=5PoEksoJNaw",
    },
    "Smith Machine Bent Row": {
        "muscle": "Back", "movement": "Horizontal Pull", "equipment": ["Marcy Smith MD-9010G"],
        "fallback": ["Chest-Supported DB Row"],
        "cues": ["Hinge + brace", "Bar to lower ribs", "Neutral neck"],
        "mistakes": ["Standing too tall", "Rounded back", "Shrugging"],
        "url": "https://www.youtube.com/watch?v=roCP6wCXPqo",
    },
    "Lat Pulldown / Pull-up": {
        "muscle": "Back", "movement": "Vertical Pull", "equipment": ["Marcy Smith MD-9010G", "Power Tower (pull-up/dip station)"],
        "fallback": ["Inverted Row on Smith Bar"],
        "cues": ["Lead with elbows", "Chest up", "Full stretch"],
        "mistakes": ["Momentum", "Shrugging", "Half reps"],
        "url": "https://www.youtube.com/watch?v=CAwf7n6Luuc",
    },
    "Safety Squat Bar Squat": {
        "muscle": "Quads", "movement": "Squat", "equipment": ["Safety Squat Bar"],
        "fallback": ["Smith Machine Squat", "Goblet Squat (35 lb KB)"],
        "cues": ["Brace first", "Knees track toes", "Drive midfoot"],
        "mistakes": ["Heels up", "Knee cave", "Chest collapse"],
        "url": "https://www.youtube.com/shorts/1oed-UmAxFs",
    },
    "Smith Machine Squat": {
        "muscle": "Quads", "movement": "Squat", "equipment": ["Marcy Smith MD-9010G"],
        "fallback": ["Goblet Squat (35 lb KB)"],
        "cues": ["Feet slightly forward", "Sit between hips", "Depth with control"],
        "mistakes": ["Shallow reps", "Knee cave", "Collapsing trunk"],
        "url": "https://www.youtube.com/watch?v=fEuYM-miK5U",
    },
    "Goblet Squat (35 lb KB)": {
        "muscle": "Quads", "movement": "Squat", "equipment": ["Kettlebells (15 lb, 35 lb)"],
        "fallback": ["Smith Machine Squat"],
        "cues": ["Bell high", "Elbows in", "Tall torso"],
        "mistakes": ["Toes-only pressure", "Chest drop", "No depth"],
        "url": "https://www.youtube.com/shorts/sz0S9V5nXJ0",
    },
    "Dumbbell Romanian Deadlift": {
        "muscle": "Hamstrings", "movement": "Hinge", "equipment": ["Dumbbells (5-25 lb pairs)"],
        "fallback": ["Curl Bar RDL", "Kettlebell RDL"],
        "cues": ["Soft knees", "Hips back", "Weights close"],
        "mistakes": ["Squatting rep", "Rounded back", "Neck crank"],
        "url": "https://www.youtube.com/shorts/7j-2m8M1M90",
    },
    "Curl Bar RDL": {
        "muscle": "Hamstrings", "movement": "Hinge", "equipment": ["Curl Bar"],
        "fallback": ["Dumbbell Romanian Deadlift"],
        "cues": ["Hips back", "Brace lats", "Full hip lockout"],
        "mistakes": ["Bar drifting away", "Too much knee bend", "Rounded low back"],
        "url": "https://www.youtube.com/watch?v=jEy_czb3RKA",
    },
    "Inverted Row on Smith Bar": {
        "muscle": "Back", "movement": "Horizontal Pull", "equipment": ["Marcy Smith MD-9010G"],
        "fallback": ["Chest-Supported DB Row"],
        "cues": ["Rigid body", "Chest to bar", "Slow lower"],
        "mistakes": ["Hip sag", "Half ROM", "Shrugging"],
        "url": "https://www.youtube.com/watch?v=2B6aN8P6WwM",
    },
    "Air Rower Intervals": {
        "muscle": "Conditioning", "movement": "Conditioning", "equipment": ["Air Rower"],
        "fallback": ["Power Tower Knee Raises"],
        "cues": ["Leg drive first", "Then hips", "Then arms"],
        "mistakes": ["Early arm pull", "Fast sloppy strokes", "Rounded low back"],
        "url": "https://www.youtube.com/watch?v=zQ82RYIFLN8",
    },
    "Power Tower Knee Raises": {
        "muscle": "Core", "movement": "Conditioning", "equipment": ["Power Tower (pull-up/dip station)"],
        "fallback": ["Air Rower Intervals"],
        "cues": ["Posterior tilt", "Slow raise", "No swing"],
        "mistakes": ["Using momentum", "Shrugging", "Tiny ROM"],
        "url": "https://www.youtube.com/watch?v=JB2oyawG9KI",
    },
}

ROUTINES = {
    "3-Day Full Blend": {
        "Day 1: Upper": [
            {"name": "Smith Machine Flat Press", "range": "8-10", "sets": 3},
            {"name": "Chest-Supported DB Row", "range": "8-12", "sets": 3},
            {"name": "Lat Pulldown / Pull-up", "range": "8-12", "sets": 3},
            {"name": "Air Rower Intervals", "range": "10-15", "sets": 2},
        ],
        "Day 2: Lower": [
            {"name": "Safety Squat Bar Squat", "range": "8-10", "sets": 3},
            {"name": "Dumbbell Romanian Deadlift", "range": "10-12", "sets": 3},
            {"name": "Goblet Squat (35 lb KB)", "range": "12-15", "sets": 2},
            {"name": "Power Tower Knee Raises", "range": "12-20", "sets": 2},
        ],
        "Day 3: Full Body": [
            {"name": "Dumbbell Flat Press", "range": "8-12", "sets": 3},
            {"name": "Smith Machine Bent Row", "range": "8-12", "sets": 3},
            {"name": "Curl Bar RDL", "range": "10-12", "sets": 3},
        ],
    }
}


def tip(label: str, body: str):
    with st.popover(f"❓ {label}"):
        st.caption(body)


def parse_range(text: str):
    lo, hi = text.split("-")
    return int(lo), int(hi)


def save_set(date_s, day, exercise, set_num, wt, reps, rir):
    row = pd.DataFrame([{
        "Date": date_s,
        "Routine": day,
        "Exercise": exercise,
        "Set": set_num,
        "Weight_lbs": float(wt),
        "Reps": int(reps),
        "RIR": int(rir),
        "Volume": float(wt) * int(reps),
    }])
    if not os.path.exists(DB_FILE):
        row.to_csv(DB_FILE, index=False)
    else:
        row.to_csv(DB_FILE, mode="a", header=False, index=False)


def load_history():
    if not os.path.exists(DB_FILE):
        return pd.DataFrame()
    try:
        df = pd.read_csv(DB_FILE)
    except (pd.errors.EmptyDataError, pd.errors.ParserError):
        return pd.DataFrame()
    for col, default in [("Weight_lbs", 0.0), ("Reps", 0), ("RIR", 0), ("Volume", 0.0)]:
        if col not in df.columns:
            df[col] = default
    return df


def can_do(exercise: str):
    required = EXERCISE_LIBRARY[exercise]["equipment"]
    return all(EQUIPMENT_PROFILE.get(item, False) for item in required)


def best_swap(exercise: str):
    for alt in EXERCISE_LIBRARY[exercise]["fallback"]:
        if alt in EXERCISE_LIBRARY and can_do(alt):
            return alt
    return None


def progression(exercise: str, rep_range: str, df: pd.DataFrame):
    if df.empty:
        return "No history yet. Start smooth and leave 2 RIR."
    ex = df[df["Exercise"] == exercise]
    if ex.empty:
        return "First time for this movement. Start moderate and build."
    last_date = ex["Date"].iloc[-1]
    last = ex[ex["Date"] == last_date]
    avg_w = last["Weight_lbs"].mean()
    avg_r = last["Reps"].mean()
    avg_rir = last["RIR"].mean()
    _, high = parse_range(rep_range)
    if avg_r >= high and avg_rir >= 1:
        return f"Hit top range. Next time add +2.5 to +5 lb (target ~{avg_w + 5:.1f})."
    return f"Hold around {avg_w:.1f} lb and add reps with clean form."


def to_embed(url: str):
    if "watch?v=" in url:
        vid = url.split("watch?v=")[-1].split("&")[0]
        return f"https://www.youtube.com/embed/{vid}?start=5&end=70"
    if "youtu.be/" in url:
        vid = url.split("youtu.be/")[-1].split("?")[0]
        return f"https://www.youtube.com/embed/{vid}?start=5&end=70"
    return url


def kpis(df: pd.DataFrame):
    if df.empty:
        return 0, 0, 0
    return int(df.shape[0]), int(df["Exercise"].nunique()), float(df["Volume"].sum())


st.title("🏋️ HyperCustom Fit")
st.caption("Simple, clean home-gym training tracker with smart guidance.")

history = load_history()
set_count, exercise_count, total_volume = kpis(history)

with st.sidebar:
    st.header("Program")
    split = st.selectbox("Choose Routine", list(ROUTINES.keys()))
    screen = st.radio("Go to", ["Dashboard", "Workout", "History", "Exercise Library", "AI Coach", "Settings"])
    st.markdown("---")
    rest = st.selectbox("Rest timer (sec)", [60, 90, 120, 180], index=1)
    if st.button("Start rest timer", use_container_width=True):
        bar = st.progress(0)
        for i in range(100):
            time.sleep(rest / 100)
            bar.progress(i + 1)
        st.success("Rest done. Start next set.")

if screen == "Dashboard":
    a, b, c = st.columns(3)
    a.metric("Logged Sets", set_count)
    b.metric("Unique Exercises", exercise_count)
    c.metric("Total Volume", f"{total_volume:.0f} lb")

    tip("RIR", "Reps In Reserve: if RIR is 2, you had about 2 reps left before failure.")

    if history.empty:
        st.info("No workouts logged yet. Start in Workout tab.")
    else:
        by_ex = history.groupby("Exercise", as_index=False)["Volume"].sum().sort_values("Volume", ascending=False)
        st.subheader("Volume by Exercise")
        st.bar_chart(by_ex.set_index("Exercise"))

elif screen == "Workout":
    st.subheader("Today’s Workout")
    day = st.selectbox("Select Day", list(ROUTINES[split].keys()))
    plan = ROUTINES[split][day]

    total = len(plan)
    done = 0
    payload = {}

    for i, item in enumerate(plan, start=1):
        name = item["name"]
        rr = item["range"]
        sets = item["sets"]

        active = name
        if not can_do(name):
            alt = best_swap(name)
            if alt:
                st.warning(f"{name} unavailable with current equipment. Swapped to {alt}.")
                active = alt
            else:
                st.error(f"{name} unavailable and no valid substitution found.")
                continue

        meta = EXERCISE_LIBRARY[active]

        with st.container(border=True):
            st.markdown(f"### {i}. {active}")
            st.caption(f"Target reps: {rr} | Sets: {sets}")
            st.caption(f"Progression: {progression(active, rr, history)}")
            st.caption(f"Fallbacks: {', '.join(meta['fallback'])}")
            tip("Exercise Tip", "Keep 1-2 RIR on most working sets. Add load only when reps are stable and clean.")

            tab1, tab2 = st.tabs(["Log Sets", "Form & Cues"])
            with tab1:
                cols = st.columns(sets)
                sets_data = []
                set_done = []
                for j in range(sets):
                    with cols[j]:
                        st.caption(f"Set {j+1}")
                        wt = st.number_input("Weight", min_value=0.0, step=2.5, key=f"{day}_{active}_w_{j}")
                        rp = st.number_input("Reps", min_value=0, step=1, key=f"{day}_{active}_r_{j}")
                        rir = st.slider("RIR", 0, 4, 2, key=f"{day}_{active}_rir_{j}")
                        ok = st.checkbox("Done", key=f"{day}_{active}_d_{j}")
                        sets_data.append((j + 1, wt, rp, rir, ok))
                        set_done.append(ok)
                payload[active] = sets_data
                if all(set_done):
                    done += 1

            with tab2:
                st.video(to_embed(meta["url"]))
                st.write("**Cues**")
                for cue in meta["cues"]:
                    st.write(f"- {cue}")
                st.write("**Common mistakes**")
                for m in meta["mistakes"]:
                    st.write(f"- {m}")

    pct = int((done / total) * 100) if total else 0
    st.progress(pct / 100)
    st.caption(f"Session completion: {pct}%")

    if st.button("Save Workout", type="primary"):
        today = datetime.date.today().strftime("%b %d, %Y")
        for ex_name, rows in payload.items():
            for set_num, wt, rp, rir, ok in rows:
                if ok:
                    save_set(today, day, ex_name, set_num, wt, rp, rir)
        st.success("Workout saved.")

elif screen == "History":
    st.subheader("History")
    if history.empty:
        st.info("No history yet.")
    else:
        st.dataframe(history.sort_index(ascending=False), use_container_width=True)

elif screen == "Exercise Library":
    st.subheader("Exercise Library")
    for ex_name, meta in EXERCISE_LIBRARY.items():
        with st.expander(ex_name):
            st.write(f"**Muscle:** {meta['muscle']} | **Movement:** {meta['movement']}")
            st.write(f"**Required equipment:** {', '.join(meta['equipment'])}")
            st.write(f"**Fallbacks:** {', '.join(meta['fallback'])}")
            st.video(to_embed(meta["url"]))

elif screen == "Settings":
    st.subheader("Equipment Settings")
    st.caption("Toggle what you currently own. This controls auto-substitutions.")
    for item in list(EQUIPMENT_PROFILE.keys()):
        EQUIPMENT_PROFILE[item] = st.checkbox(item, value=EQUIPMENT_PROFILE[item])

elif screen == "AI Coach":
    st.subheader("AI Coach")
    key = st.sidebar.text_input("Gemini API Key", type="password").strip()
    if not key:
        st.info("Add your Gemini API key in the sidebar to chat.")
    else:
        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "assistant", "content": "Ask me about programming, substitutions, or form."}]
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        if prompt := st.chat_input("Ask your question..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        payload = {
                            "contents": [{"parts": [{"text": (
                                "You are a hypertrophy coach for a home gym athlete. "
                                "Equipment: Smith machine MD-9010G, DB 5-25, KB 15/35, SSB, curl bar, air rower, power tower. "
                                f"Question: {prompt}"
                            )}]}]
                        }
                        response = requests.post(
                            GEMINI_API_URL,
                            json=payload,
                            headers={"Content-Type": "application/json"},
                            params={"key": key},
                            timeout=20,
                        )
                        if response.status_code != 200:
                            reply = f"Connection rejected ({response.status_code})."
                        else:
                            reply = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                        st.write(reply)
                        st.session_state.messages.append({"role": "assistant", "content": reply})
                    except requests.RequestException as exc:
                        err = f"Network/API error: {exc}"
                        st.write(err)
                        st.session_state.messages.append({"role": "assistant", "content": err})
