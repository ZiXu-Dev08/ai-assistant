import streamlit as st
import requests
from datetime import datetime

# ---------- 后端API地址 ----------
API_BASE = "http://172.17.247.223:8000"

# ---------- 页面配置 ----------
st.set_page_config(
    page_title="AI智能助手",
    page_icon="💁🏻",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': "https://www.extremelycoolapp.com/bug",
        'About': "# This is a header. This is an *extremely* cool app!"
    }
)

# ---------- 初始化session_state ----------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "nick_name" not in st.session_state:
    st.session_state.nick_name = "来福"  # 修复：初始化为字符串而非空列表

if "nature" not in st.session_state:
    st.session_state.nature = "专业耐心的助理"  # 修复：初始化为字符串而非空列表

if "current_session" not in st.session_state:
    st.session_state.current_session = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")


# ---------- 辅助函数：调用后端API ----------
def api_save_session():
    """保存当前会话到后端"""
    try:
        resp = requests.post(
            f"{API_BASE}/sessions/{st.session_state.current_session}",
            json={
                "nick_name": st.session_state.nick_name,
                "nature": st.session_state.nature,
                "current_session": st.session_state.current_session,
                "messages": st.session_state.messages
            }
        )

    except Exception:
        pass  # 后端未启动时静默失败


def api_load_sessions():
    """从后端获取会话列表"""
    try:
        resp = requests.get(f"{API_BASE}/sessions")
        return resp.json().get("sessions", [])
    except Exception:
        return []


def api_load_session(session_id):
    """从后端加载指定会话"""
    try:
        resp = requests.get(f"{API_BASE}/sessions/{session_id}")
        if resp.status_code == 200:
            data = resp.json()
            st.session_state.messages = data["messages"]
            st.session_state.nick_name = data["nick_name"]
            st.session_state.nature = data["nature"]
            st.session_state.current_session = session_id
    except Exception:
        st.error("加载会话失败，请确认后端已启动")


def api_delete_session(session_id):
    """从后端删除指定会话"""
    try:
        requests.delete(f"{API_BASE}/sessions/{session_id}")
        if st.session_state.current_session == session_id:
            st.session_state.messages = []
            st.session_state.current_session = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    except Exception:
        st.error("删除会话失败")


# ---------- 页面标题 ----------
st.title("AI智能助手")
st.write("欢迎来到AI智能助手")

# ---------- 展示聊天记录 ----------
st.text(f"会话名称：{st.session_state.current_session}")
for message in st.session_state.messages:
    if message["role"] == "user":
        st.chat_message("user").write(message["content"])
    else:
        st.chat_message("assistant").write(message["content"])

# ---------- 侧边栏 ----------
with st.sidebar:
    st.subheader("AI控制面板")

    # 新建会话
    if st.button("新建会话", use_container_width=True, icon="✏️"):
        if st.session_state.messages:
            api_save_session()  # 保存旧会话到后端
        st.session_state.messages = []
        st.session_state.current_session = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        st.rerun()

    # 会话历史
    st.text("会话历史")
    session_list = api_load_sessions()
    for session in session_list:
        col1, col2 = st.columns([4, 1])
        with col1:
            is_current = session == st.session_state.current_session
            if st.button(
                    session,
                    use_container_width=True,
                    icon="📃",
                    key=f"load_{session}",
                    type="primary" if is_current else "secondary"
            ):
                if st.session_state.messages:
                    api_save_session()  # 先保存当前会话
                api_load_session(session)
                st.rerun()
        with col2:
            if st.button("", use_container_width=True, icon="❎️", key=f"delete_{session}"):
                api_delete_session(session)
                st.rerun()

    st.divider()

    # 助手信息
    st.subheader("助手信息")
    nick_name = st.text_input("名称", placeholder="请输入名称", value=st.session_state.nick_name)
    if nick_name:
        st.session_state.nick_name = nick_name
    nature = st.text_area("性格", placeholder="请输入助手性格", value=st.session_state.nature)
    if nature:
        st.session_state.nature = nature

# ---------- 聊天输入 ----------
prompt = st.chat_input("请输入所咨询的问题：")
if prompt:
    # 显示用户消息
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 调用后端API（替代原来直接调DeepSeek）
    assistant_placeholder = st.empty()
    full_response = ""

    try:
        response = requests.post(
            f"{API_BASE}/chat",
            json={
                "message": prompt,
                "nick_name": st.session_state.nick_name,
                "nature": st.session_state.nature,
                "messages_history": st.session_state.messages[:-1],  # 历史消息（不含刚发的）
                "stream": True
            },
            stream=True  # 流式接收
        )

        if response.status_code == 200:
            # 流式输出
            for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                if chunk:
                    full_response += chunk
                    assistant_placeholder.chat_message("assistant").write(full_response)
        else:
            st.error(f"API调用失败：{response.status_code}")
            full_response = "抱歉，服务暂时不可用。"
            assistant_placeholder.chat_message("assistant").write(full_response)

    except requests.exceptions.ConnectionError:
        st.error("无法连接到后端服务，请确认FastAPI已启动（uvicorn backend:app --reload）")
        full_response = "后端服务未启动。"
        assistant_placeholder.chat_message("assistant").write(full_response)
    except Exception as e:
        st.error(f"发生错误：{e}")
        full_response = "抱歉，发生了未知错误。"
        assistant_placeholder.chat_message("assistant").write(full_response)

    # 保存AI回复
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    api_save_session()