from services.model_loader import *

if __name__ == "__main__":
    print("📦 Предварительная загрузка всех моделей...")
    demux_model = load_demucs_model()
    print("🎉 Все модели успешно загружены и сохранены.")