# How to Run: streamlit run app.py

import os
import streamlit as st
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

load_dotenv()

st.set_page_config(page_title="Disaster Preparedness Assistant", page_icon="🆘", layout="wide")
st.title("🆘 Disaster Preparedness Assistant")

MODE_NOW = "⚡ Now Action"
MODE_PLAN = "🧰 Preparedness Plan"

# Sidebar controls
with st.sidebar:
    st.header("⚙️ Settings")

    provider = st.selectbox("Provider", ["Auto", "Gemini", "Groq"], index=0)

    mode = st.selectbox("Mode", [MODE_NOW, MODE_PLAN], index=0)

    style = st.selectbox("Gaya bahasa", ["Formal", "Santai"], index=1)
    temperature = st.slider("Temperature", 0.0, 1.0, 0.4, 0.05)

    st.divider()
    st.subheader("🔑 API Keys")
    google_key = st.text_input(
        "GOOGLE_API_KEY (Gemini)", type="password", value=os.getenv("GOOGLE_API_KEY", "")
    )
    groq_key = st.text_input(
        "GROQ_API_KEY (Groq)", type="password", value=os.getenv("GROQ_API_KEY", "")
    )

    colk1, colk2 = st.columns(2)
    with colk1:
        if st.button("Save keys"):
            if google_key:
                os.environ["GOOGLE_API_KEY"] = google_key
            if groq_key:
                os.environ["GROQ_API_KEY"] = groq_key
            st.success("Keys saved (session).")
    with colk2:
        if st.button("🧹 Clear chat"):
            st.session_state.chat_history = []
            st.session_state.last_provider_used = None
            st.session_state.last_model_used = None
            st.rerun()

    st.divider()
    st.subheader("🤖 Model IDs")
    gemini_model = st.text_input("Gemini model", value="gemini-2.5-flash")
    groq_model = st.text_input("Groq model", value="meta-llama/llama-4-scout-17b-16e-instruct")

    st.divider()
    st.caption("Tip: Auto akan coba Gemini dulu, lalu fallback ke Groq kalau error/limit.")

# Session state init
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_provider_used" not in st.session_state:
    st.session_state.last_provider_used = None
if "last_model_used" not in st.session_state:
    st.session_state.last_model_used = None

# Dynamic caption
mode_desc = {
    MODE_NOW: "⚡ *Now Action*: prioritas, langkah cepat, dan pesan ke keluarga/RT (dipakai saat sudah cukup aman membuka HP).",
    MODE_PLAN: "🧰 *Preparedness Plan*: go-bag, home prep, rencana evakuasi, dan plan 7 hari.",
}[mode]

selected_desc = {"Auto": "Auto", "Gemini": "Gemini", "Groq": "Groq"}[provider]

last_used = st.session_state.last_provider_used
last_model = st.session_state.last_model_used

if last_used and last_model:
    st.caption(f"Mode: {mode_desc} · Provider: **{selected_desc}** · Last used: **{last_used}** (`{last_model}`)")
else:
    st.caption(f"Mode: {mode_desc} · Provider: **{selected_desc}**")

# Prompts
def build_system_prompt(mode_name: str, style_name: str) -> str:
    style_rules = (
        "Gunakan bahasa baku, ringkas, gunakan kata 'Anda'."
        if style_name == "Formal"
        else "Gunakan bahasa santai tapi tetap sopan, gunakan kata 'kamu'."
    )

    global_rules = f"""
Kamu adalah Disaster Preparedness Assistant fokus BANJIR & GEMPA.
Tujuan: memberi langkah aman, terstruktur, dan bisa dipraktikkan (bukan teori panjang).

FRAMING PENTING:
- Mode "Now Action" digunakan saat pengguna sudah cukup aman untuk membuka HP
  (misalnya setelah guncangan berhenti / saat air mulai naik tapi masih aman bergerak).
- Fokus utama: prioritas tindakan + komunikasi (pesan singkat untuk keluarga/RT/posko).

ATURAN KESELAMATAN (WAJIB):
- Prioritaskan keselamatan jiwa.
- Jika ada air dekat listrik / stop kontak / panel: JANGAN sentuh listrik.
- Jangan buat nomor darurat/lokasi spesifik jika user tidak memberi.
- Tidak memberi diagnosa medis / instruksi medis detail.
- Jika info penting belum ada, tanya pertanyaan singkat (maks 3) sebelum memberi langkah rinci.

GAYA BAHASA: {style_rules}
Selalu gunakan heading & bullet yang rapi.
""".strip()

    if mode_name == MODE_NOW:
        mode_rules = """
MODE: Now Action
- Jika bencana belum jelas, tanya: "Ini BANJIR atau GEMPA?"
- Ajukan maks 3 pertanyaan konteks jika belum ada:
  * BANJIR: (1) air sudah masuk rumah? (2) lantai berapa? (3) listrik dekat air atau aman?
  * GEMPA: (1) di rumah/apartemen/kantor? (2) ada luka/terjebak? (3) ada bau gas/asap/retakan besar?

Jika konteks sudah cukup, jawab dengan format WAJIB:

Ringkasan situasi:
✅ Langkah 0–10 menit (1–5):
📣 Pesan cepat (Keluarga + RT/Posko):
🔁 Jika... maka... (triggers):
⚠️ Peringatan singkat (maks 3):
""".strip()
    else:
        mode_rules = """
MODE: PREPAREDNESS PLAN (rencana kesiapsiagaan)
- Ajukan pertanyaan singkat untuk personalisasi (maks 4):
  1) tinggal di rumah/apartemen dan lantai
  2) ada bayi/lansia/hewan?
  3) risiko utama: banjir/gempa/keduanya
  4) kendaraan: motor/mobil/tidak
- Buat rencana realistis: maksimal 12–18 item per bagian.
- Jawab dengan format WAJIB:

🎒 Go Bag checklist:
🏠 Home prep checklist:
🗺️ Rencana evakuasi:
📅 Rencana 7 hari:
""".strip()

    return global_rules + "\n\n" + mode_rules

# LLM factory dan fallback
def make_gemini(model: str, temp: float):
    return ChatGoogleGenerativeAI(model=model, temperature=temp)

def make_groq(model: str, temp: float):
    return ChatGroq(model=model, temperature=temp)

def to_lc_messages(system_prompt: str, history: list[dict]) -> list[tuple]:
    msgs: list[tuple] = [("system", system_prompt)]
    for m in history:
        msgs.append(("human" if m["role"] == "user" else "ai", m["content"]))
    return msgs

def invoke_with_fallback(messages: list[tuple]):
    chosen = provider
    has_gemini_key = bool(os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"))
    has_groq_key = bool(os.getenv("GROQ_API_KEY"))

    def try_gemini():
        llm = make_gemini(gemini_model, temperature)
        out = llm.invoke(messages)
        st.session_state.last_provider_used = "Gemini"
        st.session_state.last_model_used = gemini_model
        return out

    def try_groq():
        llm = make_groq(groq_model, temperature)
        out = llm.invoke(messages)
        st.session_state.last_provider_used = "Groq"
        st.session_state.last_model_used = groq_model
        return out

    if chosen == "Gemini":
        if not has_gemini_key:
            raise RuntimeError("GOOGLE_API_KEY belum di-set untuk Gemini.")
        return try_gemini()

    if chosen == "Groq":
        if not has_groq_key:
            raise RuntimeError("GROQ_API_KEY belum di-set untuk Groq.")
        return try_groq()

    # Auto
    if has_gemini_key:
        try:
            return try_gemini()
        except Exception:
            if has_groq_key:
                return try_groq()
            raise
    else:
        if has_groq_key:
            return try_groq()
        raise RuntimeError("Tidak ada API key. Isi GOOGLE_API_KEY atau GROQ_API_KEY di sidebar.")

# UI rendering
def extract_section(text: str, start_markers: list[str], end_markers: list[str]) -> str:
    start_idx = None
    marker_used = None
    for m in start_markers:
        i = text.find(m)
        if i != -1 and (start_idx is None or i < start_idx):
            start_idx = i
            marker_used = m
    if start_idx is None:
        return ""

    line_end = text.find("\n", start_idx)
    body_start = line_end + 1 if line_end != -1 else start_idx + len(marker_used)

    end_idx = None
    for em in end_markers:
        j = text.find(em, body_start)
        if j != -1 and (end_idx is None or j < end_idx):
            end_idx = j

    if end_idx is None:
        return text[body_start:].strip()
    return text[body_start:end_idx].strip()

def render_assistant(text: str, current_mode: str):
    markers_now = ["Ringkasan situasi", "✅ Langkah 0–10 menit", "📣 Pesan cepat", "🔁 Jika", "⚠️ Peringatan"]
    markers_prep = ["🎒 Go Bag", "🏠 Home prep", "🗺️ Rencana evakuasi", "📅 Rencana 7 hari"]

    if current_mode == MODE_NOW:
        if not any(m in text for m in markers_now):
            st.markdown(text)
            return

        summary = extract_section(
            text,
            ["Ringkasan situasi", "Ringkasan situasi:"],
            ["✅ Langkah 0–10 menit", "📣 Pesan cepat", "🔁 Jika", "⚠️ Peringatan"],
        )
        steps = extract_section(
            text,
            ["✅ Langkah 0–10 menit", "✅ Langkah 0–10 menit (1–5)", "✅ Langkah 0–10 menit (1–5):"],
            ["📣 Pesan cepat", "🔁 Jika", "⚠️ Peringatan"],
        )
        msg = extract_section(
            text,
            ["📣 Pesan cepat", "📣 Pesan cepat (Keluarga + RT/Posko)", "📣 Pesan cepat (Keluarga + RT/Posko):", "📣 Pesan cepat:"],
            ["🔁 Jika", "⚠️ Peringatan"],
        )
        triggers = extract_section(
            text,
            ["🔁 Jika", "🔁 Jika... maka... (triggers)", "🔁 Jika... maka... (triggers):"],
            ["⚠️ Peringatan"],
        )
        warnings = extract_section(
            text,
            ["⚠️ Peringatan", "⚠️ Peringatan singkat", "⚠️ Peringatan singkat (maks 3)", "⚠️ Peringatan singkat (maks 3):"],
            [],
        )

        if summary:
            st.info(summary)
        if steps:
            st.subheader("✅ Langkah 0–10 menit")
            st.markdown(steps)
        if msg:
            st.subheader("📣 Pesan cepat")
            st.code(msg, language="text")
        if triggers:
            st.subheader("🔁 Jika… maka…")
            st.warning(triggers)
        if warnings:
            st.subheader("⚠️ Peringatan")
            st.error(warnings)

    else:
        if not any(m in text for m in markers_prep):
            st.markdown(text)
            return

        go_bag = extract_section(
            text,
            ["🎒 Go Bag", "🎒 Go Bag checklist", "🎒 Go Bag checklist:"],
            ["🏠 Home prep", "🗺️ Rencana evakuasi", "📅 Rencana 7 hari"],
        )
        home_prep = extract_section(
            text,
            ["🏠 Home prep", "🏠 Home prep checklist", "🏠 Home prep checklist:"],
            ["🗺️ Rencana evakuasi", "📅 Rencana 7 hari"],
        )
        evac = extract_section(
            text,
            ["🗺️ Rencana evakuasi", "🗺️ Rencana evakuasi:"],
            ["📅 Rencana 7 hari"],
        )
        plan7 = extract_section(
            text,
            ["📅 Rencana 7 hari", "📅 Rencana 7 hari:"],
            [],
        )

        if go_bag:
            st.subheader("🎒 Go Bag checklist")
            st.markdown(go_bag)
        if home_prep:
            st.subheader("🏠 Home prep checklist")
            st.markdown(home_prep)
        if evac:
            st.subheader("🗺️ Rencana evakuasi")
            st.markdown(evac)
        if plan7:
            st.subheader("📅 Rencana 7 hari")
            st.markdown(plan7)

# Render existing history
for m in st.session_state.chat_history:
    with st.chat_message("user" if m["role"] == "user" else "assistant"):
        if m["role"] == "assistant":
            render_assistant(m["content"], mode)
        else:
            st.markdown(m["content"])

# Chat input
user_text = st.chat_input(
    "Ketik situasi kamu… (contoh: 'barusan gempa, saya di apartemen lantai 10' / 'air mulai naik di rumah')"
)
if not user_text:
    st.stop()

st.session_state.chat_history.append({"role": "user", "content": user_text})
with st.chat_message("user"):
    st.markdown(user_text)

system_prompt = build_system_prompt(mode, style)
lc_messages = to_lc_messages(system_prompt, st.session_state.chat_history)

try:
    ai_msg = invoke_with_fallback(lc_messages)
    ai_text = ai_msg.content if isinstance(ai_msg.content, str) else str(ai_msg.content)
except Exception as e:
    ai_text = (
        "Maaf, terjadi error saat memanggil model.\n\n"
        f"- Provider: **{provider}**\n"
        f"- Detail: `{type(e).__name__}: {e}`\n\n"
        "Cek API key di sidebar, atau ganti Provider ke Groq / Auto."
    )

st.session_state.chat_history.append({"role": "assistant", "content": ai_text})
with st.chat_message("assistant"):
    render_assistant(ai_text, mode)
