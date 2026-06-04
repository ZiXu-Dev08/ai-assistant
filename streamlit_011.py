import streamlit as st#导入streamlit库
import os#导入os库（系统环境变量）
from openai import OpenAI#导入openai库（大模型）
from datetime import datetime
import json

#设置页面配置
st.set_page_config(
    page_title="AI智能助手",#页面标题
    page_icon="💁🏻",#图标
    layout="wide",#页面布局，可选值有centered（居中）和wide（全屏）
    initial_sidebar_state="expanded",#侧边栏状态，
    menu_items={
        'Get Help': 'https://www.extremelycoolapp.com/help',#帮助按钮所链接的URL（网址）
        'Report a bug': "https://www.extremelycoolapp.com/bug",#错误按钮所链接的URL
        'About': "# This is a header. This is an *extremely* cool app!"#关于按钮所链接的URL
    }
)

#创建一个函数，用于保存聊天内容
def save_session():
    # 1、保存当前会话信息
    if st.session_state.current_session:
        # 构建新的会话对象
        session_data = {
            "nick_name": st.session_state.nick_name,  # 昵称
            "nature": st.session_state.nature,  # 性格
            "current_session": st.session_state.current_session, # 会话标识
            "messages": st.session_state.messages  # 会话内容
        }

        # 创建文件夹
        if not os.path.exists("sessions"):  # 判断session文件夹是否存在
            os.mkdir("sessions")  # 创建session文件夹

        # 保存会话信息
        with open(f"sessions/{st.session_state.current_session}.json", "w", encoding="utf-8")as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)


#加载所有的会话列表信息
def load_sessions():
    session_list=[]
    #加载sessions目录下的文件
    if os.path.exists("sessions"):#判断session文件夹是否存在
        file_list = os.listdir("sessions")#获取session目录下的文件列表
        for filename in file_list:#遍历文件列表
            if filename.endswith(".json"):#判断文件名是否以.json结尾
                session_list.append(filename[:-5])#获取文件名，并去掉.json后缀
    session_list.sort(reverse=True)#返回会话列表,倒序排列
    return session_list

#加载指定的会话信息
def load_session(session_name):
    try:
        if os.path.exists(f"sessions/{session_name}.json"):
            #读取会话数据
            with open(f"sessions/{session_name}.json","r",encoding="utf-8") as f:
                session_data = json.load(f)
                st.session_state.messages = session_data["messages"]
                st.session_state.nick_name = session_data["nick_name"]
                st.session_state.nature = session_data["nature"]
                st.session_state.current_session = session_name
    except Exception:
        st.error("加载会话失败！")


#删除会话信息
def delete_session(session_name):
    try:
        if os.path.exists(f"sessions/{session_name}.json",):#判断文件是否存在
            os.remove(f"sessions/{session_name}.json")#删除文件
            #如果删除的是当前会话，则需要更新消息列表
            if st.session_state.current_session == session_name:#判断当前会话是否是删除的会话
                st.session_state.messages = []#清空消息列表
                st.session_state.current_session =generate_session_name().strftime("%Y-%m-%d-%H-%M-%S")#构建新的会话
    except Exception:
        st.error("删除会话失败！")


#大标题
st.title("AI智能助手")
st.write("欢迎来到AI智能助手")

#ai系统角色设置
ai ="""
        你叫%s，现在是用户的智能助手，请完全代入助手角色。
        规则: 
          1.每次只回1条消息
          2.禁止任何场景或状态描述性文字
          3.匹配用户的语言
          4.回复简短，像微信聊天一样
          5.有需要的话可以用等emoji表情
          6.用符合助手性格的方式对话
          7.回复的内容，要充分体现助手的性格特征
        助手性格:
            %s
        你必须严格遵守上述规则来回复用户。
    """

print("<-------------------------系统角色：",ai)




# 初始化聊天内容
if "messages" not in st.session_state:#判断session_state.messages变量是否存在
    st.session_state.messages = []#创建session_state.messages变量，并初始化为一个空列表用来保存聊天内容

 #初始化昵称
if "nick_name" not in st.session_state:#判断session_state.messages变量是否存在
    st.session_state.nick_name = []#创建session_state.messages变量，并初始化为一个空列表用来保存聊天内容

 #初始化性格
if "nature" not in st.session_state:#判断session_state.messages变量是否存在
    st.session_state.nature = []#创建session_state.messages变量，并初始化为一个空列表用来保存聊天内容

#会话标识
if "current_session" not in st.session_state:
    st.session_state.current_session =datetime.now().strftime("%Y-%m-%d-%H-%M-%S")


# 展示聊天信息
st.text(f"会话名称：{st.session_state.current_session}")
for message in st.session_state.messages:#遍历session_state.messages变量中的内容，列表中的存储格式为 {"role": "user", "content": "prompt}
    if message["role"] == "user":#判断消息来源
        st.chat_message("user").write(message["content"])#调用streamlit的chat_message方法，创建一个用户消息，参数是消息的来源，将用户输入的问题作为消息内容输出用户输入的问题
    else:
        st.chat_message("assistant").write(message["content"])#调用streamlit的chat_message方法，创建一个助手消息，参数是消息的来源，将大模型回复的内容作为消息内容输出大模型回复的内容

#创建openai客户端
client = OpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY'),#设置API密钥
    base_url="https://api.deepseek.com")#设置API地址


#左侧侧边栏
with (st.sidebar):
    #会话信息
    st.subheader("AI控制面板")

    #新建会话
    if st.button("新建会话",width="stretch",icon="✏️"):#st.button("按钮名称"，width=按钮大小，icon=图标)
        #1、调用函数，保存当前会话信息
        save_session()

        #2、新建会话
        if st.session_state.messages:#判断session_state.messages变量是否为空,不为空则保存当前会话信息
            st.session_state.messages = []#清空session_state.messages变量
            st.session_state.current_session =datetime.now().strftime("%Y-%m-%d-%H-%M-%S")#生成会话标识
            save_session()#保存当前会话信息
            st.rerun()#重新运行当前页面

    #会话历史
    st.text("会话历史")
    session_list = load_sessions()
    for session in session_list:
        col1,col2 = st.columns([4,1])
        with col1:
            #加载会话信息
            if st.button(session,width="stretch",icon="📃",key=f"load_{session}",type="primary" if session == st.session_state.current_session else "secondary"):
                load_session(session)
                st.rerun()
        # 删除会话
        with col2:
            if st.button("",width="stretch",icon="❎️",key=f"delete_{session}"):
                delete_session(session)
                st.rerun()

    #分割线
    st.divider()

    #助手信息
    st.subheader("助手信息")
    #昵称输入框
    nick_name = st.text_input("名称",placeholder="请输入名称",value="来福")#创建昵称输入框
    #昵称保存
    if nick_name:
        st.session_state.nick_name = nick_name
    #性格输入框
    nature= st.text_area("性格",placeholder="请输入助手性格",value="专业耐心的助理")
    #性格保存
    if nature:
        st.session_state.nature = nature

# 创建聊天输入框
prompt = st.chat_input("请输入所咨询的问题：")  # 调用streamlit的chat_input方法，创建聊天输入框，参数是输入框的提示语，将用户输入的问题保存在prompt变量
if prompt:  # 判断prompt变量是否为空
    st.chat_message("user").write(prompt)  # 调用streamlit的chat_message方法，创建一个用户消息，参数是消息的来源，将用户输入的问题作为消息内容输出用户输入的问题
    st.session_state.messages.append({"role": "user", "content": prompt})  # 将用户所输入的内容保存在session_state.messages变量中


    #调用大模型
    response = client.chat.completions.create(
        model="deepseek-v4-pro",#设置模型名称
        messages=[#
            {"role": "system", "content": ai % (st.session_state.nick_name,st.session_state.nature)},#设置系统角色，系统角色是模型根据上下文进行ChatGPT对话的参考角色，这里设置模型根据上下文进行ChatGPT对话的参考角色为陪伴
            *st.session_state.messages   #将列表中存储的历史记录解包出来作为参数，参数是模型根据上下文进行ChatGPT对话的参考，解决模型不能记忆的问题
        ],
        stream= True,#设置是否返回流式数据
        reasoning_effort="high",#设置模型推理的难度
        extra_body={"thinking": {"type": "enabled"}}#设置模型推理的难度
    )

    print("<------------------------提示词：", prompt)

    #非流式输出大模型回复
    #st.chat_message("assistant").write(response.choices[0].message.content)#调用streamlit的chat_message方法，创建一个用户消息，参数是消息的来源，将大模型回复的内容作为消息内容输出大模型回复的内容

    #流式输出大模型回复
    response_message = st.empty()
    full_response = ""
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            full_response += content
            response_message.write(full_response)

    st.session_state.messages.append(
        {"role": "assistant", "content": full_response})  # 将大模型回复的内容保存在session_state.messages变量中
    print("<-------------------------大模型回复：", full_response)

    #保存会话信息
    save_session()