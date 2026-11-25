import csv
import os
import sqlite3
import hashlib
import secrets
import hmac
import streamlit as st

# ================= PAGE SETUP =================
st.set_page_config(page_title="Marga | ಮಾರ್ಗ", page_icon="🧭", layout="centered")

APP_DIR = os.path.dirname(os.path.abspath(__file__))
COURSES_FILE = os.path.join(APP_DIR, "data", "courses.csv")
DB_FILE = os.path.join(APP_DIR, "marga_users.db")

# ================= STYLING =================
st.markdown("""
<style>
.block-container { max-width: 900px; padding-top: 1.1rem; padding-bottom: 2rem; }
:root { --navy:#17324D; --teal:#168C86; --gold:#D6A84F; }
[data-testid="stHeader"] { background: transparent; }
div.stButton > button { border-radius: 12px; font-weight: 600; min-height: 42px; }
div.stButton > button[kind="primary"] { background: #17324D; border-color: #17324D; color: white; }
div.stButton > button[kind="primary"]:hover { background: #168C86; border-color: #168C86; color: white; }
div[data-testid="stExpander"] { border-radius: 12px; }
.marga-brand { text-align:center; padding: 1.1rem 0 .5rem; }
.marga-mark { font-size: 2.5rem; line-height: 1.2; }
.marga-name { font-size: 2.35rem; font-weight: 800; letter-spacing: .08em; color: #17324D; }
.marga-sub { color: #168C86; font-size: .92rem; letter-spacing: .12em; font-weight: 600; }
.intro-card { background: linear-gradient(135deg,#17324D,#168C86); color:white; padding:1.6rem 1.3rem; border-radius:20px; text-align:center; margin:.6rem 0 1rem; }
.intro-card h2 { color:white; margin-bottom:.35rem; }
.intro-card p { color:#E9F5F4; font-size:1.05rem; }
.small-note { color:#64748b; font-size:.88rem; }
</style>
""", unsafe_allow_html=True)

# ================= COURSE DATA =================
@st.cache_data
def load_courses(_file_version):
    with open(COURSES_FILE, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

courses = load_courses(os.path.getmtime(COURSES_FILE))

# ================= LANGUAGE =================
if "lang" not in st.session_state:
    st.session_state["lang"] = "English"

KN = st.session_state.get("lang", "English") == "ಕನ್ನಡ"

def t(kn, en):
    return kn if KN else en

def language_picker_compact(key="lang_compact"):
    # Small, compact dropdown selector instead of large two-button block.
    options = ["English", "ಕನ್ನಡ"]
    current = st.session_state.get("lang", "English")
    chosen = st.selectbox(
        "🌐",
        options,
        index=options.index(current) if current in options else 0,
        key=key,
        label_visibility="collapsed",
    )
    if chosen != st.session_state.get("lang"):
        st.session_state["lang"] = chosen
        st.rerun()

# ================= PASSWORDS =================
def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 300_000
    ).hex()
    return f"{salt}:{hashed}"

def verify_password(password, stored_hash):
    try:
        salt, expected_hash = stored_hash.split(":", 1)
        # New accounts use 300,000 iterations. Also check 200,000 iterations
        # so accounts created by the earlier app version can still log in.
        for iterations in (300_000, 200_000):
            actual_hash = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations
            ).hex()
            if hmac.compare_digest(expected_hash, actual_hash):
                return True
        return False
    except (ValueError, AttributeError, TypeError):
        return False

# ================= USER DB / MIGRATION =================
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                eligibility TEXT NOT NULL,
                name TEXT NOT NULL DEFAULT ''
            )
        """)
        # Add name column to an existing database made by the older version.
        columns = {r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()}
        if "name" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN name TEXT NOT NULL DEFAULT ''")
        conn.commit()

init_db()

def set_login(email, name, eligibility):
    st.session_state["logged_in"] = True
    st.session_state["email"] = email
    st.session_state["name"] = name
    st.session_state["eligibility"] = eligibility
    st.session_state["show_intro"] = True

# ================= AUTH SCREEN =================
if not st.session_state.get("logged_in", False):
    left, right = st.columns([4, 1])
    with left:
        st.markdown("""
        <div class="marga-brand">
          <div class="marga-mark">🧭</div>
          <div class="marga-name">MARGA</div>
          <div class="marga-sub">DISCOVER · LEARN · GROW</div>
        </div>
        """, unsafe_allow_html=True)
    with right:
        language_picker_compact("auth_language")

    st.markdown(
        f"<div style='text-align:center;color:#64748b;margin:.2rem 0 1rem'>{t('ನಿಮ್ಮ ಕನಸುಗಳಿಗೆ ದಾರಿ ಹುಡುಕಿ','Find the path to your dreams')}</div>",
        unsafe_allow_html=True,
    )
    reg_tab, login_tab = st.tabs([t("ಹೊಸ ಖಾತೆ", "Register"), t("ಲಾಗಿನ್", "Login")])

    eligibility_options = [
        "After 10th", "After PUC / 12th", "After ITI",
        "After Diploma", "After Degree", "After PG"
    ]

    with reg_tab:
        st.subheader(t("ನಿಮ್ಮ ಖಾತೆ ರಚಿಸಿ", "Create your account"))
        reg_name = st.text_input(t("ನಿಮ್ಮ ಹೆಸರು", "Full name"), key="register_name")
        reg_email = st.text_input(t("ಇಮೇಲ್", "Email address"), key="register_email")
        reg_password = st.text_input(t("ಪಾಸ್‌ವರ್ಡ್ (ಕನಿಷ್ಠ 8 ಅಕ್ಷರ)", "Password (at least 8 characters)"), type="password", key="register_password")
        reg_confirm = st.text_input(t("ಪಾಸ್‌ವರ್ಡ್ ದೃಢೀಕರಿಸಿ", "Confirm password"), type="password", key="register_confirm")
        reg_eligibility = st.selectbox(t("ನಿಮ್ಮ ವಿದ್ಯಾರ್ಹತೆ", "Your eligibility"), eligibility_options, key="register_eligibility")
        if st.button(t("ಖಾತೆ ರಚಿಸಿ", "Create account"), type="primary", use_container_width=True, key="register_submit"):
            name = reg_name.strip()
            email = reg_email.strip().lower()
            if not name:
                st.error(t("ನಿಮ್ಮ ಹೆಸರು ನಮೂದಿಸಿ.", "Please enter your name."))
            elif not email or "@" not in email or "." not in email.split("@")[-1]:
                st.error(t("ಸರಿಯಾದ ಇಮೇಲ್ ನಮೂದಿಸಿ.", "Please enter a valid email."))
            elif len(reg_password) < 8:
                st.error(t("ಪಾಸ್‌ವರ್ಡ್ ಕನಿಷ್ಠ 8 ಅಕ್ಷರಗಳಿರಬೇಕು.", "Password must be at least 8 characters."))
            elif reg_password != reg_confirm:
                st.error(t("ಪಾಸ್‌ವರ್ಡ್‌ಗಳು ಹೊಂದಿಕೆಯಾಗುತ್ತಿಲ್ಲ.", "Passwords do not match."))
            else:
                try:
                    with sqlite3.connect(DB_FILE) as conn:
                        conn.execute(
                            "INSERT INTO users (email,password_hash,eligibility,name) VALUES (?,?,?,?)",
                            (email, hash_password(reg_password), reg_eligibility, name),
                        )
                        conn.commit()
                    st.success(t("ಖಾತೆ ರಚಿಸಲಾಗಿದೆ! ಸ್ವಾಗತ.", "Account created! Welcome."))
                    set_login(email, name, reg_eligibility)
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error(t("ಈ ಇಮೇಲ್ ಈಗಾಗಲೇ ನೋಂದಾಯಿಸಲಾಗಿದೆ. Login ಬಳಸಿ.", "This email is already registered. Please log in."))

    with login_tab:
        st.subheader(t("ಮತ್ತೆ ಸ್ವಾಗತ", "Welcome back"))
        login_email = st.text_input(t("ಇಮೇಲ್", "Email address"), key="login_email")
        login_password = st.text_input(t("ಪಾಸ್‌ವರ್ಡ್", "Password"), type="password", key="login_password")
        if st.button(t("ಲಾಗಿನ್ ಮಾಡಿ", "Log in"), type="primary", use_container_width=True, key="login_submit"):
            email = login_email.strip().lower()
            with sqlite3.connect(DB_FILE) as conn:
                user = conn.execute(
                    "SELECT email,password_hash,eligibility,name FROM users WHERE email=?",
                    (email,),
                ).fetchone()
            if user and verify_password(login_password, user[1]):
                name = user[3].strip() if user[3] else email.split("@")[0].replace(".", " ").title()
                set_login(user[0], name, user[2])
                st.rerun()
            else:
                st.error(t("ಇಮೇಲ್ ಅಥವಾ ಪಾಸ್‌ವರ್ಡ್ ತಪ್ಪಾಗಿದೆ. Password case-sensitive; ನೋಂದಾಯಿಸಿದಾಗ ಬಳಸಿದ ಪಾಸ್‌ವರ್ಡ್ ಅದೇ ನಮೂದಿಸಿ.", "Email or password is incorrect. Passwords are case-sensitive; enter the exact password used when registering."))
    st.stop()

# ================= INTRO / WELCOME =================
if st.session_state.get("show_intro", False):
    lang_col, _ = st.columns([1, 5])
    with lang_col:
        language_picker_compact("intro_language")

    name = st.session_state.get("name", "Friend")
    st.markdown(f"""
    <div class="intro-card">
      <div style="font-size:2.5rem;margin-bottom:.2rem">🧭</div>
      <h2>Hi {name}, welcome to Marga!</h2>
      <p>Your journey begins here.</p>
      <div style="font-size:1.15rem;font-weight:700;letter-spacing:.06em;margin-top:1rem">
        DISCOVER&nbsp; ✦ &nbsp;LEARN&nbsp; ✦ &nbsp;GROW&nbsp; ✦ &nbsp;ACHIEVE
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### " + t("ನಿಮ್ಮ ಭವಿಷ್ಯಕ್ಕೆ ಹೊಸ ದಾರಿ", "A new path for your future"))
    # Slideshow-like welcome panels. User can continue into the main page.
    intro_cols = st.columns(3)
    with intro_cols[0]:
        st.markdown(f"**🔎 {t('ಹುಡುಕಿ','Discover')}**")
        st.caption(t("ನಿಮ್ಮ ಆಸಕ್ತಿಗೆ ಹೊಂದುವ ಕೋರ್ಸ್‌ಗಳನ್ನು ಹುಡುಕಿ.", "Explore courses that match your interests."))
    with intro_cols[1]:
        st.markdown(f"**📘 {t('ಕಲಿಯಿರಿ','Learn')}**")
        st.caption(t("ಶಿಕ್ಷಣ ಮತ್ತು ಕೌಶಲ್ಯಗಳ ಅವಕಾಶಗಳನ್ನು ತಿಳಿಯಿರಿ.", "Learn about education and skill opportunities."))
    with intro_cols[2]:
        st.markdown(f"**🌱 {t('ಬೆಳೆಯಿರಿ','Grow')}**")
        st.caption(t("ನಿಮ್ಮ ಗುರಿಯತ್ತ ವಿಶ್ವಾಸದಿಂದ ಸಾಗಿರಿ.", "Move toward your goals with confidence."))
    if st.button(t("Marga ಗೆ ಮುಂದುವರಿಯಿರಿ →", "Continue to Marga →"), type="primary", use_container_width=True):
        st.session_state["show_intro"] = False
        st.rerun()
    st.stop()

# ================= COURSE LABELS =================
LEVELS = {
    "all_courses": ("ಎಲ್ಲಾ ಕೋರ್ಸ್‌ಗಳು", "All Courses", "📚"),
    "after_10th": ("10ನೇ ನಂತರ", "After 10th", "📘"),
    "after_puc": ("ಪಿಯುಸಿ ನಂತರ", "After PUC", "🎓"),
    "after_iti": ("ಐಟಿಐ ನಂತರ", "After ITI", "🔧"),
    "after_diploma": ("ಡಿಪ್ಲೊಮಾ ನಂತರ", "After Diploma", "📐"),
    "after_degree": ("ಪದವಿ ನಂತರ", "After Degree", "🏛️"),
    "after_pg": ("ಸ್ನಾತಕೋತ್ತರ ನಂತರ", "After PG", "🎓"),
    "skills": ("ಕೌಶಲ್ಯ ಕೋರ್ಸ್‌ಗಳು", "Skills", "🛠️"),
    "jobs": ("ಸರ್ಕಾರಿ ಉದ್ಯೋಗ", "Govt Jobs", "🏢"),
}
SPECIAL = {"skills": {"skill"}, "jobs": {"government"}}

CATEGORIES = {
    "engineering": ("ಇಂಜಿನಿಯರಿಂಗ್", "Engineering", "⚙️"),
    "medical": ("ವೈದ್ಯಕೀಯ", "Medical", "🩺"),
    "nursing": ("ನರ್ಸಿಂಗ್", "Nursing", "💉"),
    "paramedical": ("ಪ್ಯಾರಾಮೆಡಿಕಲ್", "Paramedical", "🧪"),
    "pharmacy": ("ಫಾರ್ಮಸಿ", "Pharmacy", "💊"),
    "science": ("ವಿಜ್ಞಾನ", "Science", "🔬"),
    "commerce": ("ವಾಣಿಜ್ಯ", "Commerce", "💼"),
    "management": ("ಮ್ಯಾನೇಜ್‌ಮೆಂಟ್", "Management", "📊"),
    "arts": ("ಕಲಾ", "Arts", "🎨"),
    "law": ("ಕಾನೂನು", "Law", "⚖️"),
    "education": ("ಶಿಕ್ಷಣ", "Education", "📚"),
    "computer": ("ಕಂಪ್ಯೂಟರ್", "Computer", "💻"),
    "iti": ("ಐಟಿಐ", "ITI", "🔧"),
    "government": ("ಸರ್ಕಾರಿ ಸೇವೆ", "Government", "🏢"),
    "agriculture": ("ಕೃಷಿ", "Agriculture", "🌾"),
    "hospitality": ("ಆತಿಥ್ಯ", "Hospitality", "🏨"),
    "design": ("ವಿನ್ಯಾಸ", "Design", "🎨"),
    "media": ("ಮಾಧ್ಯಮ", "Media", "📰"),
    "fine_arts": ("ಲಲಿತ ಕಲೆ", "Fine Arts", "🖼️"),
    "sports": ("ಕ್ರೀಡೆ", "Sports", "🏅"),
    "skill": ("ಕೌಶಲ್ಯ", "Skill", "🛠️"),
    "aviation": ("ವಿಮಾನಯಾನ", "Aviation", "✈️"),
    "maritime": ("ಸಮುದ್ರಯಾನ", "Maritime", "🚢"),
    "logistics": ("ಲಾಜಿಸ್ಟಿಕ್ಸ್", "Logistics", "📦"),
    "banking": ("ಬ್ಯಾಂಕಿಂಗ್ ಮತ್ತು ಹಣಕಾಸು", "Banking and Finance", "🏦"),
    "beauty": ("ಸೌಂದರ್ಯ", "Beauty", "💄"),
}

def cat_label(key):
    kn, en, icon = CATEGORIES.get(key, (key.title(), key.title(), "📌"))
    return f"{icon} {t(kn, en)}"

def pick(row, field):
    if KN and row.get(field + "_kn"):
        return row[field + "_kn"]
    return row.get(field + "_en") or "-"

def fix_duration(text):
    s = (text or "-").replace(" to ", "–")
    if KN:
        for a, b in [
            ("years plus training", "ವರ್ಷ + ತರಬೇತಿ"), ("years", "ವರ್ಷ"),
            ("year", "ವರ್ಷ"), ("months", "ತಿಂಗಳು"), ("month", "ತಿಂಗಳು"),
            ("weeks", "ವಾರ"), ("week", "ವಾರ"), ("Varies", "ಬದಲಾಗುತ್ತದೆ"),
            ("Selection", "ಆಯ್ಕೆ ಆಧಾರಿತ"), ("Exam", "ಪರೀಕ್ಷೆ ಆಧಾರಿತ")
        ]:
            s = s.replace(a, b)
    return s

# ================= MAIN APP HEADER =================
header_left, header_right = st.columns([4, 1])
with header_left:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:.7rem;padding:.15rem 0">
      <span style="font-size:2rem">🧭</span>
      <div>
        <div style="font-size:1.65rem;font-weight:800;letter-spacing:.05em;color:#17324D">MARGA <span style="font-size:1.2rem;color:#168C86">ಮಾರ್ಗ</span></div>
        <div style="font-size:.72rem;letter-spacing:.12em;color:#168C86;font-weight:600">DISCOVER · LEARN · GROW</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
with header_right:
    language_picker_compact("main_language")
    if st.button("↪ Logout", key="logout_btn", help="Log out"):
        for key in ["logged_in", "email", "name", "eligibility", "show_intro"]:
            st.session_state.pop(key, None)
        st.rerun()

name = st.session_state.get("name", "Friend")
st.markdown(f"### {t('ನಮಸ್ಕಾರ','Hi')} {name}, {t('ಮಾರ್ಗಕ್ಕೆ ಸ್ವಾಗತ!','welcome to Marga!')} 👋")
st.markdown(f"<div style='color:#168C86;font-weight:500;margin-bottom:1rem'>{t('ನಿಮ್ಮ ಕನಸುಗಳಿಗೆ ದಾರಿ ಹುಡುಕಿ — ಕಲಿಕೆ ಮತ್ತು ಅವಕಾಶಗಳು ಒಂದೇ ಕಡೆ.','Find your path to possibilities — learning and opportunities in one place.')}</div>", unsafe_allow_html=True)

# ================= STEP 1 / FILTER =================
st.subheader(t("1️⃣ ಕೋರ್ಸ್ ಹಂತ ಆಯ್ಕೆ ಮಾಡಿ", "1️⃣ Choose a course level"))
level = st.pills(
    "level", list(LEVELS.keys()), default="all_courses",
    format_func=lambda k: f"{LEVELS[k][2]} {t(LEVELS[k][0], LEVELS[k][1])}",
    label_visibility="collapsed",
) or "all_courses"

if level == "all_courses":
    by_level = courses
elif level in SPECIAL:
    by_level = [c for c in courses if c["category"] in SPECIAL[level]]
else:
    by_level = [c for c in courses if level in c.get("levels", "").split("|")]

# ================= STEP 2 / CATEGORY =================
st.subheader(t("2️⃣ ನಿಮ್ಮ ಆಸಕ್ತಿಯ ವಿಭಾಗ", "2️⃣ Your field of interest"))
available = sorted({c["category"] for c in by_level})
category = st.selectbox(
    "category", ["all"] + available,
    format_func=lambda k: t("ಎಲ್ಲಾ ವಿಭಾಗಗಳು", "All fields") if k == "all" else cat_label(k),
    label_visibility="collapsed",
)

search = st.text_input(
    "search", placeholder=t("🔍 ಕೋರ್ಸ್ ಹೆಸರು ಹುಡುಕಿ...", "🔍 Search course name..."),
    label_visibility="collapsed",
).strip().lower()

results = by_level
if category != "all":
    results = [c for c in results if c["category"] == category]
if search:
    results = [c for c in results if search in c.get("name_en", "").lower() or search in c.get("name_kn", "").lower()]

st.markdown(f"**{t('ಸಿಕ್ಕ ಕೋರ್ಸ್‌ಗಳು','Courses found')}: {len(results)}**")
if not results:
    st.info(t("ಯಾವುದೇ ಕೋರ್ಸ್ ಸಿಗಲಿಲ್ಲ. ಬೇರೆ ವಿಭಾಗ ಅಥವಾ ಹೆಸರು ಪ್ರಯತ್ನಿಸಿ.", "No courses found. Try another field or keyword."))

# ================= COURSE CARDS =================
for row in results:
    with st.container(border=True):
        st.markdown(f"### {row.get('name_kn') if KN else row.get('name_en')}")
        st.caption(cat_label(row.get("category", "")))
        with st.expander(t("ಪೂರ್ತಿ ವಿವರ ನೋಡಿ", "See full details")):
            st.markdown(f"**⏱ {t('ಅವಧಿ','Duration')}:** {fix_duration(row.get('duration',''))}")
            st.markdown(f"**✅ {t('ಅರ್ಹತೆ','Eligibility')}:** {pick(row, 'eligibility')}")
            st.markdown(f"**💼 {t('ಉದ್ಯೋಗ ಅವಕಾಶ','Career scope')}:** {pick(row, 'career_scope')}")
            if row.get("official_link"):
                st.markdown(f"🔗 [{t('ಅಧಿಕೃತ ವೆಬ್‌ಸೈಟ್','Official website')}]({row['official_link']})")

# ================= FOOTER =================
st.divider()
st.caption(t(
    "⚠️ ಪ್ರವೇಶದ ಮೊದಲು ಅರ್ಹತೆ, ಶುಲ್ಕ ಮತ್ತು ದಿನಾಂಕಗಳನ್ನು ಅಧಿಕೃತ ವೆಬ್‌ಸೈಟ್‌ನಲ್ಲಿ ಪರಿಶೀಲಿಸಿ.",
    "⚠️ Verify eligibility, fees and dates on the official website before applying."
))
