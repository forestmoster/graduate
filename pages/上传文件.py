from openai import OpenAI
from openai.types.beta.threads import TextContentBlock
import streamlit as st
from langchain.tools import DuckDuckGoSearchRun
import io
import os
import shutil
import openai
import pandas as pd
from docx.shared import Inches
from langchain.agents import AgentExecutor, initialize_agent, AgentType, LLMSingleActionAgent, AgentOutputParser
from langchain.callbacks import StreamlitCallbackHandler
from langchain.chat_models import ChatOpenAI
from langchain.prompts import StringPromptTemplate
import streamlit as st
import uuid
from docx import Document
from langchain.tools import Tool
from typing import List, Union
from FILE_Chroma import FileChroma, streamlit_sidebar_delete_database

# 创建tmp临时文件夹
# if 'session_id' not in st.session_state:
#     st.session_state.session_id = str(uuid.uuid4())  # 创建一个唯一的UUID
# session_folder = os.path.join('tmp', st.session_state.session_id)
# 创建永久文件夹
session_folder = './tmp/graduate_database'
# xxxxxxxx
vector_folder = os.path.join(session_folder, 'vector')
if not os.path.exists(vector_folder):
    os.makedirs(vector_folder)
if not os.path.exists(session_folder):
    os.makedirs(session_folder)
PDFS=FileChroma(vector_folder)
uploaded_file = st.file_uploader("选择一个纯文本docx文件或者pdf文件",accept_multiple_files=True,label_visibility="hidden")
s=st.button(label='提交文件到数据库')
if s:
    st.caption('稍等这个过程可能要几min')
    PDFS.upload_pdfs_chroma(uploaded_file)
    PDFS.upload_docx_chroma(uploaded_file)

streamlit_sidebar_delete_database(PDFS)