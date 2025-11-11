import base64
import hashlib
import io
import json
import os
import random
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Dict, List

import pandas as pd
import streamlit as st
from fpdf import FPDF
from PIL import Image, ImageDraw, ImageFont

import db
import notifications
from security import (
    create_password_record,
    decrypt_text,
    derive_encryption_key,
    encrypt_text,
    verify_password,
)

APP_NAME = "Heartline Care Companion"
SCHEDULES = ["Day", "Night", "Mixed"]
PASTEL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=Playfair+Display:wght@600&display=swap');
:root {
  --rose-beige: #F6E7EB;
  --peachy-sakura: #FAD4DC;
  --matcha-sage: #A9C3A8;
  --warm-charcoal: #3A3A3A;
  --soft-cream: #FDFBF7;
}
.stApp {
  background: linear-gradient(180deg, #F6E7EB 0%, #FDFBF7 50%, #FFFFFF 100%);
  color: var(--warm-charcoal);
  font-family: 'DM Sans', 'Inter', sans-serif;
}
.heart-hero {
  border-radius: 28px;
  padding: 32px;
  background: linear-gradient(120deg, rgba(250,212,220,0.75), rgba(169,195,168,0.35));
  box-shadow: 0 25px 60px rgb(250 212 220 / 28%);
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  gap: 18px;
}
.heart-hero h1 {
  font-family: 'Playfair Display', serif;
  color: var(--warm-charcoal);
  margin-bottom: 6px;
}
.heart-hero p {
  margin: 0;
  font-size: 1.02rem;
  color: #4f414d;
}
.heart-hero .hero-emoji {
  font-size: 2.5rem;
  background: var(--soft-cream);
  border-radius: 20px;
  padding: 12px 16px;
  box-shadow: 0 12px 25px rgb(0 0 0 / 8%);
}
.heart-card {
  background: var(--soft-cream);
  border-radius: 20px;
  padding: 20px;
  box-shadow: 0 15px 35px rgb(246 231 235 / 55%);
  border: 1px solid rgba(250,212,220,0.55);
  margin-bottom: 16px;
}
.heart-illustration {
  width: 100%;
  border-radius: 24px;
  padding: 18px;
  margin-top: -8px;
  margin-bottom: 18px;
  border: 1px solid rgba(58,58,58,0.08);
  box-shadow: inset 0 0 30px rgb(255 255 255 / 60%);
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.95rem;
  color: #4f414d;
}
.illustration-home { background: linear-gradient(120deg, rgba(250,212,220,0.45), rgba(246,231,235,0.6)); }
.illustration-health { background: linear-gradient(120deg, rgba(246,231,235,0.75), rgba(253,251,247,0.7)); }
.illustration-shift { background: linear-gradient(120deg, rgba(169,195,168,0.45), rgba(250,212,220,0.45)); }
</style>
"""

AUDIO_LIBRARY = {
    "Lo-fi Bloom": "https://cdn.pixabay.com/download/audio/2022/03/15/audio_0d3c3c4ba0.mp3?filename=lofi-study-112191.mp3",
    "Soft Chimes": "https://cdn.pixabay.com/download/audio/2021/12/23/audio_58e8cd5e0f.mp3?filename=calm-meditation-110517.mp3",
    "Night Shift Waves": "https://cdn.pixabay.com/download/audio/2022/11/02/audio_29a25de403.mp3?filename=soft-ambient-124841.mp3",
}

TASK_SIZES = ["Tiny", "Medium", "Big"]
ENERGY_TASK_LIBRARY = {
    "low": [
        "Sip warm water with lemon",
        "Put away one item",
        "Send a 'thinking of you' emoji",
    ],
    "medium": [
        "Reply to one email",
        "Prep a simple meal",
        "Walk outside for 10 minutes",
    ],
    "high": [
        "Deep clean a surface",
        "Study sprint (45 min)",
        "Move your body with music",
    ],
}
SELF_CARE_PROMPTS = [
    "Have you sipped water yet? 🍵",
    "Three slow breaths: in 4… hold… out…",
    "Shoulders down, jaw unclenched, gentle stretch?",
    "Snack time? Protein + something cozy.",
]
EMOTION_SUPPORT = {
    "Scary": "Break it into micro steps and phone a friend if you can.",
    "Overwhelming": "Body double or set a 5-minute starter timer.",
    "Confusing": "Write the next question you need answered first.",
    "Boring": "Pair it with a sweet playlist or a treat afterwards.",
}
AFFIRMATIONS = [
    "i’m proud of the tiny progress you made today 💗",
    "rest counts too. thanks for being gentle with yourself.",
    "future you is smiling because you cared today.",
]


def inject_pastel_theme() -> None:
    st.markdown(PASTEL_CSS, unsafe_allow_html=True)


def hero_section(title: str, subtitle: str, emoji: str) -> None:
    st.markdown(
        f"""
        <div class="heart-hero">
            <div class="hero-emoji">{emoji}</div>
            <div>
                <h1>{title}</h1>
                <p>{subtitle}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def pastel_illustration(view_key: str) -> None:
    classes = {
        "home": "illustration-home",
        "health": "illustration-health",
        "shift": "illustration-shift",
    }
    captions = {
        "home": "Mood clouds shift — Heartline follows.",
        "health": "Admin tasks + compassion can coexist.",
        "shift": "Night lights, day naps, all valid rhythms.",
    }
    css_class = classes.get(view_key, "illustration-home")
    caption = captions.get(view_key, "Soft planner energy.")
    st.markdown(
        f"""
        <div class="heart-illustration {css_class}">
            <span>{caption}</span>
            <div class="illustration-dots"><span></span><span></span><span></span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


@contextmanager
def heart_card_container():
    st.markdown('<div class="heart-card">', unsafe_allow_html=True)
    yield
    st.markdown("</div>", unsafe_allow_html=True)


def routine_prescription(mood: int, energy: int, schedule: str) -> Dict[str, List[str]]:
    tone = "slo-mo" if energy <= 3 else "steady" if energy <= 7 else "glow"
    base = {
        "body": ["Sip warm lemon water", "Stretch shoulders + jaw", "Take meds / vitamins"],
        "mind": ["Name one feeling (no fixing needed)", "Note 3 sensations in your body", "Play 5-min calming audio"],
        "logistics": ["Scan calendar for next 3 days", "Flag one admin task to delegate", "Check refill status"],
    }
    if tone == "slo-mo":
        base["body"] = ["Eat a soft meal", "Lay down with legs up", "Choose comfy clothes"]
        base["logistics"] = ["Mark day as Rest-ish", "Send quick status to team", "Move non-urgent tasks"]
    elif tone == "glow":
        base["body"].append("Walk outside for 10 min")
        base["logistics"].extend(["Plan one proactive appointment", "Prep call questions"])
    by_schedule = {
        "Day": "Anchor lunch + sunlight between 10a-2p",
        "Night": "Dim lights early, hydrate before shift",
        "Mixed": "Protect 4-hr core sleep block",
    }
    base["logistics"].insert(0, by_schedule.get(schedule, "Honor the rhythm you have"))
    return base


def appointment_reminders(appointments: List[Dict]) -> List[str]:
    templates = {"Dental Cleaning": 180, "Therapy": 7, "Annual Physical": 365}
    reminders = []
    now = datetime.now().date()
    for label, cadence in templates.items():
        last = max(
            [appt["date"].date() for appt in appointments if appt["category"] == label],
            default=None,
        )
        if not last:
            reminders.append(f"You haven't logged a {label.lower()} yet — want to pick a date?")
        else:
            due = last + timedelta(days=cadence)
            if due <= now:
                reminders.append(f"{label} is ready to be scheduled again. You're allowed to take your time.")
            else:
                reminders.append(f"Next {label.lower()} feels good around {due.strftime('%b %d')}. Soft nudge only ✨")
    return reminders


def generate_script(data: Dict) -> str:
    greeting = random.choice(["Hi there!", "Hello, thanks for taking my call.", "Good day!"])
    insurance_line = f"My insurance is {data['insurance']}" if data.get("insurance") else "I would like to confirm what insurance you accept."
    energy_note = "I'm feeling a bit anxious about calling, so thank you for patience." if data.get("call_support") else ""
    script = f"""{greeting} My name is {data['name'] or '_____'} and I'd like to schedule {data['need']}.
{insurance_line}
My availability is {data['availability'] or 'flexible'}.
Could you please let me know what information you need from me?
{data['notes']}
{energy_note}
Thank you so much for your help today!"""
    return script.strip()


def shift_plan(schedule: str, energy: int) -> Dict[str, List[str]]:
    plans = {
        "Day": {
            "sleep": ["Aim for 7 hrs between 11p-7a", "Light stretch before bed"],
            "meals": ["Protein breakfast", "12p daylight lunch", "6p grounded dinner"],
            "movement": ["Morning sunlight lap", "Afternoon posture reset"],
        },
        "Night": {
            "sleep": ["Core sleep 8a-1p", "1 hr wind-down pre-shift"],
            "meals": ["Fuel-up meal 5p", "Warm bowl at 1a", "Hydrate every break"],
            "movement": ["Pre-shift mobility", "Gentle decompression after"],
        },
        "Mixed": {
            "sleep": ["Protect a 4-hr anchor block", "20-min nap before late shift"],
            "meals": ["Set alarms for meals", "Carry stable snacks", "Magnesium-rich dinner"],
            "movement": ["Stack micro stretches", "2-min breath after calls"],
        },
    }
    focus = "Call it a bare-minimum day" if energy <= 3 else "Steady + kind pace" if energy <= 7 else "Try one energizing habit"
    plans[schedule]["focus"] = [focus]
    return plans[schedule]


def compassion_prompt(mood: int) -> str:
    if mood <= 3:
        return "Today is heavy. Permission to cancel and cocoon."
    return random.choice(
        [
            "It's okay to pause. Rest is part of the care plan.",
            "One small step still counts as momentum.",
            "You're doing brave admin work for Future You.",
            "Slow breaths, soft shoulders, no apologies needed.",
        ]
    )


def render_home():
    ensure_data_loaded()
    hero_section(
        "Soft pastel check-in",
        "Log energy, mood, and rhythms with zero judgement — Heartline adapts gently.",
        "🌸",
    )
    pastel_illustration("home")
    st.markdown("### Heartline")
    st.write("the soft productivity space for overwhelmed smart girls ☁️💗")
    st.caption("you don’t need to grind to grow. we do tiny steps, gentle wins, soft progress.")
    cta1, cta2 = st.columns(2)
    if cta1.button("start your soft era ✨"):
        st.toast("We'll meet you inside your dashboard 💗")
    if cta2.button("peek inside the cloud ☁️"):
        st.toast("Scroll to explore the pastel features waiting for you.")
    st.divider()

    if needs_no_shame_screen():
        st.success("hi angel 🤍 life gets loud sometimes. i'm just glad you're here. pick what feels doable today.")
        tiny, regular, challenge = st.columns(3)
        if tiny.button("tiny step", key="reentry_tiny"):
            mark_reentry_acknowledged()
            st.toast("Tiny is perfect. Maybe brush teeth or sip water.")
        if regular.button("regular step", key="reentry_regular"):
            mark_reentry_acknowledged()
            st.toast("Steady step logged. Maybe one admin thing or short walk.")
        if challenge.button("challenge step", key="reentry_challenge"):
            mark_reentry_acknowledged()
            st.toast("Spicy! Pick one bold move and we'll cheer for you.")

    left, right = st.columns([1.25, 0.95])

    with left:
        st.subheader("hi angel — how's your energy today?")
        with st.form("check_in"):
            mood = st.slider("Heart vibe", 0, 10, st.session_state.latest_energy)
            energy = st.slider("Body battery", 0, 10, st.session_state.latest_energy)
            schedule = st.select_slider("Current rhythm", options=SCHEDULES, value=st.session_state.selected_schedule)
            highlight = st.text_area(
                "Tiny note for Future You",
                placeholder="E.g. 'Neck sore after double' or 'Win: queued dentist call'",
                height=90,
            )
            submitted = st.form_submit_button("Save check-in")
        if submitted:
            entry = {
                "timestamp": datetime.now(),
                "mood": mood,
                "energy": energy,
                "schedule": schedule,
                "note": highlight,
            }
            store_check_in(entry)
            st.success("Logged with care.")

        current_energy = st.session_state.latest_energy
        routine = routine_prescription(mood if submitted else current_energy, current_energy, st.session_state.selected_schedule)
        st.markdown("#### Today’s gentle recipe")
        cols = st.columns(3)
        for idx, cat in enumerate(["body", "mind", "logistics"]):
            with cols[idx]:
                st.markdown(f"**{cat.title()}**")
                for item in routine[cat]:
                    st.write(f"• {item}")
        st.markdown("#### Energy-based suggestions")
        for idea in energy_task_suggestions(current_energy):
            st.write(f"• {idea}")
        if current_energy <= 3:
            st.warning("take it easy today 🍵 • tidy one small thing • reply to one message • stretch with me for 3 minutes?")
        with st.expander("Why is this task heavy?", expanded=False):
            feeling = st.radio(
                "Name the vibe (no fixing needed)",
                list(EMOTION_SUPPORT.keys()),
                horizontal=True,
                key="feeling_radio",
            )
            st.info(emotion_support_message(feeling))

    with right:
        st.subheader("Today at a glance")
        latest = st.session_state.check_ins[-1] if st.session_state.check_ins else None
        summary_cols = st.columns(2)
        summary_cols[0].metric("Mood", (latest or {"mood": st.session_state.latest_energy})["mood"])
        summary_cols[1].metric("Energy", (latest or {"energy": st.session_state.latest_energy})["energy"])
        st.caption(f"Rhythm: {st.session_state.selected_schedule}")

        st.markdown("#### Today, just three")
        trio = today_three_tasks()
        archive_count = max(0, len(st.session_state.tasks) - 3)
        for task in trio:
            label = f"{task['size']} • {task['title']}"
            placeholder = task["id"].startswith("placeholder")
            checked = st.checkbox(
                label,
                value=task.get("done", False),
                key=f"three_{task['id']}",
                disabled=placeholder,
            )
            if not placeholder:
                toggle_task_completion(task["id"], checked)
                if checked:
                    st.balloons()
        if archive_count:
            st.caption(f"{archive_count} tasks are chilling in the cloud archive until you’re ready.")
        with st.form("task_form"):
            new_task = st.text_input("Add a task to the cloud", placeholder="email Dr. Kim")
            size = st.selectbox("Size", TASK_SIZES, index=1)
            add_task = st.form_submit_button("Save task")
        if add_task:
            if new_task.strip():
                add_personal_task(new_task.strip(), size)
                st.success("Task tucked into the cloud.")
            else:
                st.error("Give the task a tiny name first.")

        st.markdown("#### Weekly digest")
        digest_text = weekly_digest_summary(st.session_state.check_ins, st.session_state.symptoms)
        st.write(digest_text)
        digest_pdf = create_digest_pdf(digest_text)
        digest_png = create_digest_png(digest_text)
        st.download_button("Download digest PDF", data=digest_pdf, file_name="heartline-digest.pdf", mime="application/pdf")
        st.download_button("Download digest PNG", data=digest_png, file_name="heartline-digest.png", mime="image/png")
        with st.form("digest_delivery"):
            digest_email = st.text_input("Email digest to", placeholder="heartline.notes@gmail.com")
            send_digest = st.form_submit_button("Send digest (staged)")
        if send_digest:
            if digest_email:
                st.success(f"We'll email {digest_email}. Attach the PDF/PNG above once your provider is wired up.")
            else:
                st.error("Add an email first.")
        if st.session_state.check_ins:
            with st.expander("Recent emotional receipts", expanded=False):
                for entry in st.session_state.check_ins[-3:][::-1]:
                    st.markdown(
                        f"{entry['timestamp'].strftime('%b %d %I:%M %p')} — mood {entry['mood']}/10, energy {entry['energy']}/10\\n\\n> {entry['note'] or 'Just vibes ✨'}"
                    )
        st.markdown("#### Soft self-care prompt")
        if st.button("Send me a gentle nudge", key="selfcare_btn"):
            st.success(random_self_care_prompt())
        elif st.session_state.self_care_prompt:
            st.success(st.session_state.self_care_prompt)
        st.markdown("#### Affirmation")
        if any(task.get("done") for task in st.session_state.tasks):
            reset_affirmation()
        st.info(current_affirmation())

    st.subheader("Reflection journal")
    with st.form("reflection_form"):
        reflection = st.text_area("what’s on your heart today?", height=120)
        save_reflection = st.form_submit_button("Save reflection")
    if save_reflection and reflection.strip():
        closing = "thank you for trying. you are growing beautifully."
        store_reflection(f"{reflection.strip()}\\n\\n_{closing}_")
        st.success("Reflection saved with a soft affirmation.")
    if st.session_state.reflections:
        with st.expander("Recent reflections", expanded=False):
            for entry in st.session_state.reflections[-3:][::-1]:
                st.markdown(f"**{entry['timestamp'].strftime('%b %d %I:%M %p')}**\\n\\n{entry['text']}")

    st.info(compassion_prompt(st.session_state.latest_energy))


def render_health_planner():
    ensure_data_loaded()
    hero_section(
        "Pastel health planner",
        "Appointments, scripts, and symptom notes live in one calm, blush-toned hub.",
        "📒",
    )
    pastel_illustration("health")
    st.subheader("Gentle appointment hub")
    with st.form("appointment_form"):
        title = st.text_input("Appointment title", placeholder="Dentist, therapy, labs...")
        category = st.selectbox("Category", ["Dental Cleaning", "Therapy", "Annual Physical", "Other"], index=1)
        provider = st.text_input("Provider or office")
        date = st.date_input("Appointment date", value=datetime.now())
        notes = st.text_area("Notes / prep items")
        submitted = st.form_submit_button("Add to planner")
    if submitted and title:
        add_appointment(
            {
                "title": title,
                "category": category,
                "provider": provider,
                "date": datetime.combine(date, datetime.min.time()),
                "notes": notes,
            }
        )
        st.success("Added. Future you sends a hug.")
    if st.session_state.appointments:
        st.markdown("#### Upcoming")
        df = pd.DataFrame(
            [
                {
                    "Title": appt["title"],
                    "Category": appt["category"],
                    "Provider": appt["provider"],
                    "Date": appt["date"].strftime("%b %d, %Y"),
                    "Prep": appt["notes"],
                }
                for appt in sorted(st.session_state.appointments, key=lambda a: a["date"])
            ]
        )
        with heart_card_container():
            st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption("No penalties if something moves. This planner flexes with you.")

    st.divider()
    st.subheader("Call script whisperer")
    with st.form("script_form"):
        name = st.text_input("Your name")
        need = st.text_input("What are you calling about?", placeholder="new patient appointment for pelvic pain...")
        insurance = st.text_input("Insurance details (optional)")
        availability = st.text_input("Preferred times")
        notes = st.text_area("Anything else to mention?", placeholder="I have referrals, I need translator, etc.")
        call_support = st.checkbox("Add anxiety-friendly reassurance line")
        generated = st.form_submit_button("Generate script")
    if generated:
        st.session_state.generated_script = generate_script(
            {
                "name": name,
                "need": need,
                "insurance": insurance,
                "availability": availability,
                "notes": notes,
                "call_support": call_support,
            }
        )
    if st.session_state.generated_script:
        st.text_area("Soft script", st.session_state.generated_script, height=200)
        st.caption("Copy, paste, or tweak. Take breaths between lines.")

    st.divider()
    st.subheader("Symptom & note tracker")
    with st.form("symptom_form"):
        symptom = st.text_input("Symptom / event")
        severity = st.slider("Intensity", 0, 10, 5)
        detail = st.text_area("Notes for your care team")
        symptom_date = st.date_input("Date", value=datetime.now())
        added = st.form_submit_button("Log entry")
    if added and symptom:
        add_symptom(
            {
                "symptom": symptom,
                "severity": severity,
                "notes": detail,
                "date": datetime.combine(symptom_date, datetime.min.time()),
            }
        )
        st.success("Saved. Proud of you for tracking the messy stuff.")
    if st.session_state.symptoms:
        symp_df = pd.DataFrame(
            [
                {
                    "Date": entry["date"].strftime("%b %d"),
                    "Symptom": entry["symptom"],
                    "Severity": entry["severity"],
                    "Notes": entry["notes"],
                }
                for entry in sorted(st.session_state.symptoms, key=lambda e: e["date"], reverse=True)
            ]
        )
        with heart_card_container():
            st.dataframe(symp_df, use_container_width=True, hide_index=True)
        pdf_bytes = create_symptom_pdf(st.session_state.symptoms)
        st.download_button("Download cute PDF for doctor", data=pdf_bytes, file_name="heartline-notes.pdf", mime="application/pdf")

    st.divider()
    st.markdown("#### Gentle reminders")
    for reminder in appointment_reminders(st.session_state.appointments):
        st.write(f"💌 {reminder}")


def render_shift_support():
    ensure_data_loaded()
    hero_section(
        "Shift rhythm cocoon",
        "Night owls, day shifters, and float teams all get a pastel plan that forgives everything.",
        "🌙",
    )
    pastel_illustration("shift")
    schedule = st.select_slider("Current rhythm", options=SCHEDULES, value=st.session_state.selected_schedule)
    energy = st.slider("How charged do you feel?", 0, 10, st.session_state.latest_energy)
    st.session_state.selected_schedule = schedule
    st.session_state.latest_energy = energy
    plan = shift_plan(schedule, energy)
    cols = st.columns(3)
    for idx, key in enumerate(["sleep", "meals", "movement"]):
        with cols[idx]:
            st.markdown(f"**{key.title()}**")
            for item in plan[key]:
                st.write(f"• {item}")
    st.success(plan["focus"][0])
    st.markdown("### Hydration + alarms")
    st.write("Set gentle chimes every 90 minutes. Avoid harsh alarms; think lo-fi windchimes.")
    st.write("Pre-fill two bottles before the shift starts. Future You will be thrilled.")
    st.markdown("### Tiny doable wins")
    micro_wins = [
        "Swap one caffeinated drink for water",
        "Send a 'made it home' text to your support person",
        "Stretch wrists between charts",
        "Put on compression socks",
    ]
    if energy <= 3:
        micro_wins = ["Brush teeth + face", "Eat a comfort snack", "Queue cozy playlist"]
    for win in micro_wins:
        st.write(f"• {win}")
    st.info(compassion_prompt(energy))


if __name__ == "__main__":
    main()


def render_notification_settings() -> None:
    st.subheader("Reminder dispatch")
    st.caption("Register Expo push tokens or send yourself a soft email ping right from Heartline.")
    form_key = "device_form_sidebar" if st.sidebar else "device_form_main"
    with st.form(form_key):
        label = st.text_input("Device label", placeholder="My iPhone")
        token = st.text_input("Expo push token", placeholder="ExponentPushToken[xxxxxxx]")
        save_token = st.form_submit_button("Save device")
    if save_token and token:
        add_device(label, token)
        st.success("Device saved.")
    if st.session_state.devices:
        st.markdown("##### Registered devices")
        st.table({"Label": [d["label"] for d in st.session_state.devices], "Token": [d["token"] for d in st.session_state.devices]})

    st.markdown("##### Send gentle reminder")
    with st.form("send_notification"):
        channel = st.selectbox("Channel", ["In-app toast", "Expo push", "Email"])
        title = st.text_input("Title", value="Heartline reminder")
        body = st.text_area("Body", value="Hydrate + take three soft breaths.")
        device_labels = [f"{d['label']} ({d['token'][:8]}...)" for d in st.session_state.devices]
        target_token = None
        if channel == "Expo push" and device_labels:
            selected = st.selectbox("Device", device_labels)
            target_token = st.session_state.devices[device_labels.index(selected)]["token"]
        digest_email = st.text_input("Email (for email/backup)", placeholder="heartline.reminders@gmail.com")
        send_now = st.form_submit_button("Send now")
    if send_now:
        try:
            if channel == "In-app toast":
                st.toast(body)
            elif channel == "Expo push":
                if not target_token:
                    raise ValueError("Add an Expo token first.")
                notifications.send_expo_notification(target_token, title, body)
                st.success("Expo push dispatched.")
            else:
                notifications.send_email_notification(digest_email, title, body)
                st.success("Email sent.")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Notification failed: {exc}")


def render_calendar_tools() -> None:
    st.subheader("Calendar & automation lab")
    st.caption("Export appointments as ICS or prep a Google sync request.")
    if st.session_state.appointments:
        ics_data = create_ics_calendar(st.session_state.appointments)
        st.download_button("Download calendar (.ics)", data=ics_data, file_name="heartline-appointments.ics", mime="text/calendar")
    else:
        st.info("Add an appointment to unlock calendar exports.")
    with st.form("google_sync_form"):
        google_email = st.text_input("Google Workspace / Gmail", placeholder="heartlineplanner@gmail.com")
        scopes = st.multiselect(
            "Requested permissions",
            ["Calendar events", "Reminders read/write", "Contacts (support circle)"],
            default=["Calendar events", "Reminders read/write"],
        )
        prep_sync = st.form_submit_button("Prep Google sync")
    if prep_sync:
        if google_email:
            st.success(
                f"Great! We'll request offline access for {google_email}. Add these scopes when you create OAuth credentials: {', '.join(scopes)}."
            )
        else:
            st.error("Add an email so we know which account to prep.")


def render_team_support_panel() -> None:
    st.subheader("Support circle sharing")
    st.caption("Loop in a trusted person or mentor without oversharing everything.")
    st.download_button(
        "Download shareable care packet (JSON)",
        data=build_share_packet(),
        file_name="heartline-share.json",
        mime="application/json",
    )
    with st.form("support_invite"):
        support_email = st.text_input("Support person email", placeholder="heartlinebuddy@gmail.com")
        scope = st.selectbox("What can they see?", ["Digest only", "Appointments + digest", "Everything in share packet"])
        invite = st.form_submit_button("Send support invite (staged)")
    if invite:
        if support_email:
            st.info(f"Invite drafted for {support_email}. Once email delivery is wired up they'll receive {scope.lower()} updates.")
        else:
            st.error("Add an email before sending.")


def render_audio_studio() -> None:
    st.markdown("### Ambient cue studio")
    track = st.selectbox("Choose a vibe", list(AUDIO_LIBRARY.keys()))
    st.audio(AUDIO_LIBRARY[track])
    st.caption("Tip: download the MP3 for offline shifts, then set it as a gentle alarm.")


def render_sidebar_tools() -> None:
    st.sidebar.subheader("Companion toolbox")
    with st.sidebar.expander("Heartline vibe", expanded=False):
        st.markdown("**productivity that doesn’t hurt**")
        st.write("no guilt. no streak shame. no “do more.” just gentle structure, supportive routines, and tiny steps that feel doable.")
        st.markdown("**some days we’re ✨ on ✨ and some days… no.**")
        st.write("heartline adjusts tasks to your energy. low-energy mode suggests gentle, cozy wins so you still feel proud of yourself.")
        st.markdown("**you’re not “lazy.” tasks can just feel heavy.**")
        st.write("mark why something feels hard — scary, overwhelming, unclear — heartline helps you break it down with soft support.")
        st.markdown("**clarity brings calm**")
        st.write("we pick one big, one medium, one tiny — enough to grow without drowning.")
    with st.sidebar.expander("Reminder dispatch"):
        render_notification_settings()
    with st.sidebar.expander("Calendar & automations"):
        render_calendar_tools()
    with st.sidebar.expander("Support circle"):
        render_team_support_panel()
    with st.sidebar.expander("Ambient cue studio"):
        render_audio_studio()


def auth_panel() -> bool:
    st.sidebar.title(APP_NAME)
    st.sidebar.caption("Logistics + emotional care, now with encrypted storage + notifications.")
    auto_login_from_token()
    user = st.session_state.user
    if user:
        st.sidebar.success(f"Signed in as {user['email']}")
        if st.sidebar.button("Sign out"):
            clear_persistent_session()
            reset_user_state()
            st.experimental_rerun()
        return True

    st.sidebar.markdown("### Sign in")
    with st.sidebar.form("login_form"):
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        remember_me = st.checkbox("Keep me signed in for 7 days", value=True)
        submitted = st.form_submit_button("Sign in")
    if submitted:
        email_normalized = email.strip().lower()
        record = db.get_user_by_email(email_normalized)
        if record and verify_password(password, record["password_hash"], record["password_salt"]):
            key = derive_encryption_key(password, record["encryption_salt"])
            st.session_state.user = {"id": record["id"], "email": record["email"], "name": record["full_name"]}
            st.session_state.crypto_key = key
            st.session_state.data_loaded = False
            if remember_me:
                clear_persistent_session()
                remember_user_session(record["id"], key)
            else:
                clear_persistent_session()
            load_user_data()
            st.experimental_rerun()
        else:
            st.sidebar.error("Invalid credentials.")

    st.sidebar.markdown("### Create account")
    with st.sidebar.form("register_form"):
        name = st.text_input("Full name", key="register_name")
        email_reg = st.text_input("Email", key="register_email")
        password_reg = st.text_input("Password", type="password", key="register_pass")
        confirm = st.text_input("Confirm password", type="password", key="register_confirm")
        remember_new = st.checkbox("Keep me signed in here", value=True)
        create = st.form_submit_button("Create account")
    if create:
        errors = []
        email_norm = email_reg.strip().lower()
        if not email_norm:
            errors.append("Email is required.")
        if password_reg != confirm:
            errors.append("Passwords do not match.")
        if len(password_reg) < 8:
            errors.append("Password must be at least 8 characters.")
        if db.get_user_by_email(email_norm):
            errors.append("Account already exists.")
        if errors:
            for err in errors:
                st.sidebar.error(err)
        else:
            password_hash, password_salt = create_password_record(password_reg)
            encryption_salt = base64.b64encode(os.urandom(16)).decode("utf-8")
            user_id = db.create_user(email_norm, name, password_hash, password_salt, encryption_salt)
            key = derive_encryption_key(password_reg, encryption_salt)
            st.session_state.user = {"id": user_id, "email": email_norm, "name": name}
            st.session_state.crypto_key = key
            st.session_state.data_loaded = False
            clear_persistent_session()
            if remember_new:
                remember_user_session(user_id, key)
            load_user_data()
            st.experimental_rerun()
    return False


def main():
    st.set_page_config(page_title=APP_NAME, page_icon="💗", layout="wide")
    inject_pastel_theme()
    init_state()
    is_authed = auth_panel()
    if not is_authed:
        st.header("Welcome to Heartline Care Companion")
        st.write("Create an account or sign in from the sidebar to unlock your encrypted planner.")
        st.stop()

    view = st.sidebar.radio("Navigate", ["Home", "Health Planner", "Shift Support"], index=0)
    if view == "Home":
        render_home()
    elif view == "Health Planner":
        render_health_planner()
    else:
        render_shift_support()

    st.sidebar.divider()
    st.sidebar.markdown("Need a break? Close the app guilt-free. We'll keep your encrypted notes safe.")
    st.sidebar.divider()
    render_sidebar_tools()


def init_state() -> None:
    db.init_db()
    defaults = {
        "check_ins": [],
        "appointments": [],
        "symptoms": [],
        "devices": [],
        "generated_script": "",
        "selected_schedule": "Day",
        "latest_energy": 5,
        "user": None,
        "crypto_key": None,
        "data_loaded": False,
        "persistent_token": None,
        "tasks": [],
        "reentry_acknowledged": False,
        "self_care_prompt": "",
        "last_affirmation": "",
        "reflections": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_user_state() -> None:
    st.session_state.check_ins = []
    st.session_state.appointments = []
    st.session_state.symptoms = []
    st.session_state.devices = []
    st.session_state.generated_script = ""
    st.session_state.user = None
    st.session_state.crypto_key = None
    st.session_state.data_loaded = False
    st.session_state.persistent_token = None
    st.session_state.selected_schedule = "Day"
    st.session_state.latest_energy = 5
    st.session_state.tasks = []
    st.session_state.self_care_prompt = ""
    st.session_state.last_affirmation = ""


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def derive_persistent_key(token: str) -> bytes:
    digest = hashlib.sha256(f"remember::{token}".encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def get_query_param_token() -> str | None:
    try:
        params = st.query_params
    except AttributeError:
        params = st.experimental_get_query_params()
    value = params.get("session")
    if isinstance(value, list):
        return value[0]
    return value


def set_query_param_token(token: str | None) -> None:
    try:
        params = st.query_params
        if token:
            params["session"] = token
        elif "session" in params:
            del params["session"]
    except AttributeError:
        if token:
            st.experimental_set_query_params(session=token)
        else:
            st.experimental_set_query_params()


def ensure_data_loaded() -> None:
    if st.session_state.user and not st.session_state.data_loaded:
        load_user_data()


def load_user_data() -> None:
    user = st.session_state.user
    key = st.session_state.crypto_key
    if not user or not key:
        return
    uid = user["id"]
    st.session_state.check_ins = [
        {
            "timestamp": datetime.fromisoformat(row["timestamp"]),
            "mood": row["mood"],
            "energy": row["energy"],
            "schedule": row["schedule"],
            "note": decrypt_text(row["note_encrypted"], key),
        }
        for row in db.fetch_check_ins(uid)
    ]
    st.session_state.appointments = [
        {
            "title": decrypt_text(row["title_encrypted"], key),
            "category": row["category"],
            "provider": decrypt_text(row["provider_encrypted"], key),
            "date": datetime.fromisoformat(row["date"]),
            "notes": decrypt_text(row["notes_encrypted"], key),
        }
        for row in db.fetch_appointments(uid)
    ]
    st.session_state.symptoms = [
        {
            "symptom": decrypt_text(row["symptom_encrypted"], key),
            "severity": row["severity"],
            "notes": decrypt_text(row["notes_encrypted"], key),
            "date": datetime.fromisoformat(row["date"]),
        }
        for row in db.fetch_symptoms(uid)
    ]
    st.session_state.devices = [
        {"id": row["id"], "label": row["label"] or "Unnamed device", "token": row["expo_token"]}
        for row in db.fetch_devices(uid)
    ]
    if st.session_state.check_ins:
        latest = st.session_state.check_ins[-1]
        st.session_state.selected_schedule = latest["schedule"]
        st.session_state.latest_energy = latest["energy"]
    st.session_state.data_loaded = True


def store_check_in(entry: Dict) -> None:
    user = st.session_state.user
    key = st.session_state.crypto_key
    if not user or not key:
        st.error("Please sign in to log check-ins.")
        return
    payload = {
        "timestamp": entry["timestamp"].isoformat(),
        "mood": entry["mood"],
        "energy": entry["energy"],
        "schedule": entry["schedule"],
        "note_encrypted": encrypt_text(entry["note"], key),
    }
    db.insert_check_in(user["id"], payload)
    st.session_state.selected_schedule = entry["schedule"]
    st.session_state.latest_energy = entry["energy"]
    st.session_state.reentry_acknowledged = True
    st.session_state.data_loaded = False
    load_user_data()


def add_appointment(entry: Dict) -> None:
    user = st.session_state.user
    key = st.session_state.crypto_key
    if not user or not key:
        st.error("Please sign in to save appointments.")
        return
    payload = {
        "title_encrypted": encrypt_text(entry["title"], key),
        "category": entry["category"],
        "provider_encrypted": encrypt_text(entry["provider"], key),
        "date": entry["date"].isoformat(),
        "notes_encrypted": encrypt_text(entry["notes"], key),
    }
    db.insert_appointment(user["id"], payload)
    st.session_state.data_loaded = False
    load_user_data()


def add_symptom(entry: Dict) -> None:
    user = st.session_state.user
    key = st.session_state.crypto_key
    if not user or not key:
        st.error("Please sign in to track symptoms.")
        return
    payload = {
        "symptom_encrypted": encrypt_text(entry["symptom"], key),
        "severity": entry["severity"],
        "notes_encrypted": encrypt_text(entry["notes"], key),
        "date": entry["date"].isoformat(),
    }
    db.insert_symptom(user["id"], payload)
    st.session_state.data_loaded = False
    load_user_data()


def add_device(label: str, token: str) -> None:
    user = st.session_state.user
    if not user:
        return
    db.insert_device(user["id"], label, token)
    st.session_state.data_loaded = False
    load_user_data()


def create_symptom_pdf(entries: List[Dict]) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, "Heartline Symptom & Note Log", ln=True)
    pdf.ln(5)
    pdf.set_font("Helvetica", size=12)
    if not entries:
        pdf.multi_cell(0, 8, "No entries recorded yet. Sending you gentle encouragement to check in when you're ready.")
    else:
        for item in entries:
            pdf.set_font("Helvetica", "B", 13)
            pdf.cell(0, 8, f"{item['date'].strftime('%b %d, %Y')} — {item['symptom']}", ln=True)
            pdf.set_font("Helvetica", size=12)
            pdf.multi_cell(0, 6, f"Severity: {item['severity']}/10")
            note_text = item["notes"] or "Notes: (none)"
            if not note_text.startswith("Notes"):
                note_text = f"Notes: {note_text}"
            pdf.multi_cell(0, 6, note_text)
            pdf.ln(4)
    data = pdf.output(dest="S")
    return data.encode("latin1") if isinstance(data, str) else bytes(data)


def create_digest_pdf(digest_text: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Heartline Weekly Digest", ln=True)
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 8, digest_text)
    data = pdf.output(dest="S")
    return data.encode("latin1") if isinstance(data, str) else bytes(data)


def create_digest_png(digest_text: str) -> bytes:
    width, height = 900, 400
    image = Image.new("RGB", (width, height), "#FDFBF7")
    draw = ImageDraw.Draw(image)
    font_title = ImageFont.load_default()
    font_body = ImageFont.load_default()
    draw.text((40, 30), "Heartline Weekly Digest", fill="#3A3A3A", font=font_title)
    draw.multiline_text((40, 90), digest_text, fill="#3A3A3A", font=font_body, spacing=8)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def create_ics_calendar(appointments: List[Dict]) -> bytes:
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Heartline Care Companion//EN"]
    for appt in appointments:
        dt_start = appt["date"].strftime("%Y%m%dT090000")
        uid = f"{uuid.uuid4()}@heartline"
        summary = appt["title"] or appt["category"]
        description = appt["notes"] or "Gentle reminder from Heartline."
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}",
                f"DTSTART:{dt_start}",
                f"SUMMARY:{summary}",
                f"DESCRIPTION:{description}",
                "END:VEVENT",
            ]
        )
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines).encode("utf-8")


def weekly_digest_summary(check_ins: List[Dict], symptoms: List[Dict]) -> str:
    window = datetime.now() - timedelta(days=7)
    recent_checks = [c for c in check_ins if c["timestamp"] >= window]
    if not recent_checks:
        return "No check-ins this week. Maybe jot one down so Future You has breadcrumbs."
    avg_mood = sum(c["mood"] for c in recent_checks) / len(recent_checks)
    avg_energy = sum(c["energy"] for c in recent_checks) / len(recent_checks)
    counts = {label: sum(1 for c in recent_checks if c["schedule"] == label) for label in SCHEDULES}
    dominant = max(counts, key=counts.get)
    recent_symptoms = [s for s in symptoms if s["date"] >= window]
    symptom_line = (
        f"You logged {len(recent_symptoms)} symptom notes — maybe bring them to your care team."
        if recent_symptoms
        else "No symptom logs this week. Rest is welcome."
    )
    return (
        f"Average mood {avg_mood:.1f}/10, energy {avg_energy:.1f}/10. "
        f"You lived mostly in {dominant.lower()} rhythm. {symptom_line}"
    )


def build_share_packet() -> bytes:
    payload = {
        "generated_at": datetime.utcnow().isoformat(),
        "check_ins": st.session_state.check_ins,
        "appointments": [
            {**appt, "date": appt["date"].isoformat()} for appt in st.session_state.appointments
        ],
        "symptoms": [
            {**entry, "date": entry["date"].isoformat()} for entry in st.session_state.symptoms
        ],
    }
    return json.dumps(payload, indent=2).encode("utf-8")


def energy_task_suggestions(energy: int) -> List[str]:
    if energy <= 3:
        return ENERGY_TASK_LIBRARY["low"]
    if energy <= 7:
        return ENERGY_TASK_LIBRARY["medium"]
    return ENERGY_TASK_LIBRARY["high"]


def latest_check_in_timestamp() -> datetime | None:
    if not st.session_state.check_ins:
        return None
    return st.session_state.check_ins[-1]["timestamp"]


def needs_no_shame_screen() -> bool:
    if st.session_state.reentry_acknowledged:
        return False
    last = latest_check_in_timestamp()
    if not last:
        return True
    return datetime.now() - last > timedelta(days=3)


def mark_reentry_acknowledged() -> None:
    st.session_state.reentry_acknowledged = True


def add_personal_task(title: str, size: str) -> None:
    st.session_state.tasks.append(
        {"id": str(uuid.uuid4()), "title": title, "size": size, "done": False, "created_at": datetime.utcnow().isoformat()}
    )


def toggle_task_completion(task_id: str, done: bool) -> None:
    for task in st.session_state.tasks:
        if task["id"] == task_id:
            task["done"] = done
            break


def today_three_tasks() -> List[Dict]:
    slots = {"Big": None, "Medium": None, "Tiny": None}
    for task in st.session_state.tasks:
        if not task["done"] and slots.get(task["size"]) is None:
            slots[task["size"]] = task
    guidance = {
        "Big": "Choose one bold move (project chunk, call, study sprint).",
        "Medium": "Handle an admin task or prep a meal.",
        "Tiny": "Send one message or tidy one corner.",
    }
    trio = []
    for size in ["Big", "Medium", "Tiny"]:
        if slots[size]:
            trio.append(slots[size])
        else:
            trio.append({"id": f"placeholder-{size}", "size": size, "title": guidance[size], "done": False})
    return trio


def random_self_care_prompt() -> str:
    prompt = random.choice(SELF_CARE_PROMPTS)
    st.session_state.self_care_prompt = prompt
    return prompt


def current_affirmation() -> str:
    if not st.session_state.last_affirmation:
        st.session_state.last_affirmation = random.choice(AFFIRMATIONS)
    return st.session_state.last_affirmation


def reset_affirmation() -> None:
    st.session_state.last_affirmation = random.choice(AFFIRMATIONS)


def emotion_support_message(feeling: str) -> str:
    return EMOTION_SUPPORT.get(feeling, "You get to do this at your own pace.")


def store_reflection(entry: str) -> None:
    st.session_state.reflections.append({"timestamp": datetime.now(), "text": entry})


def remember_user_session(user_id: int, crypto_key: bytes) -> None:
    token = base64.urlsafe_b64encode(os.urandom(32)).decode("utf-8")
    db_token = hash_token(token)
    fernet_key = derive_persistent_key(token)
    encrypted_key = encrypt_text(base64.b64encode(crypto_key).decode("utf-8"), fernet_key)
    expires_at = (datetime.utcnow() + timedelta(days=7)).isoformat()
    db.store_session_token(user_id, db_token, encrypted_key, expires_at)
    st.session_state.persistent_token = token
    set_query_param_token(token)


def clear_persistent_session() -> None:
    token = st.session_state.get("persistent_token") or get_query_param_token()
    if token:
        db.delete_session_token(hash_token(token))
    st.session_state.persistent_token = None
    set_query_param_token(None)


def auto_login_from_token() -> None:
    if st.session_state.user:
        return
    token = st.session_state.get("persistent_token") or get_query_param_token()
    if not token:
        return
    record = db.fetch_session_token(hash_token(token))
    if not record:
        set_query_param_token(None)
        return
    if datetime.fromisoformat(record["expires_at"]) < datetime.utcnow():
        db.delete_session_token(record["token_hash"])
        set_query_param_token(None)
        return
    user_row = db.get_user_by_id(record["user_id"])
    if not user_row:
        clear_persistent_session()
        return
    try:
        key_string = decrypt_text(record["encrypted_key"], derive_persistent_key(token))
        crypto_key = base64.b64decode(key_string.encode("utf-8"))
    except Exception:
        clear_persistent_session()
        return
    st.session_state.user = {"id": user_row["id"], "email": user_row["email"], "name": user_row["full_name"]}
    st.session_state.crypto_key = crypto_key
    st.session_state.persistent_token = token
    st.session_state.data_loaded = False
    load_user_data()


def set_query_param_token(token: str | None) -> None:
    try:
        params = st.query_params
        if token:
            params["session"] = token
        elif "session" in params:
            del params["session"]
    except AttributeError:
        if token:
            st.experimental_set_query_params(session=token)
        else:
            st.experimental_set_query_params()
