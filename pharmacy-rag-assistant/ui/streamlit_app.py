import sys
from pathlib import Path
import streamlit as st

sys.path.append(str(Path(__file__).parent.parent))

from agents.conversational_agent import ConversationalAgent

st.set_page_config(
    page_title="Аналитик",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #4A9ECC;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        color: #1a1a1a;
    }
    .user-message {
        background-color: #E3F2FD;
        border-left: 4px solid #2196F3;
    }
    .assistant-message {
        background-color: #F3E5F5;
        border-left: 4px solid #9C27B0;
    }
    </style>
    """, unsafe_allow_html=True)


if "agent" not in st.session_state:
    st.session_state.agent = ConversationalAgent()

if "messages" not in st.session_state:
    st.session_state.messages = []

st.markdown('<h1 class="main-header">Аналитический Ассистент</h1>', unsafe_allow_html=True)

with st.sidebar:
    st.divider()

    if st.button("Очистить историю", use_container_width=True):
        st.session_state.messages = []
        st.session_state.agent.clear_history()
        st.rerun()

    st.divider()

for message in st.session_state.messages:
    role = message["role"]
    content = message["content"]

    if role == "user":
        st.markdown(f'<div class="chat-message user-message"><strong>Вы:</strong><br>{content}</div>',
                   unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-message assistant-message"><strong>Ассистент:</strong><br>{content}</div>',
                   unsafe_allow_html=True)

        if "figures" in message:
            for fig in message["figures"]:
                st.plotly_chart(fig, use_container_width=True)


user_input = st.chat_input("Ваш вопрос please...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    st.markdown(f'<div class="chat-message user-message"><strong>Вы:</strong><br>{user_input}</div>',
               unsafe_allow_html=True)

    with st.spinner("Думаю, думаю, ничего не придумаю ..."):
        try:
            result = st.session_state.agent.chat(user_input)
            st.session_state.messages.append({
                "role": "assistant",
                "content": result["response"],
                "figures": result.get("figures", [])
            })

            st.markdown(f'<div class="chat-message assistant-message"><strong>Ассистент:</strong><br>{result["response"]}</div>',
                       unsafe_allow_html=True)

            for fig in result.get("figures", []):
                st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Произошла ошибка: {str(e)}")


if not st.session_state.messages:
    st.info("""
    Для старта можете написать это:
    _ "Дай информацию про аптеки в Астане"
    - "Покажи топ-10 самых продаваемых препаратов"
    - "Как изменились продажи за последний месяц?"
    - "Какие категории медикаментов самые прибыльные?"
    """)
