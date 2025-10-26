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
    "https://hackpsu-aaravdaga-5997s-projects.vercel.app",
    "https://hackpsu-aj1y0cag4-aaravdaga-5997s-projects.vercel.app",
    "https://hackpsu-git-main-aaravdaga-5997s-projects.vercel.app",
    "https://hackpsu-h24rl23wb-aaravdaga-5997s-projects.vercel.app",
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
    """Remove markdown wrappers and extract valid JSON with aggressive cleaning."""
    raw_text = raw_text.strip()
    
    # Remove markdown code blocks
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:].strip()
    elif raw_text.startswith("```"):
        raw_text = raw_text[3:].strip()
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3].strip()
    
    # Extract JSON object
    match = re.search(r'\{[\s\S]*\}', raw_text)
    if match:
        raw_text = match.group(0)
    
    # Fix escape sequences
    raw_text = raw_text.replace('\\n', ' ')
    raw_text = raw_text.replace('\\t', ' ')
    raw_text = raw_text.replace('\\r', ' ')
    raw_text = raw_text.replace("\\'", "'")
    
    # Remove invalid escapes
    raw_text = re.sub(r'\\(?!["\\/bfnrtu])', '', raw_text)
    
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

API_KEY = os.getenv("OPENROUTER_API_KEY")
if not API_KEY:
    raise ValueError("OPENROUTER_API_KEY not found")

print(f"[INIT] API Key configured: {API_KEY[:20]}...")

API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "qwen/qwen-2.5-72b-instruct:free"

def get_children_nodes(topic: str):
    """
    Generate nodes, links, and content for a mind map using AI.
    Returns format with MULTIPLE quiz questions per node.
    """
    prompt = f"""Generate a learning mind map for the topic "{topic}".

Return ONLY valid JSON (no markdown, no extra text) with this structure:

{{
  "nodes": [
    {{"id": "node1", "label": "Main Topic", "level": 0, "unlocked": true, "quiz_completed": false}},
    {{"id": "node2", "label": "Subtopic 1", "level": 1, "unlocked": false, "quiz_completed": false}},
    {{"id": "node3", "label": "Subtopic 2", "level": 2, "unlocked": false, "quiz_completed": false}}
  ],
  "links": [
    {{"source": "node1", "target": "node2"}},
    {{"source": "node2", "target": "node3"}}
  ],
  "nodeContent": {{
    "node1": {{
      "content": "Write 4-5 detailed paragraphs (each 4-5 sentences) explaining this topic comprehensively. Include definition, key concepts, real-world examples, applications, challenges, and advanced context.",
      "quizzes": [
        {{
          "question": "First question about key concept?",
          "options": ["Correct answer", "Wrong 1", "Wrong 2", "Wrong 3"],
          "answer": 0
        }},
        {{
          "question": "Second question about application?",
          "options": ["Wrong 1", "Correct answer", "Wrong 2", "Wrong 3"],
          "answer": 1
        }},
        {{
          "question": "Third question about example?",
          "options": ["Wrong 1", "Wrong 2", "Correct answer", "Wrong 3"],
          "answer": 2
        }}
      ]
    }},
    "node2": {{
      "content": "4-5 paragraph detailed explanation of subtopic 1.",
      "quizzes": [
        {{
          "question": "Question 1 about this subtopic?",
          "options": ["Option A", "Correct answer", "Option C", "Option D"],
          "answer": 1
        }},
        {{
          "question": "Question 2 about this subtopic?",
          "options": ["Option A", "Option B", "Option C", "Correct answer"],
          "answer": 3
        }},
        {{
          "question": "Question 3 about this subtopic?",
          "options": ["Correct answer", "Option B", "Option C", "Option D"],
          "answer": 0
        }}
      ]
    }}
  }}
}}

CRITICAL REQUIREMENTS:
- Return ONLY the JSON object (no markdown, no prose)
- NO backslashes or escape characters
- Create 10-15 nodes minimum with proper hierarchy
- Level 0 = root (unlocked: true, quiz_completed: false)
- Level 1 nodes = unlocked: true (to allow immediate exploration)
- Level 2, 3, 4 nodes = unlocked: false
- Each "content" = 4-5 detailed paragraphs (4-5 sentences each) with examples
- Each "quizzes" = ARRAY of 10 quiz objects
- Each quiz object has:
  - "question": string
  - "options": array of 4 strings
  - "answer": integer 0-3 (index of correct option)
- Use short, unique IDs (e.g., "ai", "ml", "dl")
- Ensure all node IDs match between nodes, links, and nodeContent
- Plain text only, no special characters or backslashes
"""

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 32000
    }

    try:
        print(f"[AI] Calling OpenRouter API for topic: {topic}")
        
        response = requests.post(API_URL, headers=headers, json=payload, timeout=150)

        if response.status_code != 200:
            print(f"[AI] API Error: {response.text}")
            return None

        response_json = response.json()
        
        if "choices" not in response_json or len(response_json["choices"]) == 0:
            print(f"[AI] Invalid response structure")
            return None
            
        raw_output = response_json["choices"][0]["message"]["content"]
        print(f"[AI] Raw response length: {len(raw_output)} chars")
        
        cleaned_output = clean_ai_json(raw_output)
       
        try:
            result = json.loads(cleaned_output)
        except json.JSONDecodeError as e:
            print(f"[AI] JSON parse failed, trying aggressive cleaning...")
            ultra_clean = cleaned_output.replace('\\', '')
            result = json.loads(ultra_clean)
        
        # Validate structure
        required_keys = ["nodes", "links", "nodeContent"]
        missing_keys = [key for key in required_keys if key not in result]
        
        if missing_keys:
            print(f"[AI] Error: Missing required keys: {missing_keys}")
            return None
        
        if not result["nodes"] or len(result["nodes"]) == 0:
            print("[AI] Error: No nodes in response")
            return None
        
        # Validate and normalize nodeContent structure
        for node_id, content in result["nodeContent"].items():
            # Handle both "quiz" and "quizzes" fields for backward compatibility
            if "quiz" in content and "quizzes" not in content:
                # Convert single quiz to array
                single_quiz = content["quiz"]
                if isinstance(single_quiz, dict):
                    content["quizzes"] = [single_quiz]
                elif isinstance(single_quiz, list):
                    content["quizzes"] = single_quiz
                del content["quiz"]
                print(f"[AI] Converted single quiz to array for node: {node_id}")
            
            # Ensure quizzes is an array
            if "quizzes" in content:
                if not isinstance(content["quizzes"], list):
                    content["quizzes"] = [content["quizzes"]]
                
                # Validate each quiz
                valid_quizzes = []
                for idx, quiz in enumerate(content["quizzes"]):
                    if isinstance(quiz, dict) and all(key in quiz for key in ["question", "options", "answer"]):
                        if isinstance(quiz["options"], list) and len(quiz["options"]) == 4:
                            if isinstance(quiz["answer"], int) and 0 <= quiz["answer"] <= 3:
                                valid_quizzes.append(quiz)
                            else:
                                print(f"[AI] Warning: Invalid answer for quiz {idx} in node {node_id}")
                        else:
                            print(f"[AI] Warning: Invalid options for quiz {idx} in node {node_id}")
                    else:
                        print(f"[AI] Warning: Incomplete quiz {idx} for node {node_id}")
                
                content["quizzes"] = valid_quizzes
                
                if len(valid_quizzes) == 0:
                    print(f"[AI] Warning: No valid quizzes for node {node_id}, creating default")
                    content["quizzes"] = [{
                        "question": f"What is the main concept of {node_id}?",
                        "options": ["Option A", "Option B", "Option C", "Option D"],
                        "answer": 0
                    }]
            
        print(f"[AI] ✓ Successfully generated graph:")
        print(f"[AI]   - {len(result['nodes'])} nodes")
        print(f"[AI]   - {len(result['links'])} links")
        print(f"[AI]   - {len(result['nodeContent'])} content entries")
        
        # Log first node's structure
        if result['nodeContent']:
            first_key = list(result['nodeContent'].keys())[0]
            first_content = result['nodeContent'][first_key]
            print(f"[AI]   - Sample node '{first_key}':")
            print(f"[AI]     - content length: {len(first_content.get('content', ''))}")
            print(f"[AI]     - number of quizzes: {len(first_content.get('quizzes', []))}")
        
        return result
        
    except requests.exceptions.Timeout:
        print("[AI] Error: Request timed out")
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
    uvicorn.run(app, host="0.0.0.0", port=8000)