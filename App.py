import datetime
import os
import time

import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="HyperCustom Fit", layout="wide", page_icon="🏋️")

DB_FILE = "workout_database.csv"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

EQUIPMENT_CATALOG = [
    "Bench",
    "Dumbbells (5-25 lb pairs)",
    "Adjustable Dumbbells",
    "Kettlebells",
    "Olympic Barbell",
    "Rack",
    "Smith Machine",
    "Cable Machine",
    "Lat Pulldown",
    "Safety Squat Bar",
    "Curl Bar",
    "Air Rower",
    "Power Tower",
]

PROFILE_PRESETS = {
    "Home Gym (MD-9010G style)": ["Bench", "Dumbbells (5-25 lb pairs)", "Kettlebells", "Smith Machine", "Safety Squat Bar", "Curl Bar", "Air Rower", "Power Tower"],
    "Commercial Gym": EQUIPMENT_CATALOG,
    "Minimal Setup": ["Dumbbells (5-25 lb pairs)", "Bench", "Power Tower"],
}

EXERCISE_LIBRARY = {
    "Barbell Bench Press": {"equipment": ["Olympic Barbell", "Bench", "Rack"], "fallback": ["Smith Machine Flat Press", "Dumbbell Flat Press"], "url": "https://www.youtube.com/watch?v=rT7DgCr-3pg", "muscle": "Chest", "movement": "Horizontal Push"},
    "Smith Machine Flat Press": {"equipment": ["Smith Machine", "Bench"], "fallback": ["Dumbbell Flat Press", "Push-Up"], "url": "https://www.youtube.com/watch?v=9R4fQv1U8b0", "muscle": "Chest", "movement": "Horizontal Push"},
    "Dumbbell Flat Press": {"equipment": ["Dumbbells (5-25 lb pairs)", "Bench"], "fallback": ["Push-Up"], "url": "https://www.youtube.com/watch?v=VmB1G1K7v94", "muscle": "Chest", "movement": "Horizontal Push"},
    "Push-Up": {"equipment": [], "fallback": [], "url": "https://www.youtube.com/watch?v=IODxDxX7oi4", "muscle": "Chest", "movement": "Horizontal Push"},
    "Barbell Row": {"equipment": ["Olympic Barbell"], "fallback": ["Chest-Supported DB Row", "Smith Machine Bent Row"], "url": "https://www.youtube.com/watch?v=vT2GjY_Umpw", "muscle": "Back", "movement": "Horizontal Pull"},
    "Chest-Supported DB Row": {"equipment": ["Dumbbells (5-25 lb pairs)", "Bench"], "fallback": ["Smith Machine Bent Row"], "url": "https://www.youtube.com/watch?v=5PoEksoJNaw", "muscle": "Back", "movement": "Horizontal Pull"},
    "Smith Machine Bent Row": {"equipment": ["Smith Machine"], "fallback": ["Inverted Row"], "url": "https://www.youtube.com/watch?v=roCP6wCXPqo", "muscle": "Back", "movement": "Horizontal Pull"},
    "Inverted Row": {"equipment": ["Power Tower"], "fallback": [], "url": "https://www.youtube.com/watch?v=2B6aN8P6WwM", "muscle": "Back", "movement": "Horizontal Pull"},
    "Overhead Press": {"equipment": ["Olympic Barbell", "Rack"], "fallback": ["Smith Machine Overhead Press", "Dumbbell Seated Press"], "url": "https://www.youtube.com/watch?v=2yjwXTZQDDI", "muscle": "Shoulders", "movement": "Vertical Push"},
    "Smith Machine Overhead Press": {"equipment": ["Smith Machine", "Bench"], "fallback": ["Dumbbell Seated Press"], "url": "https://www.youtube.com/watch?v=R5JhoUX4hRQ", "muscle": "Shoulders", "movement": "Vertical Push"},
    "Dumbbell Seated Press": {"equipment": ["Dumbbells (5-25 lb pairs)", "Bench"], "fallback": [], "url": "https://www.youtube.com/watch?v=qEwKCR5JCog", "muscle": "Shoulders", "movement": "Vertical Push"},
    "Lat Pulldown": {"equipment": ["Lat Pulldown"], "fallback": ["Pull-Up", "Inverted Row"], "url": "https://www.youtube.com/watch?v=CAwf7n6Luuc", "muscle": "Back", "movement": "Vertical Pull"},
    "Pull-Up": {"equipment": ["Power Tower"], "fallback": ["Inverted Row"], "url": "https://www.youtube.com/watch?v=eGo4IYlbE5g", "muscle": "Back", "movement": "Vertical Pull"},
    "Back Squat": {"equipment": ["Olympic Barbell", "Rack"], "fallback": ["Safety Squat Bar Squat", "Smith Machine Squat", "Goblet Squat"], "url": "https://www.youtube.com/watch?v=Dy28eq2PjcM", "muscle": "Quads", "movement": "Squat"},
    "Safety Squat Bar Squat": {"equipment": ["Safety Squat Bar"], "fallback": ["Smith Machine Squat", "Goblet Squat"], "url": "https://www.youtube.com/shorts/1oed-UmAxFs", "muscle": "Quads", "movement": "Squat"},
    "Smith Machine Squat": {"equipment": ["Smith Machine"], "fallback": ["Goblet Squat"], "url": "https://www.youtube.com/watch?v=fEuYM-miK5U", "muscle": "Quads", "movement": "Squat"},
    "Goblet Squat": {"equipment": ["Kettlebells"], "fallback": ["Dumbbell Split Squat"], "url": "https://www.youtube.com/shorts/sz0S9V5nXJ0", "muscle": "Quads", "movement": "Squat"},
    "Dumbbell Split Squat": {"equipment": ["Dumbbells (5-25 lb pairs)"], "fallback": [], "url": "https://www.youtube.com/watch?v=2C-uNgKwPLE", "muscle": "Quads", "movement": "Squat"},
    "Romanian Deadlift": {"equipment": ["Olympic Barbell"], "fallback": ["Dumbbell Romanian Deadlift", "Curl Bar RDL"], "url": "https://www.youtube.com/watch?v=2SHsk9AzdjA", "muscle": "Hamstrings", "movement": "Hinge"},
    "Dumbbell Romanian Deadlift": {"equipment": ["Dumbbells (5-25 lb pairs)"], "fallback": ["Curl Bar RDL"], "url": "https://www.youtube.com/shorts/7j-2m8M1M90", "muscle": "Hamstrings", "movement": "Hinge"},
    "Curl Bar RDL": {"equipment": ["Curl Bar"], "fallback": [], "url": "https://www.youtube.com/watch?v=jEy_czb3RKA", "muscle": "Hamstrings", "movement": "Hinge"},
}

PROGRAMS = {
    "3-Day Full Body": {
        "days": 3,
        "routine": {
            "Day 1": [("Barbell Bench Press", "6-10", 3), ("Barbell Row", "8-12", 3), ("Back Squat", "6-10", 3)],
            "Day 2": [("Overhead Press", "6-10", 3), ("Lat Pulldown", "8-12", 3), ("Romanian Deadlift", "8-12", 3)],
            "Day 3": [("Dumbbell Flat Press", "8-12", 3), ("Chest-Supported DB Row", "10-15", 3), ("Goblet Squat", "10-15", 3)],
        },
    },
    "4-Day Upper/Lower": {
        "days": 4,
        "routine": {
            "Day 1 Upper": [("Barbell Bench Press", "6-10", 3), ("Barbell Row", "8-12", 3), ("Overhead Press", "8-12", 3)],
            "Day 2 Lower": [("Back Squat", "6-10", 3), ("Romanian Deadlift", "8-12", 3), ("Goblet Squat", "10-15", 2)],
            "Day 3 Upper": [("Dumbbell Flat Press", "8-12", 3), ("Lat Pulldown", "8-12", 3), ("Dumbbell Seated Press", "10-15", 3)],
            "Day 4 Lower": [("Safety Squat Bar Squat", "8-12", 3), ("Dumbbell Romanian Deadlift", "10-15", 3), ("Dumbbell Split Squat", "10-15", 2)],
        },
    },
}


def init_state():
    if "selected_equipment" not in st.session_state:
        st.session_state.selected_equipment = PROFILE_PRESETS["Home Gym (MD-9010G style)"]


def has_eq(ex_name):
    req = EXERCISE_LIBRARY[ex_name]["equipment"]
    return all(eq in st.session_state.selected_equipment for eq in req)


def best_alt(ex_name):
    for alt in EXERCISE_LIBRARY[ex_name]["fallback"]:
        if alt in EXERCISE_LIBRARY and has_eq(alt):
            return alt
    return None


def adapt_program(program_name):
    base = PROGRAMS[program_name]["routine"]
    adapted = {}
    for day, items in base.items():
        adapted_items = []
        for ex, rr, sets in items:
            chosen = ex if has_eq(ex) else best_alt(ex)
            if chosen:
                adapted_items.append((chosen, rr, sets, ex != chosen))
        adapted[day] = adapted_items
    return adapted


def recommended_program(days_available):
    if days_available >= 4:
        return "4-Day Upper/Lower"
    return "3-Day Full Body"


def save_set(row):
    frame = pd.DataFrame([row])
    if not os.path.exists(DB_FILE):
        frame.to_csv(DB_FILE, index=False)
    else:
        frame.to_csv(DB_FILE, mode="a", header=False, index=False)


def load_history():
    if not os.path.exists(DB_FILE):
        return pd.DataFrame()
    try:
        df = pd.read_csv(DB_FILE)
    except (pd.errors.EmptyDataError, pd.errors.ParserError):
        return pd.DataFrame()
    for col, default in [("Weight_lbs", 0.0), ("Reps", 0), ("RIR", 0), ("Volume", 0.0), ("Program", "")]:
        if col not in df.columns:
            df[col] = default
    return df


def to_embed(url):
    if "watch?v=" in url:
        vid = url.split("watch?v=")[-1].split("&")[0]
        return f"https://www.youtube.com/embed/{vid}?start=5&end=65"
    if "youtu.be/" in url:
        vid = url.split("youtu.be/")[-1].split("?")[0]
        return f"https://www.youtube.com/embed/{vid}?start=5&end=65"
    return url


init_state()
history = load_history()

st.title("🏋️ HyperCustom Fit")
st.caption("Equipment-aware training plans for home and commercial gyms.")

with st.sidebar:
    st.header("Setup")
    preset = st.selectbox("Equipment preset", list(PROFILE_PRESETS.keys()))
    if st.button("Load preset", use_container_width=True):
        st.session_state.selected_equipment = PROFILE_PRESETS[preset].copy()
    st.session_state.selected_equipment = st.multiselect("Your equipment", EQUIPMENT_CATALOG, default=st.session_state.selected_equipment)

    days = st.slider("Days/week available", 2, 6, 4)
    suggested = recommended_program(days)
    st.success(f"Suggested plan: {suggested}")
    chosen_program = st.selectbox("Program", list(PROGRAMS.keys()), index=list(PROGRAMS.keys()).index(suggested))

    view = st.radio("Screen", ["Dashboard", "Workout", "Program Builder", "History", "Exercise Library", "AI Coach"])
    st.markdown("---")
    rest = st.selectbox("Rest timer", [60, 90, 120, 180], 1)
    if st.button("Start Rest Timer", use_container_width=True):
        bar = st.progress(0)
        for i in range(100):
            time.sleep(rest / 100)
            bar.progress(i + 1)
        st.success("Rest complete")

adapted = adapt_program(chosen_program)

if view == "Dashboard":
    c1, c2, c3 = st.columns(3)
    c1.metric("Equipment Selected", len(st.session_state.selected_equipment))
    c2.metric("Program Days", PROGRAMS[chosen_program]["days"])
    c3.metric("Logged Sets", 0 if history.empty else int(history.shape[0]))

    st.subheader("Your Current Adapted Program")
    for day, items in adapted.items():
        with st.expander(day):
            for ex, rr, sets, swapped in items:
                flag = " (auto-sub)" if swapped else ""
                st.write(f"- {ex}{flag} · {sets} x {rr}")

elif view == "Program Builder":
    st.subheader("Program Recommendations")
    st.write("- Train **3 days/week**: Full-body plan to maximize frequency per muscle.")
    st.write("- Train **4 days/week or more**: Upper/Lower split for extra volume and recovery balance.")
    st.info("The app auto-swaps unsupported exercises based on selected equipment.")

    table_rows = []
    for pname, pdata in PROGRAMS.items():
        total_ex = sum(len(v) for v in pdata["routine"].values())
        supported = sum(1 for d in pdata["routine"].values() for e, _, _ in d if has_eq(e) or best_alt(e))
        table_rows.append({"Program": pname, "Days": pdata["days"], "Exercises Supported": f"{supported}/{total_ex}"})
    st.dataframe(pd.DataFrame(table_rows), use_container_width=True)

elif view == "Workout":
    st.subheader(f"Workout · {chosen_program}")
    day = st.selectbox("Choose workout day", list(adapted.keys()))
    plan = adapted[day]
    payload = {}

    for idx, (ex, rr, sets, swapped) in enumerate(plan, start=1):
        meta = EXERCISE_LIBRARY[ex]
        with st.container(border=True):
            st.markdown(f"### {idx}. {ex}")
            if swapped:
                st.warning("Auto-substituted based on equipment.")
            st.caption(f"{sets} sets · {rr} reps")
            tab1, tab2 = st.tabs(["Log", "Demo"])
            with tab1:
                cols = st.columns(sets)
                rows = []
                for i in range(sets):
                    with cols[i]:
                        wt = st.number_input("Wt", min_value=0.0, step=2.5, key=f"{day}_{ex}_w_{i}")
                        reps = st.number_input("Reps", min_value=0, step=1, key=f"{day}_{ex}_r_{i}")
                        rir = st.slider("RIR", 0, 4, 2, key=f"{day}_{ex}_rir_{i}")
                        done = st.checkbox("Done", key=f"{day}_{ex}_d_{i}")
                        rows.append((i + 1, wt, reps, rir, done))
                payload[ex] = rows
            with tab2:
                st.video(to_embed(meta["url"]))

    if st.button("Save Workout", type="primary"):
        today = datetime.date.today().strftime("%b %d, %Y")
        for ex, rows in payload.items():
            for set_num, wt, reps, rir, done in rows:
                if done:
                    save_set({
                        "Date": today,
                        "Program": chosen_program,
                        "Routine": day,
                        "Exercise": ex,
                        "Set": set_num,
                        "Weight_lbs": wt,
                        "Reps": reps,
                        "RIR": rir,
                        "Volume": wt * reps,
                    })
        st.success("Workout saved")

elif view == "History":
    st.subheader("History")
    if history.empty:
        st.info("No history yet.")
    else:
        st.dataframe(history.sort_index(ascending=False), use_container_width=True)

elif view == "Exercise Library":
    st.subheader("Exercise Library")
    for ex, meta in EXERCISE_LIBRARY.items():
        with st.expander(ex):
            st.write(f"Required: {', '.join(meta['equipment']) if meta['equipment'] else 'None'}")
            st.write(f"Fallbacks: {', '.join(meta['fallback']) if meta['fallback'] else 'None'}")
            st.video(to_embed(meta["url"]))

elif view == "AI Coach":
    st.subheader("AI Coach")
    api_key = st.sidebar.text_input("Gemini API Key", type="password").strip()
    if not api_key:
        st.info("Add Gemini API key in sidebar")
    else:
        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "assistant", "content": "Ask about programs, equipment, or substitutions."}]
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
        if prompt := st.chat_input("Ask your coach..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("assistant"):
                try:
                    equipment_text = ", ".join(st.session_state.selected_equipment)
                    payload = {"contents": [{"parts": [{"text": f"You are a coach. User equipment: {equipment_text}. Program: {chosen_program}. Question: {prompt}"}]}]}
                    response = requests.post(GEMINI_API_URL, json=payload, headers={"Content-Type": "application/json"}, params={"key": api_key}, timeout=20)
                    reply = f"Connection rejected ({response.status_code})." if response.status_code != 200 else response.json()["candidates"][0]["content"]["parts"][0]["text"]
                except requests.RequestException as exc:
                    reply = f"Network/API error: {exc}"
                st.write(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
