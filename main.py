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
    "hackpsu-git-main-aaravdaga-5997s-projects.vercel.app",
"hackpsu-ciow1qzuq-aaravdaga-5997s-projects.vercel.app",
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
    
    # Step 1: Replace common problematic escape sequences
    raw_text = raw_text.replace('\\n', ' ')  # newlines
    raw_text = raw_text.replace('\\t', ' ')  # tabs
    raw_text = raw_text.replace('\\r', ' ')  # carriage returns
    
    # Step 2: Fix escaped quotes and apostrophes in content
    # This regex finds string values and removes invalid escapes
    def fix_string_value(match):
        value = match.group(1)
        # Remove invalid escape sequences but keep valid JSON escapes
        value = value.replace("\\'", "'")
        value = value.replace('\\"', '"')
        # Remove any other backslash that's not followed by valid JSON escape chars
        value = re.sub(r'\\(?!["\\/bfnrtu])', '', value)
        return f'"{value}"'
    
    # Apply to all string values in JSON
    raw_text = re.sub(r':\s*"([^"]*(?:\\.[^"]*)*)"', lambda m: f': {fix_string_value(m)}', raw_text)
    
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
    """Helper function to call AI API with robust error handling."""
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
        response = requests.post(API_URL, headers=headers, json=payload, timeout=90)

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
        print(f"[AI] Cleaned output preview (first 200): {cleaned_output[:200]}...")
       
        try:
            result = json.loads(cleaned_output)
            print("[AI] ✓ JSON parsed successfully")
            return result
        except json.JSONDecodeError as parse_error:
            print(f"[AI] JSON parse failed: {parse_error.msg} at position {parse_error.pos}")
            
            # Show problematic area
            start = max(0, parse_error.pos - 150)
            end = min(len(cleaned_output), parse_error.pos + 150)
            print(f"[AI] Problem area: ...{cleaned_output[start:end]}...")
            
            # Try ultra-aggressive cleaning - remove ALL backslashes
            print("[AI] Attempting ultra-aggressive cleaning...")
            ultra_clean = cleaned_output.replace('\\', '')
            
            try:
                result = json.loads(ultra_clean)
                print("[AI] ✓ Recovered with ultra-aggressive cleaning")
                return result
            except:
                print("[AI] ✗ Ultra-aggressive cleaning failed")
                return None
        
    except requests.exceptions.Timeout:
        print("[AI] Error: Request timed out after 90 seconds")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[AI] Error: Request failed - {str(e)}")
        return None
    except Exception as e:
        print(f"[AI] Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
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
        
        prompt = f"""Generate a learning mind map structure for {topic}.

Return ONLY valid JSON with nodes and links.
IMPORTANT: Do NOT use any backslashes in your response.

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
- NO backslashes anywhere"""

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
        
        # Get first 10 nodes for content generation
        node_list = "\n".join([f"- {n['id']}: {n['label']}" for n in nodes[:10]])
        
        prompt = f"""Write educational content for these topics about {topic}:

{node_list}

CRITICAL INSTRUCTIONS:
1. Return ONLY a valid JSON object
2. Do NOT use backslashes anywhere in your response
3. Use plain apostrophes and quotes without escaping
4. Use simple language without special characters
5. Each content entry should be 4-6 paragraphs
6. Each paragraph should be 4-5 sentences

Example format:
{{
  "nodeContent": {{
    "node_id": "First paragraph about the concept. It explains the basics clearly. Second paragraph with real examples from everyday life. Third paragraph about practical applications and uses. Fourth paragraph with more detailed information and context.",
    "another_id": "Content here written in plain text without any backslashes or special escape sequences. Use regular apostrophes and quotes."
  }}
}}

Remember: NO backslashes, NO escape sequences, just plain text in proper JSON format."""

        result = call_ai(prompt, max_tokens=8000)
        
        if not result:
            # Retry with even simpler prompt
            print("[STAGE 2] Retrying with simplified prompt...")
            simple_prompt = f"""Generate content about {topic} for: {node_list}

Return valid JSON with NO backslashes:

{{"nodeContent": {{"node_id": "Plain text content with 3-4 paragraphs. Use simple apostrophes. No special characters.", "other_id": "More content..."}}}}

Use only plain text."""
            
            result = call_ai(simple_prompt, max_tokens=6000)
        
        if not result or "nodeContent" not in result:
            return JSONResponse({"error": "Failed to generate content after retry"}, status_code=500)
        
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
        
        prompt = f"""Create comprehension quiz questions for these topics about {topic}:

{node_info}

CRITICAL INSTRUCTIONS:
1. Return ONLY valid JSON
2. Do NOT use any backslashes in your response
3. Use plain text without escape characters
4. Write questions and answers in simple clear language

Return this exact format:

{{
  "nodeQuizzes": {{
    "node_id": {{
      "question": "A clear question about this topic without any special characters",
      "options": [
        "Correct answer with details",
        "Plausible wrong answer 1",
        "Plausible wrong answer 2",
        "Plausible wrong answer 3"
      ],
      "answer": 0
    }},
    "another_id": {{
      "question": "Another question in plain text",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": 2
    }}
  }}
}}

REQUIREMENTS:
- Each quiz is a single object (NOT an array)
- Questions test understanding
- All options should be plausible
- Mix up correct answer position (0, 1, 2, or 3)
- Use plain text only, no backslashes or escape characters
- Return ONLY the JSON object"""

        result = call_ai(prompt, max_tokens=6000)
        
        if not result:
            # Retry with simpler prompt
            print("[STAGE 3] Retrying with simplified prompt...")
            simple_prompt = f"""Create quiz questions for {topic} topics: {node_info}

Return valid JSON without backslashes:

{{"nodeQuizzes": {{"node_id": {{"question": "Simple question", "options": ["A", "B", "C", "D"], "answer": 0}}, "other_id": {{"question": "Another question", "options": ["A", "B", "C", "D"], "answer": 1}}}}}}

Use plain text only."""
            
            result = call_ai(simple_prompt, max_tokens=4000)
        
        if not result or "nodeQuizzes" not in result:
            return JSONResponse({"error": "Failed to generate quizzes after retry"}, status_code=500)
        
        # Validate quiz structure - ensure each quiz is an object, not array
        for node_id, quiz in result["nodeQuizzes"].items():
            if isinstance(quiz, list):
                result["nodeQuizzes"][node_id] = quiz[0] if quiz else {
                    "question": "Test question",
                    "options": ["A", "B", "C", "D"],
                    "answer": 0
                }
        
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