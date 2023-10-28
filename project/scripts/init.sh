#!/bin/bash

# Создание БД
sleep 10
airflow upgradedb
sleep 10

# Добавление user -- этот шаг рабочик
airflow users create \
          --username admin \
          --firstname admin \
          --lastname admin \
          --role Admin \
          --email admin@example.org \
          -p 12345

# Запуск шедулера и вебсервера
airflow scheduler & airflow webserver -p 8080