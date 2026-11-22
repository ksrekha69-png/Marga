import csv
import os
import streamlit as st

st.set_page_config(page_title="ಮಾರ್ಗ | Marga", page_icon="🎓")

st.markdown(
    "<style>.block-container{max-width:760px;padding-top:1.5rem;}</style>",
    unsafe_allow_html=True,
)

@st.cache_data
def load_courses(version):
    with open("data/courses.csv", encoding="utf-8") as f:
        return list(csv.DictReader(f))

courses = load_courses(os.path.getmtime("data/courses.csv"))
courses = load_courses(os.path.getmtime("data/courses.csv"))
# ---------- Language ----------
lang = st.radio("language", ["ಕನ್ನಡ", "English"], horizontal=True,
                label_visibility="collapsed")
KN = lang == "ಕನ್ನಡ"

def t(kn, en):
    return kn if KN else en

def pick(row, field):
    """Kannada value if available, else English."""
    if KN and row.get(field + "_kn"):
        return row[field + "_kn"]
    return row.get(field + "_en") or row.get(field) or "-"

# ---------- Labels ----------
LEVELS = {
    "after_10th": ("10ನೇ ನಂತರ", "After 10th", "📘"),
    "after_puc": ("ಪಿಯುಸಿ ನಂತರ", "After PUC", "🎓"),
    "after_iti": ("ಐಟಿಐ ನಂತರ", "After ITI", "🔧"),
    "after_diploma": ("ಡಿಪ್ಲೊಮಾ ನಂತರ", "After Diploma", "📐"),
    "after_degree": ("ಪದವಿ ನಂತರ", "After Degree", "🏛️"),
    "after_pg": ("ಸ್ನಾತಕೋತ್ತರ ನಂತರ", "After PG", "🎓"),
}

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
}

def cat_label(key):
    kn, en, icon = CATEGORIES.get(key, (key.title(), key.title(), "📌"))
    return f"{icon} {t(kn, en)}"

def fix_duration(text):
    if not KN:
        return text
    return (text.replace("years", "ವರ್ಷ").replace("year", "ವರ್ಷ")
                .replace("Varies", "ಬದಲಾಗುತ್ತದೆ"))

# ---------- Header ----------
st.title("🎓 ಮಾರ್ಗ | Marga")
st.caption(t("ನಿಮ್ಮ ಮುಂದಿನ ದಾರಿ ಕಂಡುಕೊಳ್ಳಿ: ಕರ್ನಾಟಕದ ಎಲ್ಲಾ ಕೋರ್ಸ್‌ಗಳು",
             "Find your next path: courses across Karnataka"))

# ---------- Step 1: level ----------
st.subheader(t("1️⃣ ನೀವು ಏನು ಪಾಸ್ ಮಾಡಿದ್ದೀರಿ?", "1️⃣ What have you passed?"))
level = st.pills(
    "level",
    list(LEVELS.keys()),
    default="after_10th",
    format_func=lambda k: f"{LEVELS[k][2]} {t(LEVELS[k][0], LEVELS[k][1])}",
    label_visibility="collapsed",
) or "after_10th"

by_level = [c for c in courses if level in c["levels"].split("|")]

# ---------- Step 2: category ----------
available = sorted({c["category"] for c in by_level})
st.subheader(t("2️⃣ ನಿಮ್ಮ ಆಸಕ್ತಿಯ ವಿಭಾಗ", "2️⃣ Your field of interest"))
category = st.selectbox(
    "category",
    ["all"] + available,
    format_func=lambda k: t("ಎಲ್ಲಾ ವಿಭಾಗಗಳು", "All fields") if k == "all" else cat_label(k),
    label_visibility="collapsed",
)

search = st.text_input(
    "search",
    placeholder=t("🔍 ಕೋರ್ಸ್ ಹೆಸರು ಹುಡುಕಿ...", "🔍 Search course name..."),
    label_visibility="collapsed",
).strip().lower()

# ---------- Filter ----------
results = by_level
if category != "all":
    results = [c for c in results if c["category"] == category]
if search:
    results = [c for c in results
               if search in c["name_en"].lower() or search in c["name_kn"]]

st.markdown(f"**{t('ಸಿಕ್ಕ ಕೋರ್ಸ್‌ಗಳು', 'Courses found')}: {len(results)}**")

# ---------- Cards ----------
if not results:
    st.info(t("ಯಾವುದೇ ಕೋರ್ಸ್ ಸಿಗಲಿಲ್ಲ. ಬೇರೆ ವಿಭಾಗ ಅಥವಾ ಹೆಸರು ಪ್ರಯತ್ನಿಸಿ.",
              "No courses found. Try another field or keyword."))

for row in results:
    with st.container(border=True):
        st.markdown(f"### {row['name_kn'] if KN else row['name_en']}")
        st.caption(f"{cat_label(row['category'])}  •  ⏱ {fix_duration(row['duration'])}")
        with st.expander(t("ಪೂರ್ತಿ ವಿವರ ನೋಡಿ", "See full details")):
            st.markdown(f"**✅ {t('ಅರ್ಹತೆ', 'Eligibility')}:** {pick(row, 'eligibility')}")
            st.markdown(f"**💼 {t('ಉದ್ಯೋಗ ಅವಕಾಶ', 'Career scope')}:** {pick(row, 'career_scope')}")
            if row.get("official_link"):
                st.markdown(f"🔗 [{t('ಅಧಿಕೃತ ವೆಬ್‌ಸೈಟ್', 'Official website')}]({row['official_link']})")

# ---------- Footer ----------
st.divider()
st.caption(t(
    "⚠️ ಪ್ರವೇಶದ ಮೊದಲು ಅರ್ಹತೆ, ಶುಲ್ಕ ಮತ್ತು ದಿನಾಂಕಗಳನ್ನು ಅಧಿಕೃತ ವೆಬ್‌ಸೈಟ್‌ನಲ್ಲಿ ಪರಿಶೀಲಿಸಿ.",
    "⚠️ Verify eligibility, fees and dates on the official website before applying."))