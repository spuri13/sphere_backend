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
    return {"message": "StudySphere Backend API - 3-Stage Generation"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

def clean_ai_json(raw_text):
    """Remove markdown wrappers and extract valid JSON."""
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
    
    # Fix common escape issues - replace problematic backslashes
    # This handles cases like "can't" becoming "can\'t"
    raw_text = raw_text.replace("\\'", "'")
    raw_text = raw_text.replace('\\"', '"')
    
    return raw_text

# Load environment
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

def call_ai(prompt, max_tokens=4000):
    """Helper function to call AI API."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": max_tokens
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=120)

        if response.status_code != 200:
            print(f"[AI] API Error: {response.text}")
            return None

        response_json = response.json()
        
        if "choices" not in response_json or len(response_json["choices"]) == 0:
            print(f"[AI] Invalid response structure")
            return None
            
        raw_output = response_json["choices"][0]["message"]["content"]
        cleaned_output = clean_ai_json(raw_output)
       
        result = json.loads(cleaned_output)
        return result
        
    except requests.exceptions.Timeout:
        print("[AI] Error: Request timed out")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[AI] Error: Request failed - {str(e)}")
        return None
    except json.JSONDecodeError as e:
        print(f"[AI] Error: Failed to parse JSON - {str(e)}")
        return None
    except Exception as e:
        print(f"[AI] Unexpected error: {str(e)}")
        return None

# STAGE 1: Generate Structure
@app.post("/api/generate-structure")
async def generate_structure(request: Request):
    try:
        data = await request.json()
        topic = data.get("topic")
        
        if not topic:
            return JSONResponse({"error": "Missing topic"}, status_code=400)
       
        print(f"[STAGE 1] Generating structure for: {topic}")
        
        prompt = f"""Generate a learning mind map structure for "{topic}".

Return ONLY valid JSON with nodes and links:

{{
  "nodes": [
    {{"id": "root", "label": "{topic}", "level": 0, "unlocked": true, "quiz_completed": false}},
    {{"id": "sub1", "label": "First Major Subtopic", "level": 1, "unlocked": true, "quiz_completed": false}},
    {{"id": "sub2", "label": "Second Major Subtopic", "level": 1, "unlocked": true, "quiz_completed": false}},
    {{"id": "detail1", "label": "Detailed Concept 1", "level": 2, "unlocked": false, "quiz_completed": false}}
  ],
  "links": [
    {{"source": "root", "target": "sub1"}},
    {{"source": "root", "target": "sub2"}},
    {{"source": "sub1", "target": "detail1"}}
  ]
}}

REQUIREMENTS:
- Create 10-15 nodes total
- Level 0 = 1 root node (unlocked: true)
- Level 1 = 3-5 main subtopics (unlocked: true)
- Level 2-3 = detailed concepts (unlocked: false)
- Use short IDs (max 10 chars)
- Clear, specific labels
- Logical hierarchy
- Return ONLY JSON"""

        result = call_ai(prompt, max_tokens=3000)
        
        if not result or "nodes" not in result or "links" not in result:
            return JSONResponse({"error": "Failed to generate structure"}, status_code=500)
        
        print(f"[STAGE 1] ✓ Generated {len(result['nodes'])} nodes, {len(result['links'])} links")
        return JSONResponse(result)
   
    except Exception as e:
        print(f"[STAGE 1] Error: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)

# STAGE 2: Generate Content
@app.post("/api/generate-content")
async def generate_content(request: Request):
    try:
        data = await request.json()
        topic = data.get("topic")
        nodes = data.get("nodes")
        
        if not topic or not nodes:
            return JSONResponse({"error": "Missing topic or nodes"}, status_code=400)
       
        print(f"[STAGE 2] Generating content for {len(nodes)} nodes")
        
        # Get first 5 nodes for content generation
        node_list = "\n".join([f"- {n['id']}: {n['label']}" for n in nodes[:10]])
        
        prompt = f"""Write detailed educational content for these topics about "{topic}":

{node_list}

Return ONLY valid JSON:

{{
  "nodeContent": {{
    "node_id": "4-6 paragraphs of detailed, informative content. Each paragraph should be 4-5 sentences. Cover: definition, key concepts, real-world examples, applications, current challenges, and advanced context. Be thorough and educational.",
    "another_id": "Similarly detailed content..."
  }}
}}

CRITICAL:
- Each entry = 4-6 full paragraphs
- Each paragraph = 4-5 complete sentences
- Be specific, detailed, and educational
- Include examples and applications
- Return ONLY JSON"""

        result = call_ai(prompt, max_tokens=8000)
        
        if not result or "nodeContent" not in result:
            return JSONResponse({"error": "Failed to generate content"}, status_code=500)
        
        print(f"[STAGE 2] ✓ Generated content for {len(result['nodeContent'])} nodes")
        return JSONResponse(result)
   
    except Exception as e:
        print(f"[STAGE 2] Error: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)

# STAGE 3: Generate Quizzes
@app.post("/api/generate-quizzes")
async def generate_quizzes(request: Request):
    try:
        data = await request.json()
        topic = data.get("topic")
        nodes = data.get("nodes")
        content = data.get("content", {})
        
        if not topic or not nodes:
            return JSONResponse({"error": "Missing topic or nodes"}, status_code=400)
       
        print(f"[STAGE 3] Generating quizzes for {len(nodes)} nodes")
        
        # Generate quiz info for each node
        node_info = "\n".join([
            f"- {n['id']}: {n['label']}"
            for n in nodes[:10]
        ])
        
        prompt = f"""Create comprehension quiz questions for these topics about "{topic}":

{node_info}

Return ONLY valid JSON:

{{
  "nodeQuizzes": {{
    "node_id": {{
      "question": "A thoughtful comprehension question about this topic",
      "options": [
        "Correct answer (detailed and specific)",
        "Plausible wrong answer 1",
        "Plausible wrong answer 2",
        "Plausible wrong answer 3"
      ],
      "answer": 0
    }},
    "another_id": {{
      "question": "Another comprehension question...",
      "options": ["...", "...", "...", "..."],
      "answer": 1
    }}
  }}
}}

REQUIREMENTS:
- Each quiz = single object (NOT array)
- Questions test understanding (not memorization)
- All options should be plausible
- Mix up correct answer position (0, 1, 2, or 3)
- Return ONLY JSON"""

        result = call_ai(prompt, max_tokens=6000)
        
        if not result or "nodeQuizzes" not in result:
            return JSONResponse({"error": "Failed to generate quizzes"}, status_code=500)
        
        # Validate quiz structure
        for node_id, quiz in result["nodeQuizzes"].items():
            if isinstance(quiz, list):
                result["nodeQuizzes"][node_id] = quiz[0] if quiz else {}
        
        print(f"[STAGE 3] ✓ Generated quizzes for {len(result['nodeQuizzes'])} nodes")
        return JSONResponse(result)
   
    except Exception as e:
        print(f"[STAGE 3] Error: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    print("="*60)
    print("StudySphere Backend - 3-Stage Generation")
    print("="*60)
    print("Stage 1: /api/generate-structure")
    print("Stage 2: /api/generate-content")
    print("Stage 3: /api/generate-quizzes")
    print("="*60)
    uvicorn.run(app, host="0.0.0.0", port=8000)