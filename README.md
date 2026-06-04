# AI智能助手

基于 FastAPI + Streamlit 的前后端分离 AI 智能助手系统。

## 功能介绍

- 前后端分离架构：FastAPI 提供 RESTful API，Streamlit 构建交互界面
- 集成 DeepSeek 大模型，支持流式与非流式两种输出模式
- 基于 JSON 文件的会话持久化，支持多轮对话与历史会话管理
- 可配置 AI 角色系统，用户可自定义助手昵称与性格参数
- 使用 Pydantic 定义接口数据模型，自动生成 API 文档
- 使用 Apifox 完成全部接口测试

## 技术栈

Python / FastAPI / Streamlit / DeepSeek API / Pydantic / JSON

## 如何运行

### 1. 安装依赖
pip install fastapi uvicorn streamlit openai requests

### 2. 设置环境变量
在系统环境变量中添加 DEEPSEEK_API_KEY

### 3. 启动后端
uvicorn backend:app --host 0.0.0.0 --port 8000 --reload

### 4. 启动前端
streamlit run app.py --server.address 0.0.0.0 --server.port 8501

### 5. 访问
浏览器打开 http://localhost:8501
