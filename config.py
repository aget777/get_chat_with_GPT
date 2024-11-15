#!/usr/bin/env python
# coding: utf-8

# In[7]:


import os

# указываем путь к папке, в которой храняться файлы с доступами
file_path = os.path.join(os.getcwd(), 'cred')


# In[ ]:


# указываем название файла с токеном для chatGPT
gpt_file_name = 'chat_gpt_api_token_igronik.txt'
# сохраняем токен в отдельную переменную
chat_gpt_api_key = open(os.path.join(file_path, gpt_file_name), encoding='utf-8').read()


# In[23]:


# указываем название файла с доступами к БД 
# там прописаны след. доступы
# server - адрес сервера
# port - номер порта(опционально), по умолчанию используем 3306
# database - название базы данных
# login - логин
# password - пароль

db_file_name = 'db_creds.txt'
# забираем доступы из файла и формируем список (каждый элемнет списка - это один параметр server, port  и тд.)
db_creds_list = open(os.path.join(file_path, db_file_name), encoding='utf-8').read().split('\n')

# создаем пустой словарь, чтобы преобразовать список в нормальный набор доступов
db_creds_dict = {}
for name in db_creds_list:
#     достаем каждый отдельный элемнт списка
# убираем кавычки / разделяем строку по разделителю / получаем список из 2-х элементов 
# первый элемент - это ключ / второй элемент - это значение
    tmp_lst = name.replace("'", "").split(' = ')
    db_creds_dict[tmp_lst[0]] = tmp_lst[1]

# разбираем словарь на переменные
server = db_creds_dict['server']
port = db_creds_dict['port']
database = db_creds_dict['database']
login = db_creds_dict['login']
password = db_creds_dict['passw']


# In[ ]:





# In[ ]:




