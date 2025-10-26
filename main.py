from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
import json
import requests

app = FastAPI()

# Fixed CORS middleware with your actual domain
origins = [
    "https://hackpsu-five.vercel.app",
    "http://localhost:3000",  # for local dev
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "StudySphere Backend API is running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

# Main endpoint - matches frontend call to /api/fetch
@app.post("/api/fetch")
async def generate_graph(request: Request):
    try:
        data = await request.json()
        topic = data.get("url")  # Frontend sends "url" field containing the topic
        
        if not topic:
            return JSONResponse({"error": "Missing topic"}, status_code=400)
       
        print(f"Generating graph for topic: {topic}")
        
        # Generate the graph data
        result = get_children_nodes(topic)
       
        if result:
            # Optional: Save to JSON file
            output_file = f"graph_{topic.replace(' ', '_')}.json"
            try:
                with open(output_file, 'w') as f:
                    json.dump(result, f, indent=2)
                print(f"Saved graph to {output_file}")
            except Exception as e:
                print(f"Warning: Could not save to file: {e}")
           
            return JSONResponse(result)
        else:
            return JSONResponse(
                {"error": "Failed to generate graph data from AI"}, 
                status_code=500
            )
   
    except Exception as e:
        print(f"Error in generate_graph: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/info")
async def get_info(request: Request):
    info = await request.json()
    url = info.get("url")
    if not url:
        return JSONResponse({"error": "Missing url"}, status_code=400)
    return {"message": f"Received URL: {url}"}

@app.post("/api/quiz")
async def get_quiz(request: Request):
    quiz = await request.json()
    url = quiz.get("url")
    if not url:
        return JSONResponse({"error": "Missing url"}, status_code=400)
    return {"message": f"Received URL: {url}"}

def clean_ai_json(raw_text):
    """
    Remove ```json and ``` wrappers if present.
    """
    raw_text = raw_text.strip()
    if raw_text.startswith("```json"):
        raw_text = raw_text[len("```json"):].strip()
    elif raw_text.startswith("```"):
        raw_text = raw_text[3:].strip()
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3].strip()
    return raw_text

# Load environment variables
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

API_KEY = os.getenv("OPENROUTER_API_KEY", "")
if not API_KEY:
    raise ValueError(
        "OPENROUTER_API_KEY not found. Ensure your .env contains:\nOPENROUTER_API_KEY=your_key_here"
    )

API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "deepseek/deepseek-chat-v3.1:free"

def get_children_nodes(topic: str):
    """
    Given a topic, generate nodes, links, and content for a mind map.
    Returns a dictionary with 'nodes', 'links', and 'nodeContent'.
    """
    prompt = f"""
You are a helpful and knowledgeable study assistant generating detailed structured learning mind maps.

Given the topic "{topic}", create a **comprehensive JSON** that captures the topic hierarchy, in-depth content explanations, and quiz questions for each subtopic.

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
      "content": "Artificial Intelligence (AI) is the simulation of human intelligence in machines. It encompasses narrow AI (task-specific systems like voice assistants) and general AI (hypothetical human-level intelligence). AI powers everyday tools like Siri and Alexa, recommendation systems, and autonomous vehicles. Key challenges include ethical concerns like bias and job displacement, privacy issues, and the difficulty of creating systems that can reason and understand context like humans.",
      "quiz": {{
        "question": "What distinguishes narrow AI from general AI?",
        "options": [
          "Narrow AI focuses on specific tasks; general AI performs any cognitive task",
          "General AI is weaker than narrow AI",
          "Narrow AI includes emotions",
          "General AI only exists in theory"
        ],
        "answer": 0
      }}
    }},
    "ML": {{
      "content": "Machine Learning is a subset of AI that enables systems to learn from data without explicit programming. It includes supervised learning (learning from labeled data), unsupervised learning (finding patterns in unlabeled data), and reinforcement learning (learning through trial and error with rewards). ML requires high-quality data and feature engineering. Applications include healthcare diagnosis, financial fraud detection, and personalized recommendations in streaming services.",
      "quiz": {{
        "question": "What defines supervised learning?",
        "options": [
          "Learning with labeled data",
          "Learning without data",
          "Learning by observation only",
          "Learning using random guessing"
        ],
        "answer": 0
      }}
    }},
    "DL": {{
      "content": "Deep Learning uses multi-layered neural networks to learn hierarchical representations of data. Unlike traditional ML, it automatically extracts features from raw data. Neural networks consist of layers of neurons with weighted connections that adjust through backpropagation. Key architectures include CNNs for image processing, RNNs for sequential data like text and speech, and Transformers that use attention mechanisms for understanding context in language tasks. Deep Learning powers applications like image recognition, language translation, and autonomous driving.",
      "quiz": {{
        "question": "What makes deep learning different from traditional ML?",
        "options": [
          "It uses multiple layers of neural networks",
          "It only works on text data",
          "It requires no data",
          "It is purely symbolic logic"
        ],
        "answer": 0
      }}
    }}
  }}
}}

CRITICAL RULES:
- Do NOT include ```json``` or any non-JSON text
- Each node must have: id, label, level, unlocked, quiz_completed
- Each nodeContent entry must have "content" (detailed paragraph) and "quiz" (single quiz object)
- Each quiz must have: question (string), options (array of 4 strings), answer (integer 0-3)
- The content must be in-depth, covering background, key ideas, and real-world examples
- Create at least 3-5 nodes with proper hierarchy (level 0 is root)
- Return ONLY valid JSON with no explanation or commentary
"""

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.6,
        "max_tokens": 4000
    }

    try:
        print(f"Calling OpenRouter API for topic: {topic}")
        response = requests.post(API_URL, headers=headers, json=data, timeout=120)

        if response.status_code != 200:
            print(f"API Error: {response.status_code} - {response.text}")
            return None

        j = response.json()
        raw_output = j["choices"][0]["message"]["content"]
        print(f"Received response, cleaning JSON...")
        
        cleaned_output = clean_ai_json(raw_output)
       
        # Parse and validate JSON
        result = json.loads(cleaned_output)
        
        # Validate structure
        if not all(key in result for key in ["nodes", "links", "nodeContent"]):
            print("Error: Missing required keys in response")
            return None
        
        print(f"Successfully generated graph with {len(result['nodes'])} nodes")
        return result
        
    except requests.exceptions.Timeout:
        print("Error: Request timed out")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error: Request failed - {str(e)}")
        return None
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON: {e}")
        print(f"Cleaned output:\n{cleaned_output[:500]}...")
        return None
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return None

if __name__ == "__main__":
    import uvicorn
    print("Starting StudySphere Backend Server...")
    print(f"CORS enabled for: hackpsu-five.vercel.app")
    uvicorn.run(app, host="0.0.0.0", port=8000)