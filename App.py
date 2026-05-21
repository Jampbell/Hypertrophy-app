import datetime
import os
import re
import time

import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="HyperCustom Fit", layout="wide", page_icon="🏋️")

DB_FILE = "workout_database.csv"
GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

EQUIPMENT_CATALOG = [
    "Bench", "Adjustable Bench", "Dumbbells", "Adjustable Dumbbells", "Kettlebells", "Olympic Barbell", "EZ Curl Bar",
    "Trap Bar", "Safety Squat Bar", "Squat Rack", "Half Rack", "Power Rack", "Smith Machine", "Cable Machine",
    "Functional Trainer", "Lat Pulldown", "Leg Press", "Leg Extension", "Leg Curl", "Pec Deck", "Dip Bars",
    "Pull-Up Bar", "Power Tower", "Resistance Bands", "Suspension Trainer", "Air Rower", "Treadmill", "Bike", "Stair Climber"
]

PROFILE_PRESETS = {
    "Home Gym": ["Bench", "Dumbbells", "Kettlebells", "Smith Machine", "Safety Squat Bar", "EZ Curl Bar", "Air Rower", "Power Tower"],
    "Commercial Gym": EQUIPMENT_CATALOG,
    "Minimal": ["Dumbbells", "Bench", "Resistance Bands"],
}

EXERCISE_LIBRARY = {
    "Barbell Bench Press": {"equipment": ["Olympic Barbell", "Bench", "Squat Rack"], "fallback": ["Smith Machine Bench Press", "Dumbbell Bench Press"], "url": "https://www.youtube.com/watch?v=rT7DgCr-3pg"},
    "Smith Machine Bench Press": {"equipment": ["Smith Machine", "Bench"], "fallback": ["Dumbbell Bench Press", "Push-Up"], "url": "https://www.youtube.com/watch?v=9R4fQv1U8b0"},
    "Dumbbell Bench Press": {"equipment": ["Dumbbells", "Bench"], "fallback": ["Push-Up"], "url": "https://www.youtube.com/watch?v=VmB1G1K7v94"},
    "Push-Up": {"equipment": [], "fallback": [], "url": "https://www.youtube.com/watch?v=IODxDxX7oi4"},
    "Barbell Row": {"equipment": ["Olympic Barbell"], "fallback": ["Chest-Supported DB Row"], "url": "https://www.youtube.com/watch?v=vT2GjY_Umpw"},
    "Chest-Supported DB Row": {"equipment": ["Dumbbells", "Bench"], "fallback": ["Cable Row"], "url": "https://www.youtube.com/watch?v=5PoEksoJNaw"},
    "Cable Row": {"equipment": ["Cable Machine"], "fallback": ["Chest-Supported DB Row"], "url": "https://www.youtube.com/watch?v=GZbfZ033f74"},
    "Overhead Press": {"equipment": ["Olympic Barbell", "Squat Rack"], "fallback": ["Dumbbell Shoulder Press", "Smith Machine Overhead Press"], "url": "https://www.youtube.com/watch?v=2yjwXTZQDDI"},
    "Dumbbell Shoulder Press": {"equipment": ["Dumbbells", "Bench"], "fallback": ["Smith Machine Overhead Press"], "url": "https://www.youtube.com/watch?v=qEwKCR5JCog"},
    "Smith Machine Overhead Press": {"equipment": ["Smith Machine", "Bench"], "fallback": ["Dumbbell Shoulder Press"], "url": "https://www.youtube.com/watch?v=R5JhoUX4hRQ"},
    "Lat Pulldown": {"equipment": ["Lat Pulldown"], "fallback": ["Pull-Up"], "url": "https://www.youtube.com/watch?v=CAwf7n6Luuc"},
    "Pull-Up": {"equipment": ["Pull-Up Bar"], "fallback": ["Lat Pulldown"], "url": "https://www.youtube.com/watch?v=eGo4IYlbE5g"},
    "Back Squat": {"equipment": ["Olympic Barbell", "Squat Rack"], "fallback": ["Safety Squat Bar Squat", "Smith Machine Squat", "Goblet Squat"], "url": "https://www.youtube.com/watch?v=Dy28eq2PjcM"},
    "Safety Squat Bar Squat": {"equipment": ["Safety Squat Bar"], "fallback": ["Smith Machine Squat", "Goblet Squat"], "url": "https://www.youtube.com/watch?v=5MTEf2hP9PY"},
    "Smith Machine Squat": {"equipment": ["Smith Machine"], "fallback": ["Goblet Squat"], "url": "https://www.youtube.com/watch?v=fEuYM-miK5U"},
    "Goblet Squat": {"equipment": ["Kettlebells"], "fallback": ["Dumbbell Split Squat"], "url": "https://www.youtube.com/watch?v=6xwGFn-J_QM"},
    "Dumbbell Split Squat": {"equipment": ["Dumbbells"], "fallback": [], "url": "https://www.youtube.com/watch?v=2C-uNgKwPLE"},
    "Romanian Deadlift": {"equipment": ["Olympic Barbell"], "fallback": ["Dumbbell Romanian Deadlift", "EZ Bar Romanian Deadlift"], "url": "https://www.youtube.com/watch?v=2SHsk9AzdjA"},
    "Dumbbell Romanian Deadlift": {"equipment": ["Dumbbells"], "fallback": ["EZ Bar Romanian Deadlift"], "url": "https://www.youtube.com/watch?v=0zG7o6hR0dQ"},
    "EZ Bar Romanian Deadlift": {"equipment": ["EZ Curl Bar"], "fallback": ["Dumbbell Romanian Deadlift"], "url": "https://www.youtube.com/watch?v=jEy_czb3RKA"},
}

PROGRAMS = {
    "3-Day Full Body": {"days": 3, "routine": {
        "Day 1": [("Barbell Bench Press", "6-10", 3), ("Barbell Row", "8-12", 3), ("Back Squat", "6-10", 3)],
        "Day 2": [("Overhead Press", "6-10", 3), ("Lat Pulldown", "8-12", 3), ("Romanian Deadlift", "8-12", 3)],
        "Day 3": [("Dumbbell Bench Press", "8-12", 3), ("Chest-Supported DB Row", "10-15", 3), ("Goblet Squat", "10-15", 3)],
    }},
    "4-Day Upper/Lower": {"days": 4, "routine": {
        "Day 1 Upper": [("Barbell Bench Press", "6-10", 3), ("Barbell Row", "8-12", 3), ("Overhead Press", "8-12", 3)],
        "Day 2 Lower": [("Back Squat", "6-10", 3), ("Romanian Deadlift", "8-12", 3), ("Goblet Squat", "10-15", 2)],
        "Day 3 Upper": [("Dumbbell Bench Press", "8-12", 3), ("Lat Pulldown", "8-12", 3), ("Dumbbell Shoulder Press", "10-15", 3)],
        "Day 4 Lower": [("Safety Squat Bar Squat", "8-12", 3), ("Dumbbell Romanian Deadlift", "10-15", 3), ("Dumbbell Split Squat", "10-15", 2)],
    }},
}


def init_state():
    ss = st.session_state
    ss.setdefault("selected_equipment", PROFILE_PRESETS["Home Gym"].copy())
    ss.setdefault("messages", [{"role": "assistant", "content": "Ask me about programming, substitutions, or app settings."}])
    ss.setdefault("rest_seconds", 90)
    ss.setdefault("rest_end", 0.0)
    ss.setdefault("days_available", 4)
    ss.setdefault("weight_targets", {})


def has_eq(ex):
    req = EXERCISE_LIBRARY[ex]["equipment"]
    return all(x in st.session_state.selected_equipment for x in req)


def best_alt(ex):
    for alt in EXERCISE_LIBRARY[ex]["fallback"]:
        if alt in EXERCISE_LIBRARY and has_eq(alt):
            return alt
    return None


def adapt_program(program_name):
    adapted = {}
    for day, items in PROGRAMS[program_name]["routine"].items():
        out = []
        for ex, rr, sets in items:
            chosen = ex if has_eq(ex) else best_alt(ex)
            if chosen:
                out.append((chosen, rr, sets, chosen != ex))
        adapted[day] = out
    return adapted


def recommended_program(days):
    return "4-Day Upper/Lower" if days >= 4 else "3-Day Full Body"


def save_set(row):
    df = pd.DataFrame([row])
    if not os.path.exists(DB_FILE):
        df.to_csv(DB_FILE, index=False)
    else:
        df.to_csv(DB_FILE, mode="a", header=False, index=False)


def load_history():
    if not os.path.exists(DB_FILE):
        return pd.DataFrame()
    try:
        df = pd.read_csv(DB_FILE)
    except (pd.errors.EmptyDataError, pd.errors.ParserError):
        return pd.DataFrame()
    for c, d in [("Weight_lbs", 0.0), ("Reps", 0), ("RIR", 0), ("Volume", 0.0), ("Program", "")]:
        if c not in df.columns:
            df[c] = d
    return df


def to_embed(url):
    if "watch?v=" in url:
        vid = url.split("watch?v=")[-1].split("&")[0]
        return f"https://www.youtube.com/embed/{vid}?start=5&end=65"
    if "youtu.be/" in url:
        vid = url.split("youtu.be/")[-1].split("?")[0]
        return f"https://www.youtube.com/embed/{vid}?start=5&end=65"
    if "youtube.com/shorts/" in url:
        vid = url.split("shorts/")[-1].split("?")[0].split("/")[0]
        return f"https://www.youtube.com/embed/{vid}"
    return url


def try_apply_command(prompt: str):
    p = prompt.lower()
    m = re.search(r"rest\s*(timer)?\s*(to|=)?\s*(\d{2,3})", p)
    if m:
        st.session_state.rest_seconds = int(m.group(3))
        return f"Updated rest timer to {m.group(3)} seconds."
    m = re.search(r"days\s*(to|=)?\s*(\d)", p)
    if m:
        st.session_state.days_available = int(m.group(2))
        return f"Updated days/week to {m.group(2)}."
    m = re.search(r"set weight for (.+?) to (\d+(?:\.\d+)?)", p)
    if m:
        ex = m.group(1).strip().title()
        wt = float(m.group(2))
        st.session_state.weight_targets[ex] = wt
        return f"Saved target weight {wt} for {ex}."
    return None


def rest_widget():
    now = time.time()
    if st.session_state.rest_end > now:
        remaining = max(0, int(st.session_state.rest_end - now))
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            c1.markdown(f"### ⏱️ Rest: **{remaining}s**")
            if c2.button("✖ Dismiss", key="dismiss_rest"):
                st.session_state.rest_end = 0.0
                st.rerun()
            st.progress(1 - (remaining / max(st.session_state.rest_seconds, 1)))
            st.caption("This timer stays visible while you scroll this section.")
        time.sleep(1)
        st.rerun()
    elif st.session_state.rest_end != 0:
        st.success("✅ Rest complete. Start next set.")
        st.session_state.rest_end = 0.0


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

    st.session_state.days_available = st.slider("Days/week available", 2, 6, st.session_state.days_available)
    suggested = recommended_program(st.session_state.days_available)
    st.success(f"Suggested plan: {suggested}")
    chosen_program = st.selectbox("Program", list(PROGRAMS.keys()), index=list(PROGRAMS.keys()).index(suggested))

    view = st.radio("Screen", ["Dashboard", "Workout", "Program Builder", "History", "Exercise Library", "AI Coach"])

adapted = adapt_program(chosen_program)

if view == "Dashboard":
    c1, c2, c3 = st.columns(3)
    c1.metric("Equipment Selected", len(st.session_state.selected_equipment))
    c2.metric("Program Days", PROGRAMS[chosen_program]["days"])
    c3.metric("Logged Sets", 0 if history.empty else int(history.shape[0]))
    for day, items in adapted.items():
        with st.expander(day):
            for ex, rr, sets, swapped in items:
                st.write(f"- {ex}{' (auto-sub)' if swapped else ''} · {sets} x {rr}")

elif view == "Program Builder":
    st.subheader("Program Recommendations")
    st.write("- 3 days/week: full-body")
    st.write("- 4+ days/week: upper/lower")

elif view == "Workout":
    st.subheader(f"Workout · {chosen_program}")
    rest_widget()
    with st.expander("Rest timer controls", expanded=False):
        st.session_state.rest_seconds = st.select_slider("Rest duration", options=[45, 60, 75, 90, 120, 150, 180], value=st.session_state.rest_seconds)
        st.caption("Timer auto-starts after each logged set.")
    day = st.selectbox("Choose workout day", list(adapted.keys()))

    for idx, (ex, rr, sets, swapped) in enumerate(adapted[day], start=1):
        with st.container(border=True):
            st.markdown(f"### {idx}. {ex}")
            if swapped:
                st.warning("Auto-substituted based on equipment")
            st.caption(f"{sets} sets · {rr} reps")
            if ex in st.session_state.weight_targets:
                st.caption(f"Suggested weight: {st.session_state.weight_targets[ex]} lb")
            for s in range(1, sets + 1):
                k = f"{day}_{ex}_{s}"
                c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
                with c1:
                    wt = st.number_input(f"Wt S{s}", min_value=0.0, step=2.5, key=f"wt_{k}")
                with c2:
                    reps = st.number_input(f"Reps S{s}", min_value=0, step=1, key=f"rp_{k}")
                with c3:
                    rir = st.slider(f"RIR S{s}", 0, 4, 2, key=f"rir_{k}")
                with c4:
                    if st.button(f"Log Set {s}", key=f"log_{k}"):
                        save_set({"Date": datetime.date.today().strftime("%b %d, %Y"), "Program": chosen_program, "Routine": day,
                                  "Exercise": ex, "Set": s, "Weight_lbs": wt, "Reps": reps, "RIR": rir, "Volume": wt * reps})
                        st.session_state.rest_end = time.time() + st.session_state.rest_seconds
                        st.success(f"Logged {ex} set {s}. Rest started.")
            demo_url = EXERCISE_LIBRARY[ex]["url"]
            st.video(to_embed(demo_url))
            st.caption(f"If video fails, open directly: {demo_url}")

elif view == "History":
    st.subheader("History")
    st.dataframe(history.sort_index(ascending=False), use_container_width=True) if not history.empty else st.info("No history yet.")

elif view == "Exercise Library":
    st.subheader("Exercise Library")
    for ex, meta in EXERCISE_LIBRARY.items():
        with st.expander(ex):
            st.write(f"Required: {', '.join(meta['equipment']) if meta['equipment'] else 'None'}")
            st.write(f"Fallbacks: {', '.join(meta['fallback']) if meta['fallback'] else 'None'}")
            st.video(to_embed(meta["url"]))
            st.caption(f"Open source: {meta['url']}")

elif view == "AI Coach":
    st.subheader("AI Coach")
    api_key = st.sidebar.text_input("Gemini API Key", type="password").strip()
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    if prompt := st.chat_input("Ask your coach or update settings (e.g., 'set rest timer to 120')"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        local_reply = try_apply_command(prompt)
        if local_reply:
            reply = local_reply
        elif not api_key:
            reply = "Add Gemini API key in sidebar."
        else:
            try:
                equipment_text = ", ".join(st.session_state.selected_equipment)
                payload = {"contents": [{"parts": [{"text": f"You are a coach. User equipment: {equipment_text}. Program: {chosen_program}. Question: {prompt}"}]}]}
                response = requests.post(GEMINI_API_URL, json=payload, headers={"Content-Type": "application/json"}, params={"key": api_key}, timeout=20)
                if response.status_code == 429:
                    reply = (
                        "You hit Gemini free-tier quota (429). Try again later, reduce message frequency, "
                        "or create a new API key/project with available quota. I can still run local app commands here."
                    )
                elif response.status_code != 200:
                    reply = f"Connection rejected ({response.status_code}): {response.text[:200]}"
                else:
                    reply = response.json()["candidates"][0]["content"]["parts"][0]["text"]
            except requests.RequestException as exc:
                reply = f"Network/API error: {exc}"
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()
