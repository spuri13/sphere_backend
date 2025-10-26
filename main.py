
from fastapi import FastAPI
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
import json
import requests



app = FastAPI()
@app.post("/api/data")
async def extract_endpoint(request: Request):
    data = await request.json()
    url = data.get("url")
    if not url:
            return JSONResponse({"error": "Missing url"}, status_code=400)
    
    return {"message": f"Received URL: {url}"}

@app.post("/api/info")
async def extract_endpoint(request: Request):
    info = await request.json()
    url = info.get("url")
    if not url:
            return JSONResponse({"error": "Missing url"}, status_code=400)
    
    
@app.post("/api/quiz")
async def extract_endpoint(request: Request):
    quiz = await request.json()
    url = quiz.get("url")
    if not url:
            return JSONResponse({"error": "Missing url"}, status_code=400)
    return {"message": f"Received URL: {url}"}

def clean_ai_json(raw_text):
    """
    Remove ```json and ``` wrappers if present.
    """
    if raw_text.startswith("```json"):
        raw_text = raw_text[len("```json"):].strip()
    if raw_text.startswith("```"):
        raw_text = raw_text[3:].strip()
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3].strip()
    return raw_text

possible_paths = [
    os.path.join(os.path.dirname(os.path.realpath(__file__)), ".env"),
    os.path.join(os.getcwd(), ".env"),  
]

dotenv_found = False
for path in possible_paths:
    if os.path.exists(path):
        load_dotenv(path)
        dotenv_found = True
        print(f".env loaded from: {path}")
        break

if not dotenv_found:
    print("Warning: .env file not found. Make sure it exists in the script folder or cwd.")


load_dotenv(path)
# python3 generate_children.py
API_KEY = os.getenv("OPENROUTER_API_KEY")
if not API_KEY:
    raise ValueError(
        "OPENROUTER_API_KEY not found. Ensure your .env contains:\nOPENROUTER_API_KEY=your_key_here"
    )

API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "deepseek/deepseek-chat-v3.1:free"

def get_children_nodes(topic: str, parent_id="root", parent_level=0):
    """
    Given a topic, generate 3 child subtopics as nodes and edges for a mind map.
    Returns a dictionary with 'nodes' and 'edges'.
    """
    prompt = f"""
You are a helpful and knowledgeable study assistant generating detailed structured learning mind maps.

Given the topic "{topic}", create a **comprehensive JSON** that captures the topic hierarchy, in-depth content explanations, and multiple quiz questions for each subtopic.

Follow this exact structure — output only valid JSON, without Markdown or extra text:

{{
  "nodes": [
    {{
      "id": "AI",
      "label": "Artificial Intelligence",
      "level": 0,
      "unlocked": true,
      "quiz_completed": false
    }},
    {{
      "id": "ML",
      "label": "Machine Learning",
      "level": 1,
      "unlocked": true,
      "quiz_completed": false
    }},
    {{
      "id": "DL",
      "label": "Deep Learning",
      "level": 2,
      "unlocked": false,
      "quiz_completed": false
    }}
  ],
  "links": [
    {{ "source": "AI", "target": "ML" }},
    {{ "source": "ML", "target": "DL" }}
  ],
  "nodeContent": {{
    "AI": {{
      "content": "Write an in-depth explanation of Artificial Intelligence (AI) that covers its definition, core goals, types (narrow vs general), real-world examples, ethical considerations, and current challenges in research. The paragraph should be comprehensive and informative.",
      "quiz": [
        {{
          "question": "What distinguishes narrow AI from general AI?",
          "options": [
            "Narrow AI focuses on specific tasks; general AI performs any cognitive task",
            "General AI is weaker than narrow AI",
            "Narrow AI includes emotions",
            "General AI only exists in theory"
          ],
          "answer": 0
        }},
        {{
          "question": "Which of the following is an example of AI in everyday use?",
          "options": [
            "Voice assistants like Siri and Alexa",
            "Manual typewriters",
            "Analog clocks",
            "Vacuum tubes"
          ],
          "answer": 0
        }},
        {{
          "question": "What is one key ethical issue in AI?",
          "options": [
            "Lack of creativity",
            "Job displacement and bias",
            "Slow computation",
            "Overuse of electricity"
          ],
          "answer": 1
        }},
        {{
          "question": "Which subfield of AI focuses on decision-making and learning from data?",
          "options": [
            "Machine Learning",
            "Cryptography",
            "Quantum Computing",
            "Network Security"
          ],
          "answer": 0
        }},
        {{
          "question": "What is a primary challenge in creating general AI?",
          "options": [
            "Building machines that understand and reason like humans",
            "Improving computer graphics",
            "Reducing hardware costs",
            "Translating code to multiple languages"
          ],
          "answer": 0
        }}
      ]
    }},
    "ML": {{
      "content": "Provide a detailed explanation of Machine Learning, covering supervised, unsupervised, and reinforcement learning paradigms. Explain the importance of data, features, and model training processes. Discuss its applications in healthcare, finance, and recommendation systems.",
      "quiz": [
        {{
          "question": "What defines supervised learning?",
          "options": [
            "Learning with labeled data",
            "Learning without data",
            "Learning by observation only",
            "Learning using random guessing"
          ],
          "answer": 0
        }},
        {{
          "question": "Which of these is an example of unsupervised learning?",
          "options": [
            "Clustering similar customers based on behavior",
            "Training a model to classify images of cats and dogs",
            "Predicting house prices from features",
            "Detecting spam emails"
          ],
          "answer": 0
        }},
        {{
          "question": "What is the goal of reinforcement learning?",
          "options": [
            "Maximize cumulative rewards through actions and feedback",
            "Predict future weather",
            "Reduce hardware costs",
            "Memorize data points"
          ],
          "answer": 0
        }},
        {{
          "question": "Which component is essential for training machine learning models?",
          "options": [
            "High-quality data",
            "Random guesses",
            "Manual rule writing",
            "Fixed outcomes"
          ],
          "answer": 0
        }},
        {{
          "question": "Which of the following best demonstrates ML in real life?",
          "options": [
            "Netflix recommending shows",
            "Sending physical mail",
            "Turning on lights manually",
            "Calculating sums with a calculator"
          ],
          "answer": 0
        }}
      ]
    }},
    "DL": {{
      "content": "Describe Deep Learning in depth, including how it differs from traditional ML, its architecture (layers, neurons, weights), and how neural networks learn using backpropagation. Discuss convolutional, recurrent, and transformer models, and their real-world uses.",
      "quiz": [
        {{
          "question": "What makes deep learning different from traditional ML?",
          "options": [
            "It uses multiple layers of neural networks",
            "It only works on text data",
            "It requires no data",
            "It is purely symbolic logic"
          ],
          "answer": 0
        }},
        {{
          "question": "What is the purpose of backpropagation?",
          "options": [
            "To adjust weights and minimize loss",
            "To increase the number of layers",
            "To generate random predictions",
            "To compress training data"
          ],
          "answer": 0
        }},
        {{
          "question": "Which architecture is used primarily for image data?",
          "options": [
            "Convolutional Neural Network (CNN)",
            "Recurrent Neural Network (RNN)",
            "Transformer",
            "Decision Tree"
          ],
          "answer": 0
        }},
        {{
          "question": "Which deep learning model excels at sequence-based tasks like language?",
          "options": [
            "Recurrent Neural Network (RNN)",
            "Convolutional Network",
            "Linear Regression",
            "Support Vector Machine"
          ],
          "answer": 0
        }},
        {{
          "question": "What does a transformer model primarily use to understand context?",
          "options": [
            "Attention mechanism",
            "Random sampling",
            "Gradient descent only",
            "Image convolution"
          ],
          "answer": 0
        }}
      ]
    }}
  }}
}}

Rules:
- Do NOT include ```json``` or any non-JSON text.
- Each node must have: id, label, level, unlocked, quiz_completed.
- Each quiz must contain **5 questions**, each with 4 options and an integer 'answer' index.
- The 'content' for each topic must be **in-depth**, covering background, key ideas, real-world uses, and examples.
- Return **only valid JSON**, with no explanation or commentary.
"""


    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.6
    }

    response = requests.post(API_URL, headers=headers, json = data, timeout=120)

    if response.status_code != 200:
        print("Error:", response.status_code, response.text)
        return None
    # python3 generate_children.py
    j = response.json()
    raw_output = j["choices"][0]["message"]["content"]
    cleaned_output = clean_ai_json(raw_output)
    try:
        data = json.loads(cleaned_output)
        return data  
    except json.JSONDecodeError as e:
        print("Failed to parse JSON:", e)
        print("Cleaned output:\n", cleaned_output)
        return None
    
if __name__ == "__main__":
    topic = input("Enter a topic: ").strip()
    print(f"\nGenerating subtopics for '{topic}'...\n")
    result = get_children_nodes(topic)

    if result:
        print(json.dumps(result, indent=2))
    else:
        print("Failed to get valid JSON from OpenRouter.ai.")