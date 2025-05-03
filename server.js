const express = require("express");
const { GoogleGenerativeAI } = require("@google/generative-ai");
const morgan = require("morgan");
const rateLimit = require("express-rate-limit");
require("dotenv").config();

const app = express();
const port = process.env.PORT || 3000;

// Middleware
app.use(express.json({ limit: "10mb" }));
app.use(morgan("combined")); // логирование запросов

// Ограничение скорости (100 запросов в 15 минут)
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 100,
  message: "Too many requests, please try again later.",
});
app.use(limiter);

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
const model = genAI.getGenerativeModel({ model: "gemini-1.5-pro" });

app.post("/upload", async (req, res) => {
  try {
    const image = req.body.image?.split(",")[1];
    if (!image) {
      return res.status(400).json({ error: "No image data provided" });
    }

    const prompt = "Помоги ответить на вопрос из теста - выбери верный вариант из представленных на изображении. Ответь коротко - только верный вариант ответа без пояснений.";

    const result = await model.generateContent([
      { text: prompt },
      { inlineData: { data: image, mimeType: "image/png" } }
    ]);

    const answer = await result.response.text();
    console.log("Gemini ответ:", answer);
    res.json({ answer });
  } catch (err) {
    console.error("Gemini API error:", err);
    res.status(500).json({ error: "Server error" });
  }
});

app.listen(port, () => {
  console.log(\`Server running on port \${port}\`);
});