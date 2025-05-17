
import os
import shutil

import psycopg2
import torchaudio
from demucs.audio import AudioFile
from demucs.pretrained import get_model
from demucs.apply import apply_model
from typing import Optional

from dotenv import load_dotenv
from pydub import AudioSegment

from services.model_loader import load_demucs_model


import os
import torchaudio
from typing import Optional
from demucs.audio import AudioFile
from demucs.apply import apply_model

import os
from typing import Optional


def do_clean_file(temp_file_path: str) -> Optional[str]:
    """
    Обрабатывает аудиофайл с помощью Demucs через CLI и сохраняет голосовую дорожку.

    Args:
        temp_file_path (str): Путь к исходному аудиофайлу.

    Returns:
        str: Путь к очищенному аудиофайлу или None в случае ошибки.
    """
    try:


        print(torchaudio.list_audio_backends())
        # Директория и имя файла
        temp_dir = os.path.dirname(temp_file_path)
        file_name = os.path.basename(temp_file_path)
        cleaned_file_name = f"{os.path.splitext(file_name)[0]}_cleaned.wav"
        cleaned_file_path = os.path.join(temp_dir, cleaned_file_name)

        # Демпс: сохраняет результаты в директорию "separated"
        redirect = "> nul" if os.name == "nt" else "> /dev/null"

        # Выполняем команду через CLI
        print(f"Запуск Demucs для {temp_file_path}...")
        os.system(f"python -m demucs --two-stems=vocals {temp_file_path} {redirect}")

        # Путь к результату
        demucs_out = os.path.join("separated", "htdemucs", os.path.splitext(file_name)[0], "vocals.wav")

        # Проверяем, существует ли результат
        if not os.path.exists(demucs_out):
            print(f"Ошибка: Результат не найден по пути {demucs_out}")
            return None

        # Перемещаем результат в `temp` с новым именем
        os.rename(demucs_out, cleaned_file_path)
        print(f"✅ Голосовая дорожка успешно сохранена как {cleaned_file_path}")
        return cleaned_file_path

    except Exception as e:
        print(f"Ошибка при очистке файла: {e}")
        return None


def get_audio_duration(file_path: str) -> float:
    """
    Определяет длительность аудиофайла в секундах.

    Args:
        file_path (str): Путь к аудиофайлу.

    Returns:
        float: Длительность аудиофайла в мс.
    """
    try:
        audio = AudioSegment.from_file(file_path)
        duration = len(audio)  # Длительность в мили секундах
        print(f"⏱️ Длительность аудиофайла: {duration} мс")
        return duration
    except Exception as e:
        print(f"Ошибка при определении длительности аудио: {e}")
        return -1


def update_cleaned_record(record_id, audio_length, name_file_cleaned):
    # Загрузка переменных из .env
    load_dotenv()

    # Получаем connection string
    connection_string = os.getenv('DATABASE_URL')

    try:
        # Подключение к БД
        connection = psycopg2.connect(connection_string)
        print("Успешное подключение к БД")
        cursor = connection.cursor()

        # Обновление нескольких полей
        update_query = """
            UPDATE myusers_callitem
            SET audio_length = %s,
                name_file_cleaned = %s
            WHERE id = %s;
        """
        cursor.execute(update_query, (audio_length, name_file_cleaned, record_id))
        connection.commit()

        print(f"Запись с id={record_id} успешно обновлена.")

    except Exception as e:
        print(f"Ошибка при обновлении записи: {e}")

    finally:
        # Закрытие соединения
        if connection:
            cursor.close()
            connection.close()

def update_record(record_id, audio_length):
    # Загрузка переменных из .env
    load_dotenv()

    # Получаем connection string
    connection_string = os.getenv('DATABASE_URL')

    try:
        # Подключение к БД
        connection = psycopg2.connect(connection_string)
        print("Успешное подключение к БД")
        cursor = connection.cursor()

        # Обновление нескольких полей
        update_query = """
            UPDATE myusers_callitem
            SET audio_length = %s
            WHERE id = %s;
        """
        cursor.execute(update_query, (audio_length, record_id))
        connection.commit()

        print(f"Запись с id={record_id} успешно обновлена.")

    except Exception as e:
        print(f"Ошибка при обновлении записи: {e}")

    finally:
        # Закрытие соединения
        if connection:
            cursor.close()
            connection.close()