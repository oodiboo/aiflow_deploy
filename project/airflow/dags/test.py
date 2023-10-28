# Необходимые импорты
from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.email_operator import EmailOperator
from airflow.operators.python_operator import PythonOperator

import pandas as pd
import sqlite3
# import psycopg2

# CON = psycopg2.connect(dbname='airflow')
CON = sqlite3.connect('example.db')

# Повторим предыдущий код с небольшим измененеием, теперь файлы 
# записываются на диск, а не передаются в потоке исполнения
# это особенность рабоыт Airflow которую мы обсудим позднее
# **context это необязательный аргумент, но мы будем его использовать далее
# это мощный инструмент который позволит нам писать идемпотентные скрипты

def extract_data(url, tmp_file, **context):
    pd.read_csv(url).to_csv(tmp_file) # Изменение to_csv, запишем данные в файл


def transform_data(group, agreg, tmp_file, tmp_agg_file, **context):
    data = pd.read_csv(tmp_file) # Изменение read_csv
    data.groupby(group).agg(agreg).reset_index().to_csv(tmp_agg_file) # Изменение to_csv, запишем данные в файл
 

def load_data(tmp_file, table_name, conn=CON, **context):
    data = pd.read_csv(tmp_file)# Изменение read_csv, прочитаем данные из файла
    data["insert_time"] = pd.to_datetime("now")
    data.to_sql(table_name, conn, if_exists='replace', index=False)

# Создаем DAG(контейнер) в который поместим наши задачи
# Для DAG-а характерны нужно задать следующие обязательные атрибуты
# - Уникальное имя
# - Интервал запусков
# - Начальная точка запуска

dag = DAG(dag_id='dag', # Имя нашего дага, уникальное
         default_args={'owner': 'airflow'}, # Список необязательных аргументов
         schedule_interval='@daily', # Интервал запусков, в данном случае 1 раз в день 24:00
         start_date=days_ago(1) # Начальная точка запуска, это с какого моменты мы бы хотели чтобы скрипт начал исполняться (далее разберем это подробнее)
    )

 
# Создадим задачу которая будет запускать питон функция
# Все именно так, создаем код для запуска другого кода
extract_data = PythonOperator(
    task_id='extract_data', # Имя задачи внутри Dag
    dag=dag,    
    python_callable=extract_data, # Запускаемая Python функция, описана выше
        
    # Чтобы передать аргументы в нашу функцию 
    # их следует передавать через следующий код
    op_kwargs={
        'url': 'https://raw.githubusercontent.com/dm-novikov/stepik_airflow_course/main/data/data.csv',
        'tmp_file': '/tmp/file.csv'}
    )

transform_data = PythonOperator(
    task_id='transform_data',
    dag=dag,
    python_callable=transform_data,
    op_kwargs={
        'tmp_file': '/tmp/file.csv',
        'tmp_agg_file': '/tmp/file_agg.csv',
        'group': ['A', 'B', 'C'],
        'agreg': {"D": sum}}
    )

load_data = PythonOperator(
    task_id='load_data',
    dag=dag,    
    python_callable=load_data,
    op_kwargs={
        'tmp_file': '/tmp/file_agg.csv',
        'table_name': 'table'}
    )

# Создадим задачу которая будет отправлять файл на почту
# НЕОБЯЗАТЕЛЬНЫЙ ШАГ (не поддерживает в курсе, вы можете самостоятельно с этим разобраться)
email_op = EmailOperator(
   task_id='send_email',
   dag=dag,   
   to=["wrknekrasov@gmail.com","wrknekrasov@yandex.ru"],
   subject="Test Email Please Ignore",
   html_content=None,
   files=['/tmp/file_agg.csv']
)

# Создадим порядок выполнения задач
# В данном случае 2 задачи буудт последователньы и ещё 2 парараллельны
extract_data >> transform_data >> [load_data, email_op]