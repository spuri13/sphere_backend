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
MODEL = "meta-llama/llama-3.3-8b-instruct:free"

def get_children_nodes(topic: str):
    """
    Generate nodes, links, and content for a mind map using DeepSeek API.
    """
    prompt = f"""Generate a learning mind map for the topic "{topic}".

Return ONLY a valid JSON object (no markdown, no explanations) with this exact structure:

{{
  "nodes": [
    {{"id": "node1", "label": "Main Topic", "level": 0, "unlocked": true, "quiz_completed": false}},
    {{"id": "node2", "label": "Subtopic 1", "level": 1, "unlocked": true, "quiz_completed": false}},
    {{"id": "node3", "label": "Subtopic 2", "level": 2, "unlocked": false, "quiz_completed": false}}
  ],
  "links": [
    {{"source": "node1", "target": "node2"}},
    {{"source": "node2", "target": "node3"}}
  ],
  "nodeContent": {{
    "node1": {{
      "content": "Detailed explanation about the main topic (2-3 sentences covering key concepts, examples, and applications).",
      "quiz": {{
        "question": "What is a key characteristic of this topic?",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "answer": 0
      }}
    }},
    "node2": {{
      "content": "Detailed explanation about subtopic 1.",
      "quiz": {{
        "question": "Question about subtopic 1?",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "answer": 0
      }}
    }},
    "node3": {{
      "content": "Detailed explanation about subtopic 2.",
      "quiz": {{
        "question": "Question about subtopic 2?",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "answer": 0
      }}
    }}
  }}
}}

Requirements:
- Create 8-10 nodes minimum
- Level 0 is the root (unlocked: true)
- Level 1 nodes should be unlocked: true
- Level 2 nodes should be unlocked: false
- Level 3 nodes should be unlocked: false
- Level 4 nodes should be unlocked: false
- Level 5+ nodes should be unlocked: false
- Each node needs content (several deeply informative paragraphs about the topic) and quiz (question with 4 options)
- Answer must be integer 0-3 (index of correct option)
- Return ONLY the JSON object, no other text"""

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.6,
        "max_tokens": 4000
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