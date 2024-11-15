#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import matplotlib.pyplot as plt


# In[ ]:


# создаем визуализацию в виде гистограммы
# column_1 - это параметр
# column_2 - это показатель

def get_visual_bar(df, column_1, column_2, rotation=45):
    plt.bar(df[column_1], df[column_2])
    plt.xticks(rotation=rotation)
    plt.show()

