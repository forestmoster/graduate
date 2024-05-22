import sys
__import__("pysqlite3")
sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
from openai import OpenAI
from langchain_community.tools import DuckDuckGoSearchRun
import streamlit as st
import ask_page
from typing_extensions import override
from openai import AssistantEventHandler
from FILE_Chroma import FileChroma
import json
client = OpenAI()
styl = """
<style>

    .stButton{
        position: fixed;
        bottom: 1rem;
        left:500;
        right:500;
        z-index:999;
    }

    @media screen and (max-width: 1000px) {

        .stButton {
            left:2%;
            width: 100%;
            bottom:1.1rem;
            z-index:999;
        }
    }

</style>

"""

st.markdown(styl, unsafe_allow_html=True)

st.title("💬 环境设计系毕业设计论文助手")
st.caption('你可以查询任何问题，也可以帮助我完善数据库，上传:blue[文件]')

# def search_database(query: str) -> str:
#   query_message = ask_page.query_message_langchain(query=query, token_budget=2000, )
#   return query_message

search = DuckDuckGoSearchRun()
PDFS=FileChroma('./tmp/graduate_database/vector')

def search_web(query: str) -> str:
      # 解析 JSON 字符串
    s = json.loads(query)
    query_message = search.run(s['query'])
    return query_message


def search_database(query):
  g= json.loads(query)
  s = PDFS.search_upload_files_chroma(g['query'])
  return f'{s}'


assistant_id='asst_dXkXdPmBFZOmMX1UhLdjBo1l'

class EventHandler(AssistantEventHandler):
  @override
  def on_event(self, event):
    # Retrieve events that are denoted with 'requires_action'
    # since these will have our tool_calls
    if event.event == 'thread.run.requires_action':
      run_id = event.data.id  # Retrieve the run ID from the event data
      self.handle_requires_action(event.data, run_id)

  def handle_requires_action(self, data, run_id):
    tool_outputs = []
    for tool in data.required_action.submit_tool_outputs.tool_calls:
      if tool.function.name == "search_database":
        tool_outputs.append({"tool_call_id": tool.id, "output":search_database(tool.function.arguments)})
      elif tool.function.name == "search_web":
        tool_outputs.append({"tool_call_id": tool.id, "output": search_web(tool.function.arguments)})

    # Submit all tool_outputs at the same time
    self.submit_tool_outputs(tool_outputs, run_id)

  def submit_tool_outputs(self, tool_outputs, run_id):
    # Use the submit_tool_outputs_stream helper
    with client.beta.threads.runs.submit_tool_outputs_stream(
            thread_id=self.current_run.thread_id,
            run_id=self.current_run.id,
            tool_outputs=tool_outputs,
            event_handler=EventHandler(),
    ) as stream:
      stream.until_done()
    # Use the submit_tool_outputs_stream helper

def run_openai_query(content: str,thread_id=None):
  if thread_id==None:
    thread = client.beta.threads.create()
    thread_id=thread.id
  client.beta.threads.messages.create(
    thread_id=thread_id,
    role="user",
    content=content,
  )
  with client.beta.threads.runs.stream(
          thread_id=thread_id,
          assistant_id=assistant_id,
          event_handler=EventHandler()
  ) as stream:
    stream.until_done()

def thread_all_messages(thread_id:str):
  thread_messages = client.beta.threads.messages.list(thread_id)
  messages = [
      {
          "role": msg.role,
          "content": msg.content[0].text.value
      }
      for msg in thread_messages
  ][::-1]
  return(messages)


def thread_last_message(thread_id: str):
  thread_messages = client.beta.threads.messages.list(thread_id)
  # 遍历消息并返回第一条
  for message in thread_messages:
    return {
      "role": message.role,
      "content": message.content[0].text.value
    }
  # 如果没有消息，返回 None
  return None


def delete_messages(thread_id:str):
  response = client.beta.threads.delete(thread_id)
  return response



if "thread_id" not in st.session_state:
  thread = client.beta.threads.create()
  thread_id = thread.id
  st.session_state["thread_id"] = thread_id
  st.session_state["messages_web"] = thread_all_messages(st.session_state["thread_id"])
if st.button('重新开始一个回答'):
  delete_messages(st.session_state["thread_id"])
  thread = client.beta.threads.create()
  thread_id = thread.id
  st.session_state["thread_id"] = thread_id
  st.session_state["messages_web"] = thread_all_messages(st.session_state["thread_id"])
  # 清空文本输入框的内容
  user_input = ""

st.session_state["messages_web"] = thread_all_messages(st.session_state["thread_id"])
for msg in st.session_state["messages_web"]:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input(placeholder="在这打字，回答问题"):
  st.chat_message("user").write(prompt)
  with st.chat_message("assistant"):
    placeholder = st.empty()
    placeholder.caption('搜索完成🎉')
    placeholder.caption('我现在在思考，别催🎈🎈')
    s=run_openai_query(f'{prompt}', f'{st.session_state["thread_id"]}')
    response=thread_last_message(f'{st.session_state["thread_id"]}')
    response=response['content']
    response_audio = client.audio.speech.create(
      model="tts-1",
      voice="alloy",
      input=response
    )
    response_audio.write_to_file("./speech.mp3")
    st.audio("./speech.mp3", autoplay=True)
    placeholder.empty()
    placeholder.caption('完成🎉')
    st.write(response)

