import chromadb
import jieba.analyse
from docx import Document
import os
import PyPDF2
from langchain_chroma import Chroma
import split
from langchain_openai import OpenAIEmbeddings
import jieba.analyse
import streamlit as st
class FileChroma:

    def __init__(self, vector_folder):
        self.vector_folder = vector_folder
        self.embedding_function = OpenAIEmbeddings(model="text-embedding-ada-002")

    @staticmethod
    def load_all_stopwords(dir_path):
        """
        Load all stopwords from all files in a directory and set them in jieba.
        """
        for filename in os.listdir(dir_path):
            if filename.endswith(".txt"):
                file_path = os.path.join(dir_path, filename)
                jieba.analyse.set_stop_words(file_path)

    def upload_pdfs_chroma(self, uploaded_files):
        if not uploaded_files:
            return None
        for uploaded_file in uploaded_files:
            all_strings = []
            if not uploaded_file.name.lower().endswith('.pdf'):
                continue
            try:
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
            except:
                raise ValueError("不支持的文件类型")
            title = uploaded_file.name
            url = ''
            self.load_all_stopwords('./stopwords-master')
            for page in pdf_reader.pages:
                page_text = page.extract_text().replace('...', '').replace('..', '').strip()
                tags = jieba.analyse.extract_tags(page_text, topK=10)
                tags_strings = " ".join(tags)
                all_strings.append((title, url, tags_strings, [page_text]))
            wikipedia_strings = []
            MAX_TOKENS = 2450
            for section in all_strings:
                wikipedia_strings.extend(split.split_strings_from_subsection_pdf(section, max_tokens=MAX_TOKENS))
            ids = [f"{title}_{i}" for i in range(1, len(wikipedia_strings) + 1)]
            pdfsearch = Chroma.from_texts(wikipedia_strings, self.embedding_function, collection_name="state-of-union",
                                          persist_directory=self.vector_folder, ids=ids)
        # return pdfsearch

    def upload_pdfs_chroma_catch(self, uploaded_files):
        if not uploaded_files:
            return None
        for uploaded_file in uploaded_files:
            all_strings = []
            if not uploaded_file.name.lower().endswith('.pdf'):
                continue
            try:
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
            except:
                raise ValueError("不支持的文件类型")
            title = uploaded_file.name
            url = ''
            self.load_all_stopwords('./stopwords-master')
            for page in pdf_reader.pages:
                page_text = page.extract_text().replace('...', '').replace('..', '').strip()
                tags = jieba.analyse.extract_tags(page_text, topK=10)
                tags_strings = " ".join(tags)
                all_strings.append((title, url, tags_strings, [page_text]))
            wikipedia_strings = []
            MAX_TOKENS = 2450
            for section in all_strings:
                wikipedia_strings.extend(split.split_strings_from_subsection_pdf(section, max_tokens=MAX_TOKENS))
            ids = [f"{title}_{i}" for i in range(1, len(wikipedia_strings) + 1)]

            pdfsearch = Chroma.from_texts(wikipedia_strings, self.embedding_function, collection_name="state-of-union",
                                           ids=ids)
            return pdfsearch

    @staticmethod
    def read_doc_font(uploaded_files):
        doc = Document(uploaded_files)
        paragraphs_strings = []
        font_sizes = []
        font_bolds = []
        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()
            if text:  # 跳过空字符串
                paragraphs_strings.append(text)
                for run in paragraph.runs:
                    font_sizes.append(run.font.size)
                    font_bolds.append(run.font.bold)
            combined_data = list(zip(paragraphs_strings, font_sizes, font_bolds))
        return combined_data

    def upload_docx_chroma(self, uploaded_files, title_long: int = 20, MAX_TOKENS: int = 2000):
        if not uploaded_files:
            return None  # 或者可以抛出一个异常，例如：raise ValueError("没有上传的文件")

        for uploaded_file in uploaded_files:
            all_strings = []
            file_name = uploaded_file.name
            # 确保文件是DOCX文件
            if not file_name.lower().endswith('.docx'):
                continue
            try:
                paragraphs = self.read_doc_font(uploaded_file)
            except:
                raise ValueError("不支持的文件类型")
            text = []
            text_count = []
            titles = []
            for paragraph, font_size, font_bold in paragraphs:
                if len(text_count) > 0 and len(titles) > 0 and (0 < len(paragraph) <= title_long or font_bold):
                    text_count = []
                    titles = []
                if 0 < len(paragraph) <= title_long or font_bold:
                    titles.append(paragraph)
                elif len(paragraph) > title_long:
                    self.load_all_stopwords('./stopwords-master')
                    tags = jieba.analyse.extract_tags(paragraph, topK=5)
                    text.append(paragraph)
                    text_count.append(paragraph)

                if len(text) > 0:
                    titles_strings = " ".join(titles)
                    tags_strings = " ".join(tags)
                    all_strings.append((file_name, titles_strings, tags_strings, text))
                    text = []
        # 对文件进行切分
            wikipedia_strings = []
            for section in all_strings:
                wikipedia_strings.extend(split.split_strings_from_subsection_word(section, max_tokens=MAX_TOKENS))
            # 生成ids
            ids = [f"{file_name}_{i}" for i in range(1, len(wikipedia_strings) + 1)]
            docsearch = Chroma.from_texts(wikipedia_strings, self.embedding_function, collection_name="state-of-union",
                                          persist_directory=self.vector_folder, ids=ids)
        # return docsearch


    def search_upload_files_chroma(self, query):
        wikipedia_strings = []
        db3 = Chroma(embedding_function=self.embedding_function, collection_name="state-of-union",
                     persist_directory=self.vector_folder)
        answer = db3.similarity_search(query, k=15)
        return answer


    def get_ids(self):
        # wikipedia_strings = []
        db3 = Chroma(embedding_function=self.embedding_function, collection_name="state-of-union",
                     persist_directory=self.vector_folder)
        # wikipedia_strings = []
        # db3 = Chroma.from_texts(wikipedia_strings, self.embedding_function, collection_name="state-of-union", persist_directory=self.vector_folder)
        return db3.get()['ids']

    def delete_vector_database(self, title):
        title = title[0]
        # wikipedia_strings = []
        # db4 = Chroma.from_texts(wikipedia_strings, self.embedding_function, collection_name="state-of-union", persist_directory=self.vector_folder)
        db4 = Chroma(embedding_function=self.embedding_function, collection_name="state-of-union",
                     persist_directory=self.vector_folder)
        all_ids = self.get_ids()
        ids_to_delete = [id for id in all_ids if id.startswith(f"{title}_")]
        for id in ids_to_delete:
            db4.delete(id)
def extract_titles_from_ids(ids):
    # 使用set来确保title是唯一的
    titles = set()
    for id in ids:
        title = id.split("_")[0]  # 假设id的格式是"filename_number"
        titles.add(title)
    return list(titles)

def streamlit_sidebar_delete_database(FileChroma):
    all_ids = FileChroma.get_ids()
    titles = extract_titles_from_ids(all_ids)
    option = st.sidebar.multiselect('选择数据库中的文件并且删除', titles)
    button = st.sidebar.button(label='删除')
    if option and button:
        FileChroma.delete_vector_database(option)
        st.sidebar.success(f'你已经成功删除{option}', icon="✅")
    st.sidebar.caption(f'数据库中的文件:{titles}', )





