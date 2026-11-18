import os
import json
import logging
from config import Config
from services.bhasha_service import generate_multilingual_advice

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are PRANVYRA Bhasha-Air — an intelligent, scientifically rigorous urban air intelligence and sustainable lifestyle companion.
You assist urban citizens, commuters, students, and families in understanding surrounding air quality, making healthier daily choices, improving indoor conditions, and reducing personal carbon and particulate footprints.

LANGUAGE INSTRUCTION:
You MUST respond in the requested language:
- If language is 'en', respond in clear, accessible English.
- If language is 'hi', respond in natural, culturally fluent Hindi (हिंदी script).
- If language is 'bn', respond in natural, culturally fluent Bengali (বাংলা script).

SCIENTIFIC & ETHICAL GUIDELINES:
1. Always be scientifically grounded. Differentiate measured observations from modeled forecasts.
2. DO NOT make medical diagnoses or clinical prescriptions. Provide general public health guidance (e.g. wearing certified N95 respirators, adjusting exertion levels, timing ventilation).
3. Be realistic, encouraging, and actionable. Do not exaggerate or make unsupported environmental claims (e.g. do NOT claim houseplants alone can purify indoor air; emphasize ventilation and HEPA filtration).
4. For emission comparisons, use transparent assumptions (e.g. standard petrol car ~170 g CO2/km, electric metro ~28 g CO2/pkm).
5. Always generate structured advice that answers these 6 mandatory questions:
   - 1. What environmental issue has been identified?
   - 2. Why does it matter?
   - 3. What action should the user take?
   - 4. Why is that action appropriate for this situation?
   - 5. What is the expected benefit?
   - 6. What assumptions and uncertainties exist?
   And synthesize:
   - "YOUR NEXT BEST ACTION"

RESPONSE FORMAT:
Provide a conversational introduction, followed by a structured JSON card inside a ```json ``` block with these exact keys:
{
  "next_best_action": "Clear, single highest-impact priority action",
  "issue": "What environmental issue has been identified?",
  "importance": "Why does it matter to health and the environment?",
  "action": "What specific action should the user take?",
  "appropriateness": "Why is that action appropriate for this situation?",
  "benefit": "What is the expected direct benefit?",
  "assumptions": "What assumptions and uncertainties exist?",
  "confidence": "High (90-95%) / Moderate (75-85%)",
  "source": "US EPA / DEFRA / WHO"
}
Followed by a concise closing tip in the selected language.
"""

def generate_ai_response(user_message, user_context, aqi_context, weather_context, language="en"):
    """
    Orchestrates multilingual AI responses using Google Gemini API or Bhasha-Air heuristic reasoning.
    Supports English, Hindi, and Bengali.
    """
    api_key = Config.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
    lang = language if language in ["en", "hi", "bn"] else "en"
    
    city = user_context.get("city", "Your City")
    transport = user_context.get("primary_transport", "public_transit")
    dist = float(user_context.get("commute_distance_km", 10.0))
    current_aqi = aqi_context.get("aqi", 100) if aqi_context.get("is_available") else 100
    
    if api_key and api_key.strip() and api_key != "your_gemini_api_key_here":
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=SYSTEM_PROMPT
            )
            context_str = f"""
LANGUAGE REQUESTED: {lang}
USER CONTEXT:
- City: {city}
- Commute: {dist} km via {transport}
- Schedule: {user_context.get('work_schedule', 'Standard Day')}
- Outdoor Hours: {user_context.get('outdoor_hours', '1-2 hours')}

ENVIRONMENTAL CONTEXT:
- Ambient AQI: {current_aqi} ({aqi_context.get('category', 'Moderate')})
- Weather: {weather_context.get('temperature', 24)}°C, Humidity: {weather_context.get('humidity', 50)}%, Wind: {weather_context.get('wind_speed', 5)} km/h
- Data Source: {aqi_context.get('data_source', 'Open-Meteo CAMS Global Model')}
"""
            full_prompt = f"{context_str}\n\nUSER QUESTION:\n{user_message}"
            response = model.generate_content(full_prompt)
            if response and response.text:
                return parse_ai_output(response.text, lang)
        except Exception as e:
            logger.warning(f"Gemini API request failed: {e}. Falling back to Bhasha-Air heuristic reasoning.")
            
    # Multilingual Bhasha-Air engine
    advice = generate_multilingual_advice(user_message, lang, current_aqi, city, transport, dist)
    return {
        "text": advice["text"],
        "structured_card": advice["card"],
        "labels": advice["labels"],
        "language": lang,
        "is_ai_generated": False
    }

def parse_ai_output(raw_text, language="en"):
    card = None
    cleaned_text = raw_text
    
    if "```json" in raw_text:
        try:
            parts = raw_text.split("```json")
            json_part = parts[1].split("```")[0].strip()
            card = json.loads(json_part)
            cleaned_text = parts[0].strip() + "\n\n" + parts[1].split("```", 1)[1].strip()
        except Exception as e:
            logger.warning(f"Failed to parse JSON from AI response: {e}")
            
    return {
        "text": cleaned_text.strip(),
        "structured_card": card,
        "language": language,
        "is_ai_generated": True
    }
