#!/usr/bin/env python
# coding: utf-8

# In[1]:


from openai import OpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from IPython.display import Audio
from pathlib import Path

import mysql.connector as connection
import pandas as pd
import warnings
from datetime import datetime
import os
import pyodbc
import warnings
import requests

from func_MySQL_DB import *
import config 

# забираем токен chatGPT из файла config
api_key = config.chat_gpt_api_key
os.environ['OPENAI_API_KEY'] = api_key

# забираем параметры подключения к БД
server = config.server
port = config.port
database = config.database
user_name = config.login
password = config.password


# In[ ]:





# In[ ]:


# создаем функцию для подключения к Базе данных
# она принимает на входе
# server - адрес сервера
# port - номер порта(опционально), по умолчанию используем 3306
# database - название базы данных
# user_name - логин
# password - пароль

def get_db_connection(server, database, user_name, password, port='3306'):
    mysql_uri = 'mysql+pymysql://'+user_name+':'+password+'@'+server+ ':'+ port +'/'+database
    db = SQLDatabase.from_uri(mysql_uri)
    
    return db


# In[ ]:


# получаем схему Базы данных
# функция внутри себя создает подключение с нашей БД с данными
def get_schema(_):
    db = get_db_connection(server, database, user_name, password, port)
    return db.get_table_info()


# In[ ]:


# создаем функцию, чтобы на основе человеческого вопроса создать SQL запрос
# на входе она принимает
# user_question - обычный вопрос человеческим языком, касающийся данных в Базе
# model_name - название модели GPT(опционально). По умолчанию используем - gpt-3.5-turbo
def get_sql_chain(user_question, model_name='gpt-3.5-turbo'):
#     создаем шаблон запроса, чтобы chatGPT понял, что от него хотят
    template = """Based on the table schema below, write a SQL query that would answer the user's question:
    {schema}

    Question: {question}
    SQL Query:"""
# формируем Объект promt
    prompt = ChatPromptTemplate.from_template(template)
    
# создаем объект Языковой модели, чтобы она преобразовала человечексий вопрос в SQL запрос
    llm = ChatOpenAI(model_name=model_name)
    
# создаем звено для получения ответа на человеческий вопрос
# get_schema - запрашиваем схему БД
# prompt - отправляем шаблон запроса
# llm.bind(stop="\nSQLResult:") - забираем ответ после этих слов
# StrOutputParser() - выводим ответ на печать

    sql_chain = (
        RunnablePassthrough.assign(schema=get_schema)
       | prompt
        | llm.bind(stop="\nSQLResult:")
        | StrOutputParser()
    )
    
# sql_chain.invoke - отправляем вопрос и получаем ответ   
    return sql_chain.invoke({"question": user_question})


# In[ ]:


# создаем функцию, которая получает SQL запрос и отправляет его в нашу БД
# SQL запрос формируется автоматически из человеческого запроса
def run_query(query):
    db = get_db_connection(server, database, user_name, password, port)
    return db.run(query)


# In[ ]:


# создаем функцию для получения человеческого ответа на вопрос, касающийся БД
# на вход она принимает вопрос в обычном человеческом виде
# отправляет его в БД -> получает SQL запрос ->
# -> отправляет его в БД -> получает ответ от БД ->
# -> интерпретирует его в обычную человеческий ответ по данным из БД

def get_db_answer(user_question, model_name='gpt-3.5-turbo'):
    
#     создаем языковую модель на SQL запрос
    llm = ChatOpenAI(model_name='gpt-3.5-turbo')
#   создаем шаблон запроса, чтобы chatGPT понял, что от него хотят  
    template = """Based on the table schema below, write a SQL query that would answer the user's question:
    {schema}

    Question: {question}
    SQL Query:"""
# формируем Объект promt
    prompt = ChatPromptTemplate.from_template(template)
    
# создаем звено для получения ответа на человеческий вопрос
# get_schema - запрашиваем схему БД
# prompt - отправляем шаблон запроса
# llm.bind(stop="\nSQLResult:") - забираем ответ после этих слов
# StrOutputParser() - выводим ответ на печать

    sql_chain = (
        RunnablePassthrough.assign(schema=get_schema)
       | prompt
        | llm.bind(stop="\nSQLResult:")
        | StrOutputParser()
    )
    
#     создаем языковую модель для интерпритации данных из БД    
    llm2 = ChatOpenAI(model_name=model_name)
    
#   создаем шаблон запроса, чтобы chatGPT понял, что от него хотят 
    template2 = """Based on the table schema below, question, sql query, and sql response, 
    write a natural language response on russian language:
    {schema}

    Question: {question}
    SQL Query: {query}
    SQL Response: {response}"""
# формируем Объект promt
    prompt2 = ChatPromptTemplate.from_template(template2)
    
# создаем полную цепочку из запросов
# на первом шаге вызываем языковую модель для того, чтобы превратить человеческий вопрос в SQL запрос ->
# -> В ответ на SQL запрос мы получаем ответ от БД ->
# -> его берет другая языковая модель и интерпретирует человеческими словами

    full_chain = (
    RunnablePassthrough.assign(query=sql_chain).assign(
        schema=get_schema,
        response=lambda vars: run_query(vars["query"]),)
    | prompt2
    | llm2
    )
    
    answer = full_chain.invoke({"question": user_question})
    
    return answer.content


# In[ ]:


def get_voice_gpt(text, file_path):
    client = OpenAI()
    # create api request 
    with client.audio.speech.with_streaming_response.create(
      model="tts-1",
      voice="onyx",
      input=text
    ) as response:
        response.stream_to_file(file_path)

