import streamlit as st
from rag.retriever import get_rag_response

st.set_page_config(
    page_title="RAG Chatbot",
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Hide Streamlit default header chrome */
    #MainMenu, footer, header { visibility: hidden; }


    /* Form card */
    .form-card {
        background: white;
        border-radius: 16px;
        padding: 40px 44px;
        border: 1px solid #e8e7e2;
        max-width: 520px;
        margin: 0 auto;
    }

    /* Chat message bubbles */
    .msg-user {
        background: #4f46e5;
        color: white;
        padding: 10px 10px;
        border-radius: 16px 16px 4px 16px;
        margin: 6px 0 6px auto;
        max-width: 75%;
        font-size: 15px;
        line-height: 1.6;
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    .msg-bot {
        background: white;
        color: #1a1a1a;
        padding: 10px 10px;
        border-radius: 16px 16px 16px 4px;
        border: 1px solid #e8e7e2;
        margin: 6px auto 6px 0;
        max-width: 80%;
        font-size: 15px;
        line-height: 1.6;
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    .msg-wrapper-user { display: flex; justify-content: flex-end; }
    .msg-wrapper-bot  { display: flex; justify-content: flex-start; }

    /* Profile pill in chat header */
    .profile-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: #eeedfe;
        border: 1px solid #afa9ec;
        border-radius: 20px;
        padding: 5px 14px;
        font-size: 14px;
        color: #3c3489;
        font-weight: 500;
    }

    /* Primary button override */
    .stButton > button {
        background: #6495ED !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-size: 14px !important;
        padding: 0.3rem 0.8rem !important;
        font-weight: 500 !important;
    }
    .stButton > button:hover {
        background: #0047AB !important;
    }
            
</style>
""", unsafe_allow_html=True)


# ── Session state defaults ────────────────────────────────────────────────────
def init_state():
    defaults = {
        "form_done": False,
        "profile": {},
        "messages": [],   # list of {"role": "user"|"assistant", "content": "..."}
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 1 — ONBOARDING FORM
# ══════════════════════════════════════════════════════════════════════════════
def show_form():
    st.markdown("<br>", unsafe_allow_html=True)

    # Centered header
    st.markdown("""
        <div style='text-align:center; margin-bottom: 8px;'>
            <span style='font-size:36px;'>💬</span>
            <h2 style='margin:8px 0 4px; font-weight:600;'>
                Before we start
            </h2>
            <p style=' font-size:15px; margin:0;'>
                Answer a few quick questions so the assistant can help you better.
            </p>
        </div>
        <br>
    """, unsafe_allow_html=True)

    with st.form("onboarding_form", clear_on_submit=False):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input(
                "Your name",
                placeholder="e.g. Wei Ling",
                help="Used to personalise the assistant's responses."
            )

        with col2:
            ageGroup = st.selectbox(
            "Age Group",
            options=["18-25", "26-39", "40-50", "50+"],
        )
        role = st.selectbox(
            "Your role",
            options=["Searching for Rental", "Currently Renting", "Landlord/Tenant"],
        )

        language = st.selectbox(
            "Preferred language",
            options=["English", "Mandarin", "Malay", "Tamil", "French", "Spanish"],
        )

        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("Start chatting →", use_container_width=True)

        if submitted:
            if not name.strip():
                st.error("Please enter your name to continue.")
            else:
                st.session_state.profile = {
                    "name":     name.strip(),
                    "ageGroup":     ageGroup,
                    "role":     role,
                    "language": language
                }
                st.session_state.form_done = True
                st.session_state.messages = []
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 2 — CHAT INTERFACE
# ══════════════════════════════════════════════════════════════════════════════
def show_chat():
    profile = st.session_state.profile
    title_row = st.container(
        horizontal=True,
        vertical_alignment="bottom",
    )

    with title_row:
        st.title(
            "Singapore Rental Assistant",
            anchor=False,
            width="stretch",
        )

    # ── Header ────────────────────────────────────────────────────────────────
    col_left, col_right = st.columns([3, 1])
    with col_left:
        st.markdown(f"""
            <div class='profile-pill'>
                👤 {profile['name']} · {profile['role']} · {profile['ageGroup']} · {profile['language']}
            </div>
        """, unsafe_allow_html=True)
    with col_right:
        if st.button("← New session",use_container_width=True):
            st.session_state.form_done = False
            st.session_state.messages = []
            st.session_state.profile = {}
            st.rerun()
    st.divider()

    # ── Message history ───────────────────────────────────────────────────────
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"""
                <div class='msg-wrapper-user'>
                    <div class='msg-user'>{msg['content']}</div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class='msg-wrapper-bot'>
                    <div class='msg-bot'>{msg['content']}</div>
                </div>
            """, unsafe_allow_html=True)

    # Welcome message on first load
    if not st.session_state.messages:
        st.markdown(f"""
            <div class='msg-wrapper-bot'>
                <div class='msg-bot'>
                    Hi {profile['name']}! I'm ready to help you with your rental enquiries.
                    I'll answer in <strong>{profile['language']}</strong> based on the documents in my knowledge base.
                    What would you like to know?
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Input ─────────────────────────────────────────────────────────────────
    with st.form("chat_form", clear_on_submit=True):
        col_input, col_btn = st.columns([5, 1])
        with col_input:
            user_input = st.text_input(
                "message",
                placeholder="Ask a question...",
                label_visibility="collapsed",
            )
        with col_btn:
            send = st.form_submit_button("Send", use_container_width=True)

    if send and user_input.strip():
        user_msg = user_input.strip()
        st.session_state.messages.append({"role": "user", "content": user_msg})

        with st.spinner("Thinking..."):
            try:
                reply = get_rag_response(
                    query=user_msg,
                    profile=profile,
                    history=st.session_state.messages[:-1],  # exclude the just-added message
                )
            except Exception as e:
                reply = f"Sorry, something went wrong: {str(e)}"

        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  ROUTER
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.form_done:
    show_chat()
else:
    show_form()
