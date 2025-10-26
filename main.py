from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
import json
import requests
import re

app = FastAPI()

# CORS configuration
origins = [
    "https://hackpsu-five.vercel.app",
    "https://hackpsu-git-main-aaravdaga-5997s-projects.vercel.app", 
    "https://hackpsu-ndvo95ani-aaravdaga-5997s-projects.vercel.app",
    "http://localhost:3000",
    "http://localhost:5173",
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

@app.post("/api/fetch")
async def generate_graph(request: Request):
    try:
        data = await request.json()
        topic = data.get("url")  # Frontend sends "url" field
        
        if not topic:
            return JSONResponse({"error": "Missing topic in 'url' field"}, status_code=400)
       
        print(f"[API] Generating graph for topic: {topic}")
        
        # Generate the graph data
        result = get_children_nodes(topic)
       
        if result:
            print(f"[API] Successfully generated graph with {len(result.get('nodes', []))} nodes")
            return JSONResponse(result)
        else:
            print("[API] Failed to generate graph - get_children_nodes returned None")
            return JSONResponse(
                {"error": "Failed to generate graph data. The AI service may be unavailable or timed out."}, 
                status_code=500
            )
   
    except Exception as e:
        print(f"[API] Error in generate_graph: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse({"error": str(e)}, status_code=500)

def clean_ai_json(raw_text):
    """
    Remove markdown wrappers and extract valid JSON.
    """
    raw_text = raw_text.strip()
    
    # Remove markdown code blocks
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:].strip()
    elif raw_text.startswith("```"):
        raw_text = raw_text[3:].strip()
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3].strip()
    
    # Find the first complete JSON object
    match = re.search(r'\{[\s\S]*\}', raw_text)
    if match:
        return match.group(0)
    
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
        print(f"[INIT] .env loaded from: {path}")
        break

if not dotenv_found:
    print("[INIT] Warning: .env file not found")

# Get API key from environment or hardcoded fallback
API_KEY = os.getenv("OPENROUTER_API_KEY")

if not API_KEY:
    raise ValueError("OPENROUTER_API_KEY not found")

print(f"[INIT] API Key configured: {API_KEY[:20]}...")

API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "mistralai/mistral-small-3.2-24b-instruct:free"

def get_children_nodes(topic: str):
    """
    Generate nodes, links, and content for a mind map using DeepSeek API.
    """
    prompt = f"""Generate a learning mind map for the topic "{topic}".

Return ONLY a valid JSON object (no markdown, no explanations) with this exact structure, but replacing the example content with content about the given topic:

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

Use the above example as to how to format your response, but use the below instructions for the content generation:

Requirements:
- Return ONLY valid JSON (no markdown, no prose before/after)
- Include 8–10 nodes minimum
- Level 0 = root (unlocked: true)
- Level 1 nodes = unlocked: false
- Levels 2, 3, 4, and/or 5 = unlocked: false
- Each node’s "content" must have AT LEAST **4 detailed paragraphs** (each 4–5 sentences) that:
  - Explain the subtopic clearly
  - Include examples or applications
  - Offer advanced context or nuances
- Each node must include a "quiz" object with:
  - one comprehension-style question
  - four plausible multiple-choice options
  - "answer" = index (0–3) of correct choice

"""

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 121072
    }

    try:
        print(f"[AI] Calling OpenRouter API for topic: {topic}")
        print(f"[AI] Model: {MODEL}")
        
        response = requests.post(API_URL, headers=headers, json=payload, timeout=120)

        print(f"[AI] Response status: {response.status_code}")

        if response.status_code != 200:
            print(f"[AI] API Error: {response.text}")
            return None

        response_json = response.json()
        
        if "choices" not in response_json or len(response_json["choices"]) == 0:
            print(f"[AI] Invalid response structure: {response_json}")
            return None
            
        raw_output = response_json["choices"][0]["message"]["content"]
        print(f"[AI] Raw response length: {len(raw_output)} chars")
        print(f"[AI] First 200 chars: {raw_output[:200]}")
        
        # Clean the output
        cleaned_output = clean_ai_json(raw_output)
        print(f"[AI] Cleaned output length: {len(cleaned_output)} chars")
       
        # Parse JSON
        result = json.loads(cleaned_output)
        
        # Validate structure
        required_keys = ["nodes", "links", "nodeContent"]
        missing_keys = [key for key in required_keys if key not in result]
        
        if missing_keys:
            print(f"[AI] Error: Missing required keys: {missing_keys}")
            print(f"[AI] Available keys: {list(result.keys())}")
            return None
        
        # Validate nodes
        if not result["nodes"] or len(result["nodes"]) == 0:
            print("[AI] Error: No nodes in response")
            return None
            
        print(f"[AI] ✓ Successfully generated graph:")
        print(f"[AI]   - {len(result['nodes'])} nodes")
        print(f"[AI]   - {len(result['links'])} links")
        print(f"[AI]   - {len(result['nodeContent'])} content entries")
        
        return result
        
    except requests.exceptions.Timeout:
        print("[AI] Error: Request timed out after 120 seconds")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[AI] Error: Request failed - {str(e)}")
        return None
    except json.JSONDecodeError as e:
        print(f"[AI] Error: Failed to parse JSON - {str(e)}")
        print(f"[AI] Attempted to parse: {cleaned_output[:500]}...")
        return None
    except Exception as e:
        print(f"[AI] Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    import uvicorn
    print("="*60)
    print("Starting StudySphere Backend Server")
    print("="*60)
    print(f"CORS enabled for: {', '.join(origins)}")
    print(f"API Key: {API_KEY[:20]}...")
    print("="*60)
    uvicorn.run(app, host="0.0.0.0", port=8000)