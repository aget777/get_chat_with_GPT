#!/usr/bin/env python
# coding: utf-8

# In[2]:


import mysql.connector as connection
import pandas as pd
import warnings
import sqlalchemy 
import config


# In[3]:


# забираем параметры подключения к БД
server = config.server
port = config.port
database = config.database
user_name = config.login
password = config.password


# In[ ]:


# функция для создания новой таблицы в MySQL
# Принимает на вход 
# server - адрес сервера БЕЗ порта / database - название базы данных
# user_name - имя пользователя / password - пароль
# table_name_db - название таблицы
# db_vars_list - список названий полей с указанием типов данных db_vars_list = ['ind INT','campaign_id INT','campaign_name VARCHAR(100)']
# port - порт указан по умолчанию, можно заменить на другой

def create_mysql_table(server, database, user_name, password, table_name_db, db_vars_list, port='3306'):
    try:
        # устанавливаем соединение с БД
        conn = connection.connect(host=server, port=port, database=database, user=user_name, password=password)
        
        if conn:
            print('Connection success')
            
        cursor = conn.cursor()
        # преобразуем список в строку
        vars_str = ', '.join(db_vars_list)
        # формируем SQL запрос на создание новой таблицы
        sql = f"""
            CREATE TABLE {table_name_db} 
            ({vars_str})
            """
        # отправляем запрос на исполнение
        cursor.execute(sql)
        print(f'Table created {table_name_db}')
        # закрываем соединение
        conn.close()
    except Exception as e:
        # если ошибка, то закрываем соединение и выводим название ошибки
        conn.close()
        print(str(e))


# In[ ]:


# создаем функцию для получения ответа от БД в виде датаФрейма
# Принимает на вход 
# server - адрес сервера БЕЗ порта / database - название базы данных
# user_name - имя пользователя / password - пароль
# query - полный SQL запрос на исполнение
# port - порт указан по умолчанию, можно заменить на другой
def get_dataframe(server, database, user_name, password, query, port='3306'):
    try:
        # устанавливаем соединение с БД
        conn = connection.connect(host=server, port=port, database=database, user=user_name, password=password)
        
        if conn:
            print('Connection success')
        # если в конце запроса отсутствуют закрывающие ; то добавляем их
        if ';' not in query:
            query += ';'
        df = pd.read_sql(query, conn)
        conn.close()
        
        return df
        
    except Exception as e:
        conn.close()
        print(str(e))


# In[1]:


# создаем функцию для загрузки датаФрейма в БД
# Принимает на вход 
# server - адрес сервера БЕЗ порта / database - название базы данных
# user_name - имя пользователя / password - пароль
# table_name_db - название таблицы / df - датаФрейм для загрузки
# port - порт указан по умолчанию, можно заменить на другой
def upload_data_to_db(server, database, user_name, password, table_name_db, df, port='3306'):
    try:
        # приводим название таблицы к нижнему регистру
        table_name_db = table_name_db.lower()
        # создаем соединение с БД
        engine = sqlalchemy.create_engine(f'mysql+mysqlconnector://{user_name}:{password}@{server}:{port}/{database}')
        # загружаем датаФрейм
        df.to_sql(name=table_name_db, con=engine, if_exists = 'replace', index=False)
        # закрываем соединение
        engine.dispose()
        print(f'Data added to {table_name_db} table')
        
    except Exception as e:
        engine.dispose()
        print(str(e))


# In[ ]:


# функция для создания новой таблицы в MySQL
# Принимает на вход 
# server - адрес сервера БЕЗ порта / database - название базы данных
# user_name - имя пользователя / password - пароль
# table_name_db - название таблицы
# db_vars_list - список названий полей с указанием типов данных db_vars_list = ['ind INT','campaign_id INT','campaign_name VARCHAR(100)']
# port - порт указан по умолчанию, можно заменить на другой

def delete_mysql_table(server, database, user_name, password, table_name_db, port='3306'):
    try:
        # устанавливаем соединение с БД
        conn = connection.connect(host=server, port=port, database=database, user=user_name, password=password)
        
        if conn:
            print('Connection success')
            
        cursor = conn.cursor()
        
        # формируем SQL запрос на создание новой таблицы
        sql = f"""
            DROP TABLE {table_name_db} 
             """
        # отправляем запрос на исполнение
        cursor.execute(sql)
        print(f'Table deleted {table_name_db}')
        # закрываем соединение
        conn.close()
    except Exception as e:
        # если ошибка, то закрываем соединение и выводим название ошибки
        conn.close()
        print(str(e))


# In[ ]:


# функция для изменения типа данных по определенному полю
# Принимает на вход 
# server - адрес сервера БЕЗ порта / database - название базы данных
# user_name - имя пользователя / password - пароль
# table_name_db - название таблицы / column_name - название поля, в котором нужно изменить тип данных
# data_type - тип данных, который нужно установить INT, VARCHAR(100), DATE
# port - порт указан по умолчанию, можно заменить на другой
def update_column_type(server, database, user_name, password, table_name_db, column_name, data_type, port='3306'):
    try:
        # приводим название таблицы к нижнему регистру
        table_name_db = table_name_db.lower()
        # устанавливаем соединение с БД
        conn = connection.connect(host=server, port=port, database=database, user=user_name, password=password)
        
        if conn:
            print('Connection success')
        cursor = conn.cursor()
        
        # формируем SQL запрос на создание новой таблицы
        sql = f'ALTER TABLE {table_name_db} MODIFY COLUMN `{column_name}` {data_type} NULL;'
        
        # отправляем запрос на исполнение
        cursor.execute(sql)
        print(f'Column {column_name} has chanched: type - {data_type} / table - {table_name_db}')
        # закрываем соединение
        conn.close()
    except Exception as e:
        # если ошибка, то закрываем соединение и выводим название ошибки
        conn.close()
        print(str(e))


# In[ ]:




