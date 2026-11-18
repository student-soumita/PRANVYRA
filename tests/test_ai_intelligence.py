import os
import unittest
import json
from app import create_app
from services.expert_router import detect_expert_roles, get_expert_details, list_all_experts, EXPERT_ROLES
from services.ai_orchestrator import process_chat_query

class TestPranvyraAIIntelligence(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()
        import uuid
        test_email = f"ai_tester_{uuid.uuid4().hex[:8]}@pranvyra.org"
        cls.client.post("/api/auth/register", json={
            "email": test_email,
            "password": "Password123!",
            "full_name": "AI Test Citizen"
        })

    def test_list_all_experts(self):
        experts = list_all_experts()
        self.assertEqual(len(experts), 5)
        expert_ids = [e["id"] for e in experts]
        self.assertIn("atmospheric_scientist", expert_ids)
        self.assertIn("urban_mobility_expert", expert_ids)
        self.assertIn("indoor_air_specialist", expert_ids)
        self.assertIn("sustainability_strategist", expert_ids)
        self.assertIn("environmental_analyst", expert_ids)

        for e in experts:
            self.assertIn("title", e)
            self.assertIn("title_hi", e)
            self.assertIn("title_bn", e)
            self.assertIn("focus", e)
            self.assertIn("icon", e)

    def test_api_experts_endpoint(self):
        resp = self.client.get("/api/assistant/experts")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertIn("experts", data)
        self.assertEqual(len(data["experts"]), 5)

    def test_expert_intent_detection_atmospheric(self):
        query = "Explain the PM2.5 concentration and how thermal inversion affects winter AQI"
        result = detect_expert_roles(query)
        self.assertEqual(result["primary_role"], "atmospheric_scientist")
        self.assertIn("atmospheric_scientist", result["multi_expert_roles"])

    def test_expert_intent_detection_mobility(self):
        query = "Compare car tailpipe emissions vs electric metro commute for 15 km"
        result = detect_expert_roles(query)
        self.assertEqual(result["primary_role"], "urban_mobility_expert")
        self.assertIn("urban_mobility_expert", result["multi_expert_roles"])

    def test_expert_intent_detection_indoor(self):
        query = "How to improve indoor air quality with HEPA filtration when cooking with LPG gas?"
        result = detect_expert_roles(query)
        self.assertEqual(result["primary_role"], "indoor_air_specialist")
        self.assertIn("indoor_air_specialist", result["multi_expert_roles"])

    def test_expert_intent_detection_sustainability(self):
        query = "What are practical steps to reduce single-use plastic waste and household carbon footprint?"
        result = detect_expert_roles(query)
        self.assertEqual(result["primary_role"], "sustainability_strategist")
        self.assertIn("sustainability_strategist", result["multi_expert_roles"])

    def test_expert_intent_detection_analyst(self):
        query = "What are the historical pollution trends, statistical uncertainty, and CAMS dataset comparisons?"
        result = detect_expert_roles(query)
        self.assertEqual(result["primary_role"], "environmental_analyst")
        self.assertIn("environmental_analyst", result["multi_expert_roles"])

    def test_cross_domain_multi_expert_detection(self):
        query = "Can I ride my bicycle in this high PM2.5 air pollution or take the metro?"
        result = detect_expert_roles(query)
        detected = result["multi_expert_roles"]
        # In a bicycle + PM2.5 query, mobility and/or atmospheric expertise is synthesized
        self.assertTrue(
            "urban_mobility_expert" in detected or "atmospheric_scientist" in detected,
            f"Expected relevant expert in multi-expert list: {detected}"
        )

    def test_manual_expert_override(self):
        # Even with mobility query, explicit role override must take precedence
        result = detect_expert_roles("What is the metro commute route?", requested_role="indoor_air_specialist")
        self.assertEqual(result["primary_role"], "indoor_air_specialist")
        self.assertFalse(result["is_auto_routed"])

    def test_multilingual_intent_detection_hindi(self):
        query = "आज हवा में PM2.5 का स्तर क्या है और वायु गुणवत्ता कैसी है?"
        result = detect_expert_roles(query)
        self.assertEqual(result["primary_role"], "atmospheric_scientist")

    def test_multilingual_intent_detection_bengali(self):
        query = "রান্নার সময় ঘরের বাতাস কীভাবে পরিষ্কার রাখব এবং ভেন্টিলেশন কেমন হওয়া উচিত?"
        result = detect_expert_roles(query)
        self.assertEqual(result["primary_role"], "indoor_air_specialist")

    def test_chat_api_with_expert_routing_english(self):
        payload = {
            "visitor_id": "test-ai-user-en",
            "message": "Explain what PM10 particles are and how to protect against them.",
            "language": "en",
            "expert_role": "auto"
        }
        resp = self.client.post("/api/assistant/chat", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["language"], "en")
        self.assertIn("expert", data)
        self.assertEqual(data["expert"]["id"], "atmospheric_scientist")
        self.assertIn("Atmospheric Scientist", data["expert"]["title"])
        self.assertIn("reply", data)
        self.assertGreater(len(data["reply"]), 20)
        self.assertIn("follow_ups", data)
        self.assertGreaterEqual(len(data["follow_ups"]), 1)

    def test_chat_api_with_expert_routing_hindi(self):
        payload = {
            "visitor_id": "test-ai-user-hi",
            "message": "कार से यात्रा करने पर कितना प्रदूषण होता है और मेट्रो का क्या फायदा है?",
            "language": "hi",
            "expert_role": "auto"
        }
        resp = self.client.post("/api/assistant/chat", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["language"], "hi")
        self.assertIn("expert", data)
        self.assertEqual(data["expert"]["id"], "urban_mobility_expert")
        self.assertIn("शहरी गतिशीलता", data["expert"]["title"])
        self.assertIn("reply", data)
        self.assertGreater(len(data["reply"]), 20)

    def test_chat_api_with_expert_routing_bengali(self):
        payload = {
            "visitor_id": "test-ai-user-bn",
            "message": "রান্নাঘরে এলপিজি ব্যবহারের সময় ইনডোর এয়ার কোয়ালিটি কীভাবে ভালো রাখব?",
            "language": "bn",
            "expert_role": "auto"
        }
        resp = self.client.post("/api/assistant/chat", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["language"], "bn")
        self.assertIn("expert", data)
        self.assertEqual(data["expert"]["id"], "indoor_air_specialist")
        self.assertIn("অভ্যন্তরীণ", data["expert"]["title"])
        self.assertIn("reply", data)
        self.assertGreater(len(data["reply"]), 20)

    def test_multi_turn_conversational_memory(self):
        visitor_id = "test-ai-multiturn-user"
        
        # Turn 1: Ask about air quality in Delhi
        payload1 = {
            "visitor_id": visitor_id,
            "message": "I live in New Delhi. What is the air quality situation right now?",
            "language": "en",
            "expert_role": "auto"
        }
        resp1 = self.client.post("/api/assistant/chat", json=payload1)
        self.assertEqual(resp1.status_code, 200)
        data1 = resp1.get_json()
        self.assertTrue(data1["success"])

        # Turn 2: Natural follow-up without repeating city or context
        payload2 = {
            "visitor_id": visitor_id,
            "message": "Can I go jogging outside this evening?",
            "language": "en",
            "expert_role": "auto"
        }
        resp2 = self.client.post("/api/assistant/chat", json=payload2)
        self.assertEqual(resp2.status_code, 200)
        data2 = resp2.get_json()
        self.assertTrue(data2["success"])
        self.assertIn("reply", data2)
        self.assertGreater(len(data2["reply"]), 20)

if __name__ == "__main__":
    unittest.main()
