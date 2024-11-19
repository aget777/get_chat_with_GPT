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
from datetime import datetime, timedelta
import os
import pyodbc
import warnings
import requests
import json
 


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


# создаем функцию для преобразования текст в голос
# на входе она принимает 
# - text - текст для озвучки
# - file_path - путь для сохранения файла вместе с его названием
# - model - указываем модель (по умолчанию 'tts-1')
# - voice - указываем название голоса для озвучки (по умолчанию 'onyx')
# на выходе сохраняем озвученный файл в папку
def get_voice_gpt(text, file_path, model='tts-1', voice='onyx'):
#     создаем объект для подключения к чату
    client = OpenAI()
# создаем АПИ запрос для озвучки
    with client.audio.speech.with_streaming_response.create(
      model=model,
      voice=voice,
      input=text
    ) as response:
        response.stream_to_file(file_path)


# In[ ]:


def get_simple_chat(dialog_list, prompt, model='gpt-3.5-turbo'):
    client = OpenAI(api_key=api_key)
    
    dialog_dict = {}
    message = [{"role": "user", "content": prompt}]

    chat_completion = client.chat.completions.create(
    model = model,
    messages=message,
    temperature=0,
    )
    
    answer = chat_completion.choices[0].message.content
    
    dialog_dict['question'] = prompt
    dialog_dict['answer'] = answer
    
    dialog_list.append(dialog_dict)

    print(f'question:{prompt}')

    return answer #chat_completion.choices[0].message.content


# In[ ]:


# создаем функцию, чтобы получить список дат для запроса расхода Токенов chatGPT
# на вход она принимает
# - final_path - путь к файлу (вместе с названием), в котором храняться записи расходов по дням
# - если такого файла нет, ничего страшного
# - start_date - дата начала загрузки данных
# Скрипт проверяет - существует файл с данными или нет -> если сущесвует, то максимальная дата в эксель файле
#  больше или равна start_date -> если да, то используем дату изэксель файла -> иначе start_date
def get_dates_list(final_path, start_date='2024-01-01'):
    dates_list = [] # создаем список для сохранения каждой отдельной дате в запрошенном периоде
#     file_path = os.getcwd()
#     file_name = 'chat_gpt_costs.xlsx'
#     final_path = os.path.join(file_path, file_name)


    date_format = '%Y-%m-%d'
#     если эксель файла с прошлыми данными нет, то ничего не делаем и датой начала будет считаться переданная дата
    if not os.path.exists(final_path):
        pass
    else:
        df = pd.read_excel(final_path) #   если файл эксель существует, то забираем его содержимое в датаФрейм

        if not df.empty:   
# если датаФрейм не пустой, то забираем из него максимальную дату, она будет считаться датой начала загрузки
            start_date = str(df['date'].max())

# приводим формат даты к нужному виду        
    start_date = datetime.strptime(start_date, date_format)
# конечной дотой загрузки считает сегодня минус 1 день
    end_date = datetime.now() #.strftime(date_format) 
# считаем кол-во дней в периоде
    count_days = (end_date - start_date).days
# проходим циклом по кол-ву дней и формируем список дат для загрузки   
    for i in range(count_days-1):
        days = i +1
        current_date = (start_date + timedelta(days=days)).strftime(date_format)
        dates_list.append(current_date)
# возвращаем список дат        
    return dates_list


# In[ ]:


# создаем функцию, чтобы распарсить ответ chatGPT с информацией о использовании токенов
# для каждого отдельного запроса
# на вход принимаем след. параметры:
# usage_data - ответ АПИ chatGPT об использованных токенах
# date - дата, к которой относится эта информация
def get_usage_chat_gpt(usage_data, date):
    
# создаем список названий полей для датаФрейма
    columns_list = ['date', 'model', 'input_tokens', 'output_tokens', 'chars']
    
# создаем временный словарь, в который сохраним распарсенные данные по каждому запросу
    tmp_dict = {}
# chatGPT предоставляет информацию отдельно по каждому типу использования
# data - это обычный чат (текстовый вопрос-ответ)
# tts_api_data - это озвучивание голосом переданного текста
# есть еще вот такие ft_data / dalle_api_data / whisper_api_data (пока что не понятно, к чему они относятся)
# парсим данные по обычному чату

    if 'data' in usage_data:
#  через цикл проходим по каждому отдельному сообщению
        for i in range(len(usage_data['data'])):
#  создаем датаФрейм для сохранения данных
            tmp_df = pd.DataFrame(columns=columns_list)
#  забираем инфо о кол-ве токенов на обработку вопроса
            tmp_df.loc[0, 'input_tokens'] = usage_data['data'][i]['n_context_tokens_total']
# забираем инфо о кол-ве токенов на обработку ответа
            tmp_df.loc[0, 'output_tokens'] = usage_data['data'][i]['n_generated_tokens_total']
# забираем метку времени (ее будем использовать, как ключ для нашего словаря)
            timestamp = usage_data['data'][i]['aggregation_timestamp']
#             date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
# наша функция приняла Дату, передаем ее в датаФрейм
            tmp_df.loc[0, 'date'] = date
# забираем инфо о модели chatGPT, которая использовалась в запросе
            tmp_df.loc[0, 'model'] = usage_data['data'][i]['snapshot_id']
# добавляем датаФрейм в словарь
            tmp_dict[str(timestamp)] = tmp_df
    
# парсим данные об использовании Голосовой модели
    if 'tts_api_data' in usage_data:
#  через цикл проходим по каждому отдельному сообщению
        for i in range(len(usage_data['tts_api_data'])):
#  создаем датаФрейм для сохранения данных
            tmp_df = pd.DataFrame(columns=columns_list)
# забираем кол-во символов в тексте, которые были переданы для озвучивания
            tmp_df.loc[0, 'chars'] = usage_data['tts_api_data'][i]['num_characters']
# забираем метку времени (ее будем использовать, как ключ для нашего словаря)
            timestamp = usage_data['tts_api_data'][i]['timestamp']
#             date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
# наша функция приняла Дату, передаем ее в датаФрейм
            tmp_df.loc[0, 'date'] = date
# забираем инфо о модели chatGPT, которая использовалась в запросе
            tmp_df.loc[0, 'model'] = usage_data['tts_api_data'][i]['model_id']
# добавляем датаФрейм в словарь
            tmp_dict[str(timestamp)] = tmp_df
# если за какую-то дату НЕ было данных, мы получим пустой словарь
# чтобы не было ошибок на след. этапах работы с данными,
# заполним словарь за эту даты нулями
    if not tmp_dict:
        tmp_df = pd.DataFrame({'date': date, 'model': '', 'input_tokens':0.0, 'output_tokens':0.0, 'chars':0.0}, index=[0])
        tmp_dict[str(date)] = tmp_df
# объединяем словарь в один датаФрейм и возвращаем его
    df = pd.concat(tmp_dict, ignore_index=True)
    
    return df


# In[ ]:


# создаем функцию, чтобы внутри датаФрейма расчитать потраченные деньги, на каждое отдельное сообщение
# изначально chatGPT НЕ отдает информацию о расходах.
# Поэтому файл со стоимостью был создан руками
# в данной функции мы принимаем строку из датаФрейма, в который уже добавлены расценки
# цены даются за расход 1000 токенов
# считаем расходы на входящие и исходящие сообщения и на озвучку
# на выходе возвращаем список
def get_costs(row):
    input_costs = 0.0
    output_costs = 0.0
    audio_costs = 0.0
    if row['input_tokens'] != '':
        input_costs = (row['input_tokens']/1000) * row['1k input tokens']
    if row['output_tokens'] != '':
        output_costs = (row['output_tokens']/1000) * row['1k output tokens']
    if row['chars'] != '':
        audio_costs = (row['chars']/1000) * row['1k characters']
        
    return [input_costs, output_costs, audio_costs]


# In[ ]:


# создаем функцию, чтобы к существующему датаФрейму добавить информацию о стоимости запросов
# и посчитать итоговые общие расходы
# изначально chatGPT НЕ отдает информацию о расходах.
# Поэтому файл со стоимостью был создан руками
# на вход функция принимает
# - df - датаФрейм, в который добавляем данные
# - final_path - путь к файлу с информацией о стоимости запросов
def get_costs_by_row(df, final_path):
#     file_path = os.getcwd()
#     file_name = 'chatGPT_pricing_18112024.xlsx'

#     final_path = os.path.join(file_path, file_name)
# забираем в датаФрейм данные о стоимости запросов
    df_pricing = pd.read_excel(final_path)
    df_pricing = df_pricing.fillna('')
# через левое соединение добавляем к нашему датаФрейму расценки
    df_costs = df.merge(df_pricing, how='left', left_on='model', right_on=['model'])
# считаем итоговую стоимость для каждого типа запросов
    df_costs['input_costs'] = df_costs.apply(lambda row: get_costs(row)[0], axis=1)
    df_costs['output_costs'] = df_costs.apply(lambda row: get_costs(row)[1], axis=1)
    df_costs['audio_costs'] = df_costs.apply(lambda row: get_costs(row)[2], axis=1)
#  считаем Общие расходы на запрос
    df_costs['total_costs'] = df_costs['input_costs'] + df_costs['output_costs'] + df_costs['audio_costs']
# возвращаем дополненный датаФрейм    
    return df_costs


# In[ ]:


# создаем итоговую функцию для получения стоимости использования chatGPT
# с расчетом по каждому запросу по дням 
# с сохранением в эксель файл
# функция на входе принимает
# - usage_path - путь к эксель файлу (вместе с названием), в котором хранятся прошлые 
# сохраненные данные об использовании, если такого файла нет, то он будет создан
# - pricing_path - путь к файлу (вместе с названием), в котором хранятся расценки на использование chatGPT
# - start_date - дата начала загрузки НЕ включительно в формате YYYY-mm-dd
def get_chat_gpt_costs(usage_path, pricing_path, start_date, api_key=api_key):
    
# забираем АПИ ключ
#     api_key = api_key
# содаем временный словарь для сохранения данных
    tmp_dict = {}
    
    # Заголовки для запроса
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # URL для получения данных о расходах
    base_url = "https://api.openai.com/v1/usage?"
# забираем список дат для запроса статистики в chatGPT
# - usage_path - передаем путь к файлу эксель вместе с его названием (даже если его нет)
# - start_date - передаем дату начала загрузки
    dates_lst = get_dates_list(usage_path, start_date)
# проходим через цикл по списку дат        
    for date in dates_lst:
# формируем URL для запроса по АПИ в chatGPT
        url = base_url + f'date={date}'
        # Отправляем GET-запрос
        response = requests.get(url, headers=headers)
        # Проверяем успешность запроса
        if response.status_code == 200:
#  забираем содержимое ответа и передаем вместе с датой в нашу функцию для парсинга данных
            usage_data = response.json()
            tmp_df = get_usage_chat_gpt(usage_data, date)
# сохраняем в словарь под конкретной датой полученный датаФрейм
            tmp_dict[str(date)] = tmp_df

# получаем словарь, гда на каждую дату находится датаФрейм с распарсенными данными
# если данных нет, то в эту дату стоят 0
# преобразуем словарь в датаФрейм
    df = pd.concat(tmp_dict, ignore_index=True)
    df = df.fillna('')
#     передаем датаФрейм и путь к файлу с расценками, для расчета итоговых расходов
    df = get_costs_by_row(df, pricing_path)


# проверяем наличие файла эксель с прошлыми записями расходов
# если такой файл есть, то 
# - достаем из него данные в датаФрейм
# - добавляем к этому датаФрейму данные за новый период
    if os.path.exists(usage_path):
        base_data = pd.read_excel(usage_path)
        df = pd.concat([base_data, df], ignore_index=True)
        
# сохраняем в итоговый эксель файл
    df.to_excel(usage_path)

# выводим на печать общую информацию
    min_date = df['date'].min()
    max_date = df['date'].max()
    total_costs = df['total_costs'].sum().round(2)

    return print(f'Расходы за период с {min_date} по {max_date} в размере {total_costs} usd сохранены в файл')


# In[ ]:


# Получить остаток на счете
# берем сумму пополнений из собственного файла эксель
# берем сумму расходов из эксель файла
# вычитам из первого второе, подучаем остаток

def get_current_balance(usage_path, biling_path):
    df_balance = pd.read_excel(biling_path)
    total_amount = df_balance['amount (usd)'].sum()
    
    df_costs = pd.read_excel(usage_path)
    df_costs['total_costs'] = df_costs['total_costs'].astype('float')
    total_costs = df_costs['total_costs'].sum()
    
    current_balance = (total_amount - total_costs).round(2)
    print(f'Current balance: {current_balance}')
    
    return current_balance

