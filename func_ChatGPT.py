#!/usr/bin/env python
# coding: utf-8

# In[1]:


from openai import OpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI


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

api_key = config.chat_gpt_api_key
os.environ['OPENAI_API_KEY'] = api_key


server = config.server
port = config.port
database = config.database
user_name = config.login
password = config.password


# In[ ]:





# In[ ]:


def get_db_connection(server, database, user_name, password, port='3306'):
    mysql_uri = 'mysql+pymysql://'+user_name+':'+password+'@'+server+ ':'+ port +'/'+database
    db = SQLDatabase.from_uri(mysql_uri)
    
    return db


# In[ ]:


def get_schema(_):
    db = get_db_connection(server, database, user_name, password, port)
    return db.get_table_info()


# In[ ]:


def get_sql_chain(user_question, model_name='gpt-3.5-turbo'):
    template = """Based on the table schema below, write a SQL query that would answer the user's question:
    {schema}

    Question: {question}
    SQL Query:"""

    prompt = ChatPromptTemplate.from_template(template)
    
    
    llm = ChatOpenAI(model_name=model_name)

    sql_chain = (
        RunnablePassthrough.assign(schema=get_schema)
       | prompt
        | llm.bind(stop="\nSQLResult:")
        | StrOutputParser()
    )
    
    return sql_chain.invoke({"question": user_question})


# In[ ]:


def run_query(query):
    db = get_db_connection(server, database, user_name, password, port)
    return db.run(query)


# In[ ]:


def get_db_answer(user_question, model_name='gpt-3.5-turbo'):
    
    llm = ChatOpenAI(model_name='gpt-3.5-turbo')
    
    template = """Based on the table schema below, write a SQL query that would answer the user's question:
    {schema}

    Question: {question}
    SQL Query:"""

    prompt = ChatPromptTemplate.from_template(template)
    

    sql_chain = (
        RunnablePassthrough.assign(schema=get_schema)
       | prompt
        | llm.bind(stop="\nSQLResult:")
        | StrOutputParser()
    )
    
    llm2 = ChatOpenAI(model_name=model_name)
    template2 = """Based on the table schema below, question, sql query, and sql response, 
    write a natural language response on russian language:
    {schema}

    Question: {question}
    SQL Query: {query}
    SQL Response: {response}"""

    prompt2 = ChatPromptTemplate.from_template(template2)
    
    
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




