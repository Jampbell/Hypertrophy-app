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
    "Trap Bar", "Safety Squat Bar", "Squat Rack", "Half Rack", "Power Rack", "Smith Machine", "Cable Machine", "MD-9010G Dual High Pulleys", "MD-9010G Low Pulley + Footplate",
    "MD-9010G Butterfly Press Arms", "MD-9010G Leg Developer", "MD-9010G Preacher Curl Pad",
    "Functional Trainer", "Lat Pulldown", "Leg Press", "Leg Extension", "Leg Curl", "Pec Deck", "Dip Bars",
    "Pull-Up Bar", "Power Tower", "Resistance Bands", "Suspension Trainer", "Air Rower", "Treadmill", "Bike", "Stair Climber"
]

PROFILE_PRESETS = {
    "Home Gym": ["Bench", "Dumbbells", "Kettlebells", "Smith Machine", "Safety Squat Bar", "EZ Curl Bar", "Air Rower", "Power Tower"],
    "Marcy MD-9010G Custom": ["Bench", "Dumbbells", "Kettlebells", "Smith Machine", "MD-9010G Dual High Pulleys", "MD-9010G Low Pulley + Footplate", "MD-9010G Butterfly Press Arms", "MD-9010G Leg Developer", "MD-9010G Preacher Curl Pad", "Safety Squat Bar", "EZ Curl Bar", "Air Rower", "Power Tower"],
    "Commercial Gym": EQUIPMENT_CATALOG,
    "Minimal": ["Dumbbells", "Bench", "Resistance Bands"],
}

EXERCISE_LIBRARY = {
    "Barbell Bench Press": {"equipment": ["Olympic Barbell", "Bench", "Squat Rack"], "fallback": ["Smith Machine Bench Press", "Dumbbell Bench Press"], "url": "https://www.youtube.com/watch?v=rT7DgCr-3pg"},
    "Smith Machine Bench Press": {"equipment": ["Smith Machine", "Bench"], "fallback": ["Dumbbell Bench Press", "Push-Up"], "url": "https://www.youtube.com/watch?v=9R4fQv1U8b0"},
    "Dumbbell Bench Press": {"equipment": ["Dumbbells", "Bench"], "fallback": ["Push-Up"], "url": "https://www.youtube.com/watch?v=VmB1G1K7v94"},
    "Push-Up": {"equipment": [], "fallback": [], "url": "https://www.youtube.com/watch?v=IODxDxX7oi4"},
    "Barbell Row": {"equipment": ["Olympic Barbell"], "fallback": ["Chest-Supported DB Row", "Cable Row"], "url": "https://www.youtube.com/watch?v=vT2GjY_Umpw"},
    "Chest-Supported DB Row": {"equipment": ["Dumbbells", "Bench"], "fallback": ["Cable Row"], "url": "https://www.youtube.com/watch?v=5PoEksoJNaw"},
    "Cable Row": {"equipment": ["Cable Machine"], "fallback": ["Chest-Supported DB Row"], "url": "https://www.youtube.com/watch?v=HJSVR_67OlM"},
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

    "Cable Crossover": {"equipment": ["MD-9010G Dual High Pulleys"], "fallback": ["Pec Deck Fly", "Dumbbell Bench Press"], "url": "https://www.youtube.com/watch?v=taI4XduLpTk"},
    "Low Cable Row (Footplate)": {"equipment": ["MD-9010G Low Pulley + Footplate"], "fallback": ["Cable Row", "Chest-Supported DB Row"], "url": "https://www.youtube.com/watch?v=GZbfZ033f74"},
    "Butterfly Press / Pec Fly": {"equipment": ["MD-9010G Butterfly Press Arms"], "fallback": ["Cable Crossover", "Dumbbell Bench Press"], "url": "https://www.youtube.com/watch?v=eozdVDA78K0"},
    "Leg Extension (MD-9010G)": {"equipment": ["MD-9010G Leg Developer"], "fallback": ["Goblet Squat"], "url": "https://www.youtube.com/watch?v=YyvSfVjQeL0"},
    "Preacher Curl (MD-9010G)": {"equipment": ["MD-9010G Preacher Curl Pad"], "fallback": ["EZ Bar Romanian Deadlift"], "url": "https://www.youtube.com/watch?v=fIWP-FRFNU0"},
}

PROGRAMS = {
    "Hypertrophy · 3-Day Full Body": {"goal": "Hypertrophy", "days": 3, "routine": {
        "Day 1": [("Barbell Bench Press", "8-12", 3), ("Barbell Row", "8-12", 3), ("Back Squat", "8-12", 3)],
        "Day 2": [("Overhead Press", "8-12", 3), ("Lat Pulldown", "10-15", 3), ("Romanian Deadlift", "8-12", 3)],
        "Day 3": [("Dumbbell Bench Press", "10-15", 3), ("Chest-Supported DB Row", "10-15", 3), ("Goblet Squat", "10-15", 3)],
    }},
    "Hypertrophy · 4-Day Upper/Lower": {"goal": "Hypertrophy", "days": 4, "routine": {
        "Day 1 Upper": [("Barbell Bench Press", "8-12", 3), ("Barbell Row", "8-12", 3), ("Dumbbell Shoulder Press", "10-15", 3)],
        "Day 2 Lower": [("Back Squat", "8-12", 3), ("Romanian Deadlift", "8-12", 3), ("Goblet Squat", "12-15", 2)],
        "Day 3 Upper": [("Dumbbell Bench Press", "10-15", 3), ("Lat Pulldown", "10-15", 3), ("Cable Row", "10-15", 3)],
        "Day 4 Lower": [("Safety Squat Bar Squat", "8-12", 3), ("Dumbbell Romanian Deadlift", "10-15", 3), ("Dumbbell Split Squat", "10-15", 2)],
    }},
    "Strength · 3-Day Full Body": {"goal": "Strength", "days": 3, "routine": {
        "Day 1": [("Barbell Bench Press", "4-6", 4), ("Barbell Row", "5-8", 4), ("Back Squat", "4-6", 4)],
        "Day 2": [("Overhead Press", "4-6", 4), ("Lat Pulldown", "6-8", 4), ("Romanian Deadlift", "5-8", 4)],
        "Day 3": [("Smith Machine Bench Press", "5-8", 4), ("Cable Row", "6-8", 4), ("Safety Squat Bar Squat", "5-8", 4)],
    }},
    "Strength · 4-Day Upper/Lower": {"goal": "Strength", "days": 4, "routine": {
        "Day 1 Upper": [("Barbell Bench Press", "4-6", 4), ("Barbell Row", "5-8", 4), ("Overhead Press", "4-6", 4)],
        "Day 2 Lower": [("Back Squat", "4-6", 4), ("Romanian Deadlift", "5-8", 4), ("Goblet Squat", "8-10", 3)],
        "Day 3 Upper": [("Smith Machine Bench Press", "5-8", 4), ("Lat Pulldown", "6-8", 4), ("Cable Row", "6-8", 4)],
        "Day 4 Lower": [("Safety Squat Bar Squat", "5-8", 4), ("Dumbbell Romanian Deadlift", "6-10", 4), ("Dumbbell Split Squat", "8-10", 3)],
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
    ss.setdefault("goal_mode", "Hypertrophy")
    ss.setdefault("exercise_notes", {})
    ss.setdefault("bw_log", [])
    ss.setdefault("nutrition_targets", {"calories": 2600, "protein": 180, "carbs": 280, "fat": 80})
    ss.setdefault("nutrition_intake", {"calories": 0, "protein": 0, "carbs": 0, "fat": 0})


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


def recommended_program(days, goal):
    if goal == "Strength":
        return "Strength · 4-Day Upper/Lower" if days >= 4 else "Strength · 3-Day Full Body"
    return "Hypertrophy · 4-Day Upper/Lower" if days >= 4 else "Hypertrophy · 3-Day Full Body"


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
        return f"https://www.youtube.com/embed/{vid}"
    if "youtu.be/" in url:
        vid = url.split("youtu.be/")[-1].split("?")[0]
        return f"https://www.youtube.com/embed/{vid}"
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
    m = re.search(r"goal\s*(to|=)?\s*(strength|hypertrophy)", p)
    if m:
        st.session_state.goal_mode = m.group(2).capitalize()
        return f"Updated goal mode to {st.session_state.goal_mode}."
    m = re.search(r"set weight for (.+?) to (\d+(?:\.\d+)?)", p)
    if m:
        ex = m.group(1).strip().title()
        wt = float(m.group(2))
        st.session_state.weight_targets[ex] = wt
        return f"Saved target weight {wt} for {ex}."
    return None


def add_bodyweight_entry(weight):
    today = datetime.date.today().strftime("%Y-%m-%d")
    st.session_state.bw_log.append({"Date": today, "Weight": float(weight)})


def lift_progress_by_exercise(df):
    if df.empty:
        return pd.DataFrame()
    grouped = df.sort_values("Date").groupby("Exercise", as_index=False).tail(1)
    return grouped[["Date", "Exercise", "Weight_lbs", "Reps", "Volume"]].sort_values("Exercise")


def render_rest_inline():
    now = time.time()
    if st.session_state.rest_end > now:
        remaining = max(0, int(st.session_state.rest_end - now))
        st.caption(f"⏱️ Rest: {remaining}s")
    elif st.session_state.rest_end != 0:
        st.caption("✅ Rest complete")
        st.session_state.rest_end = 0.0


init_state()
history = load_history()


st.markdown("""
<style>
.main .block-container {padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1100px;}
.app-hero {background: linear-gradient(135deg,#111827,#1f2937); padding: 16px 20px; border-radius: 14px; border:1px solid #334155; margin-bottom: 12px;}
.app-hero h2 {color:#f8fafc; margin:0; font-size:1.35rem}
.app-hero p {color:#cbd5e1; margin:.35rem 0 0 0;}
.kpi-grid {display:grid; grid-template-columns: repeat(3,minmax(0,1fr)); gap:10px; margin:8px 0 14px 0;}
.kpi-card {background:#111827; border:1px solid #334155; border-radius:12px; padding:10px 12px;}
.kpi-label {color:#94a3b8; font-size:.78rem;}
.kpi-value {color:#f8fafc; font-size:1.2rem; font-weight:700;}
.section-card {background:#0b1220; border:1px solid #243041; border-radius:14px; padding:10px 12px; margin-bottom:10px;}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='app-hero'><h2>🏋️ HyperCustom Fit</h2><p>Equipment-aware coaching with cleaner tracking, progression, and nutrition in one place.</p></div>", unsafe_allow_html=True)

with st.sidebar:
    st.header("Setup")
    preset = st.selectbox("Equipment preset", list(PROFILE_PRESETS.keys()))
    if st.button("Load preset", use_container_width=True):
        st.session_state.selected_equipment = PROFILE_PRESETS[preset].copy()
    st.session_state.selected_equipment = st.multiselect("Your equipment", EQUIPMENT_CATALOG, default=st.session_state.selected_equipment)

    st.session_state.goal_mode = st.selectbox("Training focus", ["Hypertrophy", "Strength"], index=0 if st.session_state.goal_mode == "Hypertrophy" else 1)
    st.session_state.days_available = st.slider("Days/week available", 2, 6, st.session_state.days_available)
    suggested = recommended_program(st.session_state.days_available, st.session_state.goal_mode)

    candidates = [k for k, v in PROGRAMS.items() if v["goal"] == st.session_state.goal_mode]
    st.success(f"Suggested plan: {suggested}")
    chosen_program = st.selectbox("Program", candidates, index=candidates.index(suggested))

    view = st.radio("Screen", ["Dashboard", "Workout", "Progress Tracker", "Nutrition", "Program Builder", "History", "Exercise Library", "AI Coach"])

adapted = adapt_program(chosen_program)

if view == "Dashboard":
    eq_count = len(st.session_state.selected_equipment)
    p_days = PROGRAMS[chosen_program]["days"]
    set_count = 0 if history.empty else int(history.shape[0])
    st.markdown(
        f"""<div class='kpi-grid'>
        <div class='kpi-card'><div class='kpi-label'>Equipment Selected</div><div class='kpi-value'>{eq_count}</div></div>
        <div class='kpi-card'><div class='kpi-label'>Program Days</div><div class='kpi-value'>{p_days}</div></div>
        <div class='kpi-card'><div class='kpi-label'>Logged Sets</div><div class='kpi-value'>{set_count}</div></div>
        </div>""",
        unsafe_allow_html=True,
    )
    for day, items in adapted.items():
        with st.expander(day):
            for ex, rr, sets, swapped in items:
                st.write(f"- {ex}{' (auto-sub)' if swapped else ''} · {sets} x {rr}")

elif view == "Progress Tracker":
    st.subheader("Progress Tracker")
    c1, c2 = st.columns(2)
    with c1:
        bw = st.number_input("Bodyweight (lb)", min_value=0.0, step=0.1)
        if st.button("Log bodyweight"):
            add_bodyweight_entry(bw)
            st.success("Bodyweight logged.")
    with c2:
        st.write("**Latest Lift Performance**")
        latest = lift_progress_by_exercise(history)
        if latest.empty:
            st.info("No lift history yet.")
        else:
            st.dataframe(latest, use_container_width=True)

    if st.session_state.bw_log:
        bw_df = pd.DataFrame(st.session_state.bw_log)
        st.line_chart(bw_df.set_index("Date")["Weight"])

elif view == "Nutrition":
    st.subheader("Nutrition Targets")
    t = st.session_state.nutrition_targets
    i = st.session_state.nutrition_intake

    c1, c2, c3, c4 = st.columns(4)
    t["calories"] = c1.number_input("Target calories", min_value=1000, max_value=6000, value=int(t["calories"]))
    t["protein"] = c2.number_input("Target protein (g)", min_value=50, max_value=400, value=int(t["protein"]))
    t["carbs"] = c3.number_input("Target carbs (g)", min_value=50, max_value=700, value=int(t["carbs"]))
    t["fat"] = c4.number_input("Target fat (g)", min_value=20, max_value=200, value=int(t["fat"]))

    st.markdown("#### Log intake")
    l1, l2, l3, l4 = st.columns(4)
    add_kcal = l1.number_input("Calories", min_value=0, step=50)
    add_p = l2.number_input("Protein", min_value=0, step=5)
    add_c = l3.number_input("Carbs", min_value=0, step=5)
    add_f = l4.number_input("Fat", min_value=0, step=5)
    if st.button("Add nutrition entry"):
        i["calories"] += int(add_kcal)
        i["protein"] += int(add_p)
        i["carbs"] += int(add_c)
        i["fat"] += int(add_f)
        st.success("Nutrition entry added.")

    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("Calories", f"{i['calories']}/{t['calories']}")
    mc2.metric("Protein", f"{i['protein']}/{t['protein']} g")
    mc3.metric("Carbs", f"{i['carbs']}/{t['carbs']} g")
    mc4.metric("Fat", f"{i['fat']}/{t['fat']} g")

elif view == "Program Builder":
    st.subheader("Program Recommendations")
    st.write("- Hypertrophy: higher reps, moderate loads, more volume")
    st.write("- Strength: lower reps, higher loads, longer rest")
    st.write("- 3 days/week: full-body")
    st.write("- 4+ days/week: upper/lower")

elif view == "Workout":
    st.subheader(f"Workout · {chosen_program}")
    with st.expander("Rest timer controls", expanded=False):
        st.session_state.rest_seconds = st.select_slider("Rest duration", options=[45, 60, 75, 90, 120, 150, 180], value=st.session_state.rest_seconds)
        st.caption("Timer auto-starts after each logged set.")

    day = st.selectbox("Choose workout day", list(adapted.keys()))

    for idx, (ex, rr, sets, swapped) in enumerate(adapted[day], start=1):
        with st.container(border=False):
            st.markdown("<div class='section-card'>", unsafe_allow_html=True)
            st.markdown(f"### {idx}. {ex}")
            if swapped:
                st.warning("Auto-substituted based on equipment")
            st.caption(f"{sets} sets · {rr} reps")
            n1, n2 = st.columns(2)
            if n1.button("History", key=f"hx_{day}_{ex}"):
                ex_hist = history[history["Exercise"] == ex] if not history.empty else pd.DataFrame()
                st.dataframe(ex_hist.tail(8), use_container_width=True) if not ex_hist.empty else st.info("No history for this exercise yet.")
            current_note = st.session_state.exercise_notes.get(ex, "")
            st.session_state.exercise_notes[ex] = n2.text_input("Notes", value=current_note, key=f"note_{day}_{ex}")
            if ex in st.session_state.weight_targets:
                st.caption(f"Suggested weight: {st.session_state.weight_targets[ex]} lb")

            for s in range(1, sets + 1):
                k = f"{day}_{ex}_{s}"
                c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 1])
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
                with c5:
                    render_rest_inline()

            demo_url = EXERCISE_LIBRARY[ex]["url"]
            st.video(to_embed(demo_url))
            st.caption(f"If video fails, open directly: {demo_url}")
            st.markdown("</div>", unsafe_allow_html=True)

elif view == "History":
    st.subheader("History")
    if history.empty:
        st.info("No history yet.")
    else:
        edit_df = history.copy().reset_index(drop=True)
        edit_df.insert(0, "Delete", False)
        edited = st.data_editor(edit_df, use_container_width=True, num_rows="fixed", key="history_editor")
        c1, c2 = st.columns(2)
        if c1.button("Save history edits", type="primary"):
            cleaned = edited.drop(columns=["Delete"], errors="ignore")
            cleaned.to_csv(DB_FILE, index=False)
            st.success("History updates saved.")
            st.rerun()
        if c2.button("Delete selected rows"):
            remaining = edited[~edited["Delete"]].drop(columns=["Delete"], errors="ignore")
            remaining.to_csv(DB_FILE, index=False)
            st.success("Selected rows deleted.")
            st.rerun()

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
                payload = {"contents": [{"parts": [{"text": f"You are a coach. Goal: {st.session_state.goal_mode}. User equipment: {equipment_text}. Program: {chosen_program}. Question: {prompt}"}]}]}
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
