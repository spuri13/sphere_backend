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

{
  "nodes": [
    {"id": "PS", "label": "Photosynthesis", "level": 0, "unlocked": true, "quiz_completed": false},
    {"id": "LightReactions", "label": "Light Reactions", "level": 1, "unlocked": false, "quiz_completed": false},
    {"id": "CalvinCycle", "label": "Calvin Cycle", "level": 1, "unlocked": false, "quiz_completed": false},
    {"id": "Chloroplast", "label": "Chloroplast Structure", "level": 2, "unlocked": false, "quiz_completed": false},
    {"id": "Pigments", "label": "Photosynthetic Pigments", "level": 2, "unlocked": false, "quiz_completed": false},
    {"id": "ATP", "label": "ATP and Energy Conversion", "level": 2, "unlocked": false, "quiz_completed": false},
    {"id": "Factors", "label": "Factors Affecting Photosynthesis", "level": 2, "unlocked": false, "quiz_completed": false},
    {"id": "Adaptations", "label": "C3, C4, and CAM Adaptations", "level": 3, "unlocked": false, "quiz_completed": false}
  ],
  "links": [
    {"source": "PS", "target": "LightReactions"},
    {"source": "PS", "target": "CalvinCycle"},
    {"source": "LightReactions", "target": "Chloroplast"},
    {"source": "LightReactions", "target": "Pigments"},
    {"source": "CalvinCycle", "target": "ATP"},
    {"source": "PS", "target": "Factors"},
    {"source": "PS", "target": "Adaptations"}
  ],
  "nodeContent": {
    "PS": {
      "content": "Photosynthesis is the biochemical process through which green plants, algae, and some bacteria convert light energy into chemical energy. It occurs primarily in the chloroplasts of plant cells, where light energy is absorbed by pigments like chlorophyll. The process uses water and carbon dioxide to produce glucose and oxygen, making it the foundation of most ecosystems.\n\nAt the molecular level, photosynthesis involves two major stages: the light-dependent reactions and the light-independent reactions, commonly known as the Calvin cycle. The light reactions capture sunlight and convert it into ATP and NADPH, while the Calvin cycle uses those products to fix carbon dioxide into glucose.\n\nBeyond its biochemical importance, photosynthesis regulates Earth’s atmosphere and drives the global carbon cycle. By sequestering carbon dioxide, plants act as natural climate stabilizers. Modern scientists also study artificial photosynthesis systems as a way to generate clean energy by mimicking this natural process.",
      "quiz": {
        "question": "What are the two major stages of photosynthesis?",
        "options": ["Light and dark reactions", "Photosystem I and II", "Krebs cycle and glycolysis", "Fermentation and respiration"],
        "answer": 0
      }
    },
    "LightReactions": {
      "content": "The light reactions of photosynthesis occur in the thylakoid membranes of chloroplasts and are the first stage of energy conversion. When sunlight hits chlorophyll molecules, it excites electrons that travel through an electron transport chain involving Photosystem II and Photosystem I. This flow generates ATP and NADPH, two high-energy molecules used later in the Calvin cycle.\n\nWater molecules are split during photolysis, releasing oxygen as a byproduct and replenishing electrons lost by chlorophyll. The energy released as electrons move along the transport chain drives the pumping of protons into the thylakoid lumen, creating a proton gradient used to synthesize ATP through chemiosmosis.\n\nThese reactions are dependent on light intensity, pigment availability, and the integrity of photosystems. They effectively convert light energy into usable chemical energy, setting the stage for glucose synthesis in the next phase.",
      "quiz": {
        "question": "What are the main products of the light reactions?",
        "options": ["ATP and NADPH", "Glucose and oxygen", "CO2 and water", "Pyruvate and acetyl-CoA"],
        "answer": 0
      }
    },
    "CalvinCycle": {
      "content": "The Calvin cycle, also called the dark or light-independent reactions, is the process by which plants convert carbon dioxide into glucose. It takes place in the stroma of the chloroplast and uses the ATP and NADPH generated from the light reactions as energy sources.\n\nThe cycle begins with the enzyme RuBisCO fixing CO2 into a five-carbon compound called RuBP, forming an unstable six-carbon molecule that quickly splits into two three-carbon molecules of 3-phosphoglycerate. These are then reduced and rearranged to form glucose precursors.\n\nThe Calvin cycle is essential for the biosynthesis of carbohydrates and other organic molecules. Its rate can be affected by temperature, CO2 concentration, and light indirectly, since ATP and NADPH production depend on it.",
      "quiz": {
        "question": "What enzyme catalyzes the first step of the Calvin cycle?",
        "options": ["RuBisCO", "ATP synthase", "Chlorophyll", "Cytochrome oxidase"],
        "answer": 0
      }
    },
    "Chloroplast": {
      "content": "Chloroplasts are double-membraned organelles that serve as the site of photosynthesis in plants and algae. Inside them, the thylakoid membranes house the pigments and protein complexes needed for capturing light energy.\n\nThe arrangement of thylakoids into stacks called grana maximizes surface area for light absorption. The stroma, the fluid-filled space surrounding the grana, is where the Calvin cycle reactions occur. This compartmentalization ensures the efficient coordination of energy capture and sugar synthesis.\n\nChloroplasts evolved from ancient cyanobacteria through endosymbiosis, as suggested by their own DNA and ribosomes. Their structure reflects billions of years of evolutionary refinement to maximize energy efficiency.",
      "quiz": {
        "question": "Where in the chloroplast does the Calvin cycle occur?",
        "options": ["Stroma", "Thylakoid membrane", "Grana", "Inner membrane"],
        "answer": 0
      }
    },
    "Pigments": {
      "content": "Photosynthetic pigments absorb light energy for use in photosynthesis. Chlorophyll a is the main pigment responsible for absorbing light primarily in the blue and red regions of the spectrum. Chlorophyll b and accessory pigments such as carotenoids broaden the range of absorbable light.\n\nEach pigment has a distinct absorption spectrum, and together they enable plants to harvest energy efficiently under varying light conditions. The light absorbed is transferred to reaction centers in the photosystems where it drives electron excitation.\n\nCarotenoids also serve as photoprotective agents, preventing oxidative damage by dissipating excess energy. The diversity of pigments contributes to the adaptability of photosynthetic organisms to different light environments.",
      "quiz": {
        "question": "Which pigment is the primary light absorber in photosynthesis?",
        "options": ["Chlorophyll a", "Carotenoid", "Xanthophyll", "Chlorophyll b"],
        "answer": 0
      }
    },
    "ATP": {
      "content": "ATP (adenosine triphosphate) acts as the universal energy currency of the cell. During the light reactions, ATP is produced through photophosphorylation driven by a proton gradient across the thylakoid membrane.\n\nThe enzyme ATP synthase catalyzes the formation of ATP from ADP and inorganic phosphate as protons flow back into the stroma. This ATP then powers various biosynthetic reactions, including those in the Calvin cycle where glucose is assembled.\n\nATP links the two stages of photosynthesis by carrying energy harvested from light into carbon fixation processes, ensuring a seamless flow of energy within the chloroplast.",
      "quiz": {
        "question": "What enzyme synthesizes ATP during photosynthesis?",
        "options": ["ATP synthase", "RuBisCO", "Cytochrome b6f", "Ferredoxin"],
        "answer": 0
      }
    },
    "Factors": {
      "content": "Several environmental factors influence the rate of photosynthesis. Light intensity affects the number of photons available to excite electrons in the chlorophyll molecules. Carbon dioxide concentration directly determines how much carbon can be fixed in the Calvin cycle.\n\nTemperature impacts enzymatic activity, especially that of RuBisCO, which has an optimal operating range. Extremely high or low temperatures can reduce photosynthetic efficiency.\n\nWater availability is also critical, as water is both a reactant and a medium for nutrient transport. Stress from drought or pollution can cause stomata to close, limiting CO2 uptake and slowing down photosynthesis.",
      "quiz": {
        "question": "Which of the following does NOT directly affect photosynthesis?",
        "options": ["Sound frequency", "CO2 concentration", "Light intensity", "Temperature"],
        "answer": 0
      }
    },
    "Adaptations": {
      "content": "Different plants have evolved adaptations to optimize photosynthesis under diverse environmental conditions. C3 plants, which include most temperate crops, use the Calvin cycle directly. They are efficient under moderate light and temperature but lose efficiency under hot conditions due to photorespiration.\n\nC4 plants such as maize minimize photorespiration by spatially separating carbon fixation and the Calvin cycle in different cell types. This allows them to thrive in high light and temperature environments.\n\nCAM plants, including many succulents, temporally separate CO2 uptake and fixation by opening stomata at night. This adaptation minimizes water loss, allowing survival in arid habitats while maintaining photosynthetic productivity.",
      "quiz": {
        "question": "What is a key adaptation of CAM plants?",
        "options": ["They open stomata at night", "They lack chloroplasts", "They fix nitrogen instead of carbon", "They do not use the Calvin cycle"],
        "answer": 0
      }
    }
  }
}


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
        "max_tokens": 400000
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