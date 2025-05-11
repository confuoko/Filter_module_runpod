import shutil
import time
import boto3
import os
from tempfile import NamedTemporaryFile

import requests
from dotenv import load_dotenv
from pydub import AudioSegment
import torch
from services.demux_service import do_clean_file, get_audio_duration


def main():
    """
        Принимает имя файла в хранилище s3 и флаг do_clean (обрабатывать или не обрабатывать).
        1. Скачивает из хранилища s3 аудио в папку temp.
        2. Оценивает длительность аудио и сохраняет это в БД.
        3. Если флаг do_clean=True - очищает и сохраняет новый файл в temp под именем _cleaned.wav.
           Если do_clean=False - сразу отправляет в Транскрибатор.
    """

    torch_variable = str(torch.cuda.is_available())
    if torch.cuda.is_available():
        print("✅ CUDA доступна (используется GPU)")
    else:
        print("❌ CUDA недоступна (используется CPU)")

    load_dotenv()

    # 1. Скачиваем аудио из хранилища s3 в папку temp
    file_key = "interview1.wav"
    do_clean = 'True'

    print(f"Получен запрос на обработку файла: {file_key}")
    print(f"Флаг обработки: {do_clean}")

    # Параметры хранилища s3
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    bucket_name = "whisper-audiotest"

    # Переменные для сервиса транскрибации
    TRANSCRIBATOR_AUTH_TOKEN = os.getenv("TRANSCRIBATOR_AUTH_TOKEN")
    TRANSCRIBATOR_QUEUE = os.getenv("TRANSCRIBATOR_QUEUE")
    headers = {
        'Content-Type': 'application/json',
        'Authorization': TRANSCRIBATOR_AUTH_TOKEN
    }

    s3 = boto3.client(
        's3',
        endpoint_url="http://storage.yandexcloud.net",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )

    file_obj = s3.get_object(Bucket=bucket_name, Key=file_key)
    temp_dir = os.path.join(os.getcwd(), 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    temp_file_path = os.path.join(temp_dir, file_key)
    demux_path = os.path.join(os.getcwd(), 'separated')
    demux_useful_path = os.path.join(demux_path, 'htdemucs')



    with open(temp_file_path, 'wb') as temp_file:
        temp_file.write(file_obj['Body'].read())

    print(f'📁 Файл сохранён во временную папку: {temp_file_path}')

    # === Определяем длительность аудиофайла ===
    duration = get_audio_duration(temp_file_path)

    # === Очищаем аудио если передан флаг do_clean ===
    if do_clean is True:
        print("🧠 Начинаю очистку аудио-файла...")
        start_time = time.time()
        cleaned_file_path = do_clean_file(temp_file_path)
        print(f"Очищенный файл сохранён в директорию: {cleaned_file_path}")


        cleaned_file_name = os.path.basename(cleaned_file_path)
        print(f"☁️ Файл получит имя: {cleaned_file_name}")

        duration = round(time.time() - start_time, 2)  # Время в секундах с округлением
        print(f"✅ Готово за {duration} секунд.")

        # === загружаем очищенное аудио в s3 ===
        s3.upload_file(
            Filename=cleaned_file_path,
            Bucket=bucket_name,
            Key=cleaned_file_name
        )
        print(f"☁️ Файл {cleaned_file_name} загружен в S3 (в корень бакета)")

        # === Удаляем временные файлы ===
        os.remove(cleaned_file_path)
        os.remove(temp_file_path)
        shutil.rmtree(demux_useful_path)
        print("🧹 Временные файлы удалены.")

        # Отправляем в Транскрибатор очищенную аудио
        data = {
            'input': {"file_key": cleaned_file_name}
        }

        response = requests.post(f'https://api.runpod.ai/v2/{TRANSCRIBATOR_QUEUE}/run', headers=headers, json=data)

        print(f"Отправляем запрос к сервису Транскрибации. Ответ: {response.json()}")


    else:
        # если флаг не передан - сразу направляет запрос в транскрибатор
        data = {
            'input': {"file_key": file_key}
        }
        response = requests.post(f'https://api.runpod.ai/v2/{TRANSCRIBATOR_QUEUE}/run', headers=headers, json=data)

        print(f"Ваша аудиозапись была сраз направлена в сервис Транскрибации. Ответ: {response.json()}")
    # сохраняем длительность файла в БД



if __name__ == "__main__":
    main()