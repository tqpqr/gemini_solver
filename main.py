from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import base64
import requests
from PIL import Image
import io
import os

app = FastAPI()

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем все источники (в продакшене уточните домены)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Получаем API-ключ из переменной окружения
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "default_key_if_not_set")
GEMINI_API_URL = os.getenv("GEMINI_API_URL", "https://api.gemini.com/v1/analyze")

@app.post("/upload")
async def upload_image(data: dict):
    if "image" not in data:
        raise HTTPException(status_code=400, detail="No image data provided")

    image_data = data["image"].split(",")[1] if "," in data["image"] else data["image"]
    try:
        # Декодируем Base64 в изображение
        img_bytes = base64.b64decode(image_data)
        img = Image.open(io.BytesIO(img_bytes))

        # Отправка на Gemini API (пример)
        response = requests.post(
            GEMINI_API_URL,
            headers={"Authorization": f"Bearer {GEMINI_API_KEY}"},
            json={"image": image_data}
        )
        response.raise_for_status()
        result = response.json()

        return {"answer": result.get("answer", "No analysis available")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)