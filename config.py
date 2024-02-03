import os

# Получаем токен из переменной окружения
TOKEN = os.getenv('TOKEN')

# Проверяем, что токен был установлен
if TOKEN is None:
    raise ValueError("Не задан TOKEN. Укажите токен в переменной окружения TOKEN.")