import os
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI(title="AI智能助手API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # 允许所有来源（开发阶段）
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- 系统角色模板 ----------
SYSTEM_PROMPT_TEMPLATE = """
你叫{nick_name}，现在是用户的智能助手，请完全代入助手角色。
规则: 
  1.每次只回1条消息
  2.禁止任何场景或状态描述性文字
  3.匹配用户的语言
  4.回复简短，像微信聊天一样
  5.有需要的话可以用emoji表情
  6.用符合助手性格的方式对话
  7.回复的内容，要充分体现助手的性格特征
助手性格: {nature}
你必须严格遵守上述规则来回复用户。
"""

# ---------- OpenAI客户端 ----------
client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# ---------- 数据模型 ----------
class ChatRequest(BaseModel):
    message: str
    nick_name: str = "来福"
    nature: str = "专业耐心的助理"
    messages_history: list = []
    stream: bool = True

class SessionData(BaseModel):
    nick_name: str
    nature: str
    current_session: str
    messages: list

# ---------- 会话管理（文件操作） ----------
SESSIONS_DIR = "sessions"

def ensure_sessions_dir():
    if not os.path.exists(SESSIONS_DIR):
        os.mkdir(SESSIONS_DIR)

def save_session(session_id: str, nick_name: str, nature: str, messages: list):
    ensure_sessions_dir()
    session_data = {
        "nick_name": nick_name,
        "nature": nature,
        "current_session": session_id,
        "messages": messages
    }
    with open(f"{SESSIONS_DIR}/{session_id}.json", "w", encoding="utf-8") as f:
        json.dump(session_data, f, ensure_ascii=False, indent=2)

def load_session(session_id: str) -> dict | None:
    filepath = f"{SESSIONS_DIR}/{session_id}.json"
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def list_sessions() -> list:
    if not os.path.exists(SESSIONS_DIR):
        return []
    files = [f[:-5] for f in os.listdir(SESSIONS_DIR) if f.endswith(".json")]
    files.sort(reverse=True)
    return files

def delete_session_file(session_id: str):
    filepath = f"{SESSIONS_DIR}/{session_id}.json"
    if os.path.exists(filepath):
        os.remove(filepath)

# ---------- API接口 ----------
@app.get("/sessions")
async def get_sessions():
    """获取所有会话列表"""
    return {"sessions": list_sessions()}

@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """获取指定会话详情"""
    data = load_session(session_id)
    if data is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    return data

# 【新增】保存会话的接口
@app.post("/sessions/{session_id}")
async def save_session_endpoint(session_id: str, session_data: SessionData):
    """保存或更新指定会话"""
    save_session(
        session_id=session_id,
        nick_name=session_data.nick_name,
        nature=session_data.nature,
        messages=session_data.messages
    )
    return {"status": "ok"}

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """删除指定会话"""
    delete_session_file(session_id)
    return {"status": "ok"}

@app.post("/chat")
async def chat(request: ChatRequest):
    """核心接口：发送消息，获取AI回复"""
    # 构建完整的消息列表
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        nick_name=request.nick_name,
        nature=request.nature
    )
    messages = [
        {"role": "system", "content": system_prompt},
        *request.messages_history,
        {"role": "user", "content": request.message}
    ]

    # 调用大模型（修正模型名）
    response = client.chat.completions.create(
        model="deepseek-chat",          # 修复：原 deepseek-v4-pro 改为 deepseek-chat
        messages=messages,
        stream=request.stream,
        # reasoning_effort 和 extra_body 是 deepseek-reasoner 的参数，标准 deepseek-chat 不支持，可去掉
        # 若要保留，需确保模型支持。建议先去掉。
    )

    if request.stream:
        # 流式返回生成器
        async def generate():
            for chunk in response:
                # 确保 delta.content 不为 None
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        return StreamingResponse(generate(), media_type="text/plain")
    else:
        reply = response.choices[0].message.content
        return {"reply": reply}