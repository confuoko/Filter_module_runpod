import os
import torch
from demucs.pretrained import get_model
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()


def load_demucs_model(model_name="htdemucs"):
    """
    Загрузка модели Demucs. Если модель не найдена локально, скачивается из интернета.

    Args:
        model_name (str): Имя модели Demucs (например, "htdemucs").

    Returns:
        torch.nn.Module: Загруженная модель Demucs.
    """
    # Директория для сохранения моделей
    save_dir = os.getenv("DEMUCS_MODEL_DIR", "pretrained_models/demucs")
    os.makedirs(save_dir, exist_ok=True)

    # Путь к модели
    model_path = os.path.join(save_dir, f"{model_name}.th")

    if os.path.exists(model_path):
        print(f"⚡ Demucs: Загружаем модель из локального файла {model_path}")
        model = torch.load(model_path)
    else:
        print(f"🔽 Demucs: Скачиваем модель '{model_name}' в {save_dir}...")
        model = get_model(name=model_name)
        torch.save(model.state_dict(), model_path)
        print("✅ Demucs модель загружена и сохранена.")

    # Загрузка модели с путём
    model = get_model(name=model_name)
    model.load_state_dict(torch.load(model_path))

    return model
