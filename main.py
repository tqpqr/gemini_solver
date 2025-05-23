from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import base64
import requests
from PIL import Image
import io
import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Получаем API-ключ и URL из переменных окружения
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "default_key_if_not_set")
GEMINI_API_URL = os.getenv("GEMINI_API_URL", "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent")

# Логируем значения переменных окружения
logger.info(f"GEMINI_API_KEY: {'set' if GEMINI_API_KEY != 'default_key_if_not_set' else 'not set'}")
logger.info(f"GEMINI_API_URL: {GEMINI_API_URL}")

@app.post("/upload")
async def upload_image(data: dict):
    logger.info("Received request to /upload")

    # Проверяем наличие image в данных
    if "image" not in data:
        logger.error("No image data provided in request")
        raise HTTPException(status_code=400, detail="No image data provided")

    image_data = data["image"]
    logger.info(f"Raw image data length: {len(image_data)}")

    # Удаляем префикс data:image/png;base64, если он есть
    if "," in image_data:
        image_data = image_data.split(",")[1]
    logger.info(f"Base64 image data length: {len(image_data)}")

    try:
        # Декодируем Base64
        logger.info("Decoding Base64 image data")
        img_bytes = base64.b64decode(image_data)
        logger.info(f"Decoded image bytes length: {len(img_bytes)}")

        # Проверяем, является ли это валидным изображением
        logger.info("Opening image with PIL")
        img = Image.open(io.BytesIO(img_bytes))
        logger.info(f"Image format: {img.format}, size: {img.size}")

        # Формируем запрос к Gemini API
        logger.info("Sending request to Gemini API")
        response = requests.post(
            f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [
                    {
                        "parts": [
                            {
                                "inline_data": {
                                    "mime_type": "image/png",
                                    "data": image_data
                                }
                            },
                            {
                                "text": "Analyze this image and provide a description."
                            }
                        ]
                    }
                ]
            },
            timeout=10  # Добавляем таймаут
        )
        logger.info(f"Gemini API response status: {response.status_code}")
        response.raise_for_status()
        result = response.json()
        logger.info(f"Gemini API response: {result}")

        # Извлекаем ответ
        answer = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "No analysis available")
        logger.info(f"Extracted answer: {answer}")
        return {"answer": answer}

    except base64.binascii.Error as e:
        logger.error(f"Base64 decoding error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid Base64 image data: {str(e)}")
    except Image.UnidentifiedImageError as e:
        logger.error(f"Image processing error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid image format: {str(e)}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Gemini API request failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error communicating with Gemini API: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
