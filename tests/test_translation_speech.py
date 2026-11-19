"""
PRANVYRA Test Suite — AI Response Translation Pipeline & Per-Message Speech Controls
Tests the complete language flow from frontend→backend→AI→translation→response,
verifies i18n dictionary parity for new speech-control keys,
and validates the translation_service module independently.
"""
import json
import os
import sys
import unittest
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.translation_service import (
    detect_language_mismatch,
    translate_environmental_text,
    translate_structured_card,
    translate_assistant_payload
)


class TestTranslationService(unittest.TestCase):
    """Unit tests for the new translation_service module."""

    def test_detect_english_text_as_hindi_mismatch(self):
        """English text should be detected as mismatch when Hindi is expected."""
        english_text = (
            "The current Air Quality Index for Delhi is 142, categorized as "
            "Unhealthy for Sensitive Groups according to US EPA standards."
        )
        self.assertTrue(detect_language_mismatch(english_text, "hi"))

    def test_detect_english_text_as_bengali_mismatch(self):
        """English text should be detected as mismatch when Bengali is expected."""
        english_text = (
            "Wind speed is 12 km/h and the boundary layer inversion is trapping "
            "ground-level particulate matter near residential corridors."
        )
        self.assertTrue(detect_language_mismatch(english_text, "bn"))

    def test_hindi_text_matches_hindi(self):
        """Hindi text should NOT be flagged as mismatch for Hindi."""
        hindi_text = (
            "वर्तमान में दिल्ली में वायु गुणवत्ता सूचकांक (AQI) लगभग 142 है। "
            "यह US EPA मानक के अनुसार संवेदनशील समूहों के लिए अस्वास्थ्यकर श्रेणी में आता है।"
        )
        self.assertFalse(detect_language_mismatch(hindi_text, "hi"))

    def test_bengali_text_matches_bengali(self):
        """Bengali text should NOT be flagged as mismatch for Bengali."""
        bengali_text = (
            "বর্তমানে দিল্লিতে বায়ু মান সূচক (AQI) প্রায় ১৪২। "
            "এটি US EPA মান অনুযায়ী সংবেদনশীল গোষ্ঠীর জন্য অস্বাস্থ্যকর।"
        )
        self.assertFalse(detect_language_mismatch(bengali_text, "bn"))

    def test_english_text_matches_english(self):
        """English text should NOT be flagged as mismatch for English."""
        english_text = "The AQI is 85, categorized as Moderate by US EPA standards."
        self.assertFalse(detect_language_mismatch(english_text, "en"))

    def test_short_text_no_mismatch(self):
        """Very short or numeric-only text should not trigger false mismatch."""
        self.assertFalse(detect_language_mismatch("AQI: 142", "hi"))
        self.assertFalse(detect_language_mismatch("PM2.5: 45 µg/m³", "bn"))

    def test_heuristic_heading_translation_hindi(self):
        """Known English headings should be replaced in Hindi translation."""
        text = "**Direct Answer:** The AQI is elevated today."
        result = translate_environmental_text(text, "hi")
        self.assertIn("प्रत्यक्ष उत्तर", result)

    def test_heuristic_heading_translation_bengali(self):
        """Known English headings should be replaced in Bengali translation."""
        text = "**Direct Answer:** The AQI is elevated today."
        result = translate_environmental_text(text, "bn")
        self.assertIn("সরাসরি উত্তর", result)

    def test_translate_assistant_payload_success(self):
        """translate_assistant_payload should return success even on heuristic path."""
        text = "**Direct Answer:** PM2.5 levels are high today."
        card = {"recommended_action": "Wear N95 mask", "confidence_level": "High (90%)"}
        result = translate_assistant_payload(text, card, "hi")
        self.assertTrue(result["success"])
        self.assertIn("text", result)
        self.assertEqual(result["language"], "hi")

    def test_translate_structured_card_preserves_keys(self):
        """Card translation must never change JSON keys."""
        card = {
            "recommended_action": "Take the Metro",
            "problem_identified": "Tailpipe emissions",
            "confidence_level": "High (95%)",
            "source": "UK DEFRA 2023"
        }
        result = translate_structured_card(card, "hi")
        self.assertIn("recommended_action", result)
        self.assertIn("problem_identified", result)
        self.assertIn("confidence_level", result)
        self.assertIn("source", result)

    def test_no_translation_when_already_correct(self):
        """If text is already in the target language, return it unchanged."""
        hindi_text = "प्रत्यक्ष उत्तर: AQI 142 है।"
        result = translate_environmental_text(hindi_text, "hi")
        self.assertEqual(result, hindi_text)


class TestI18nSpeechControlKeys(unittest.TestCase):
    """Verifies all new speech-control i18n keys exist in EN, HI, and BN dictionaries."""

    REQUIRED_KEYS = [
        "play_response", "stop_speaking", "pause_speaking", "resume_speaking",
        "stop_all_speech", "speaking", "speech_paused", "speech_stopped",
        "translating_response", "response_translation_failed",
        "language_voice_unavailable", "translate_this"
    ]

    @classmethod
    def setUpClass(cls):
        cls.dicts = {}
        for lang in ("en", "hi", "bn"):
            path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "static", "js", "i18n", f"{lang}.json")
            with open(path, "r", encoding="utf-8") as f:
                cls.dicts[lang] = json.load(f)

    def test_all_speech_keys_present_en(self):
        for key in self.REQUIRED_KEYS:
            self.assertIn(key, self.dicts["en"], f"EN missing key: {key}")
            self.assertTrue(len(self.dicts["en"][key]) > 0, f"EN key '{key}' is empty")

    def test_all_speech_keys_present_hi(self):
        for key in self.REQUIRED_KEYS:
            self.assertIn(key, self.dicts["hi"], f"HI missing key: {key}")
            self.assertTrue(len(self.dicts["hi"][key]) > 0, f"HI key '{key}' is empty")

    def test_all_speech_keys_present_bn(self):
        for key in self.REQUIRED_KEYS:
            self.assertIn(key, self.dicts["bn"], f"BN missing key: {key}")
            self.assertTrue(len(self.dicts["bn"][key]) > 0, f"BN key '{key}' is empty")

    def test_dictionary_parity(self):
        """All three dictionaries must have the exact same set of keys."""
        en_keys = set(self.dicts["en"].keys())
        hi_keys = set(self.dicts["hi"].keys())
        bn_keys = set(self.dicts["bn"].keys())
        self.assertEqual(en_keys, hi_keys, f"EN-HI key mismatch: {en_keys.symmetric_difference(hi_keys)}")
        self.assertEqual(en_keys, bn_keys, f"EN-BN key mismatch: {en_keys.symmetric_difference(bn_keys)}")


class TestTrilingualChatResponse(unittest.TestCase):
    """Tests AI chat API for proper language in responses across EN, HI, BN."""

    @classmethod
    def setUpClass(cls):
        from app import create_app
        cls.app = create_app()
        cls.client = cls.app.test_client()
        import uuid
        email = f"lang_test_{uuid.uuid4().hex[:8]}@pranvyra.org"
        reg_resp = cls.client.post("/api/auth/register", json={
            "full_name": "Lang Test Citizen",
            "email": email,
            "password": "Password123!"
        })
        assert reg_resp.status_code == 201 or reg_resp.get_json().get("success")

    def _send_chat(self, message, language):
        return self.client.post("/api/assistant/chat", json={
            "message": message,
            "language": language,
            "expert_role": "auto"
        })

    def test_english_response(self):
        resp = self._send_chat("What is the current AQI?", "en")
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["language"], "en")
        self.assertIsNotNone(data["reply"])
        self.assertGreater(len(data["reply"]), 20)

    def test_hindi_response_contains_devanagari(self):
        resp = self._send_chat("वर्तमान वायु गुणवत्ता क्या है?", "hi")
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["language"], "hi")
        reply = data["reply"]
        # The fallback engine generates Hindi responses natively
        devanagari_count = len(re.findall(r'[\u0900-\u097F]', reply))
        self.assertGreater(devanagari_count, 10, f"Hindi response has too little Devanagari: {reply[:100]}")

    def test_bengali_response_contains_bengali_script(self):
        resp = self._send_chat("বর্তমান বায়ুর মান কেমন?", "bn")
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["language"], "bn")
        reply = data["reply"]
        bengali_count = len(re.findall(r'[\u0980-\u09FF]', reply))
        self.assertGreater(bengali_count, 10, f"Bengali response has too little Bengali script: {reply[:100]}")

    def test_response_includes_translation_flags(self):
        """Response must include was_translated and translation_failed fields."""
        resp = self._send_chat("How to reduce PM2.5?", "en")
        data = resp.get_json()
        self.assertIn("was_translated", data)
        self.assertIn("translation_failed", data)

    def test_semantic_precaution_queries_multilingual(self):
        """
        Validates the 3 mandatory semantic test queries:
        EN: What precautions should I take when AQI is unhealthy?
        HI: जब AQI खराब हो तो मुझे क्या सावधानियां रखनी चाहिए?
        BN: AQI খারাপ থাকলে আমার কী কী সতর্কতা নেওয়া উচিত?
        """
        # 1. English
        resp_en = self._send_chat("What precautions should I take when AQI is unhealthy?", "en")
        data_en = resp_en.get_json()
        self.assertTrue(data_en["success"])
        self.assertIn("Direct Answer", data_en["reply"])
        self.assertIn("N95", data_en["reply"])
        card_en = data_en.get("structured_card")
        self.assertIsNotNone(card_en)
        self.assertIn("N95", card_en.get("recommended_action", ""))

        # 2. Hindi
        resp_hi = self._send_chat("जब AQI खराब हो तो मुझे क्या सावधानियां रखनी चाहिए?", "hi")
        data_hi = resp_hi.get_json()
        self.assertTrue(data_hi["success"])
        reply_hi = data_hi["reply"]
        dev_count = len(re.findall(r'[\u0900-\u097F]', reply_hi))
        self.assertGreater(dev_count, 100, f"Hindi response has insufficient Devanagari: {reply_hi[:100]}")
        self.assertFalse(detect_language_mismatch(reply_hi, "hi"))
        card_hi = data_hi.get("structured_card")
        self.assertIsNotNone(card_hi)
        card_dev = len(re.findall(r'[\u0900-\u097F]', card_hi.get("problem_identified", "")))
        self.assertGreater(card_dev, 5, "Hindi card problem_identified must be in Hindi script")

        # 3. Bengali
        resp_bn = self._send_chat("AQI খারাপ থাকলে আমার কী কী সতর্কতা নেওয়া উচিত?", "bn")
        data_bn = resp_bn.get_json()
        self.assertTrue(data_bn["success"])
        reply_bn = data_bn["reply"]
        bn_count = len(re.findall(r'[\u0980-\u09FF]', reply_bn))
        self.assertGreater(bn_count, 100, f"Bengali response has insufficient Bengali script: {reply_bn[:100]}")
        self.assertFalse(detect_language_mismatch(reply_bn, "bn"))
        card_bn = data_bn.get("structured_card")
        self.assertIsNotNone(card_bn)
        card_bn_cnt = len(re.findall(r'[\u0980-\u09FF]', card_bn.get("problem_identified", "")))
        self.assertGreater(card_bn_cnt, 5, "Bengali card problem_identified must be in Bengali script")

    def test_follow_ups_match_language(self):
        """Follow-up suggestions should be in the requested language."""
        resp = self._send_chat("मेट्रो या स्कूटर, कौन बेहतर है?", "hi")
        data = resp.get_json()
        self.assertTrue(data["success"])
        if data.get("follow_up_suggestions"):
            for suggestion in data["follow_up_suggestions"]:
                # Hindi follow-ups should contain some Devanagari
                dev = len(re.findall(r'[\u0900-\u097F]', suggestion))
                self.assertGreater(dev, 2, f"Follow-up not in Hindi: {suggestion}")


class TestFrontendSpeechControls(unittest.TestCase):
    """Verifies that the HTML and JS source contain the required speech control elements."""

    @classmethod
    def setUpClass(cls):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(base, "templates", "index.html"), "r", encoding="utf-8") as f:
            cls.html = f.read()
        with open(os.path.join(base, "static", "js", "assistant.js"), "r", encoding="utf-8") as f:
            cls.js = f.read()
        with open(os.path.join(base, "static", "css", "modules.css"), "r", encoding="utf-8") as f:
            cls.css = f.read()

    def test_global_stop_all_speech_button_exists(self):
        self.assertIn('chatStopAllSpeechBtn', self.html)

    def test_per_message_play_button_in_js(self):
        self.assertIn('btn-play-msg', self.js)

    def test_per_message_stop_button_in_js(self):
        self.assertIn('btn-stop-msg', self.js)

    def test_per_message_pause_button_in_js(self):
        self.assertIn('btn-pause-msg', self.js)

    def test_per_message_resume_button_in_js(self):
        self.assertIn('btn-resume-msg', self.js)

    def test_setMsgControlState_function_exists(self):
        self.assertIn('setMsgControlState', self.js)

    def test_msg_speech_controls_css(self):
        self.assertIn('.msg-speech-controls', self.css)
        self.assertIn('.btn-msg-ctrl', self.css)

    def test_global_stop_button_css(self):
        self.assertIn('.btn-stop-all-speech', self.css)

    def test_mini_wave_indicator_css(self):
        self.assertIn('.mini-wave-bar', self.css)
        self.assertIn('miniWaveAnim', self.css)

    def test_translation_banner_css(self):
        self.assertIn('.translation-info-banner', self.css)
        self.assertIn('.translation-warning-banner', self.css)

    def test_was_translated_passed_in_js(self):
        self.assertIn('wasTranslated', self.js)
        self.assertIn('translationFailed', self.js)


class TestWelcomeLandingPage(unittest.TestCase):
    """Verifies that the /welcome post-login branded landing page works securely and responsively."""

    @classmethod
    def setUpClass(cls):
        from app import create_app
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.app.config["WTF_CSRF_ENABLED"] = False

    def setUp(self):
        """Create a fresh test client for each test to avoid session pollution."""
        self.client = self.app.test_client()

    def test_unauthenticated_welcome_redirects_to_login(self):
        """Unauthenticated requests to /welcome must be redirected to /login."""
        resp = self.client.get("/welcome", follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers["Location"])

    def test_authenticated_welcome_renders_landing_page(self):
        """Authenticated users must see the PRANVYRA branded landing experience."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 9999
            sess["username"] = "welcome_tester"

        resp = self.client.get("/welcome")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("PRANVYRA", html)
        self.assertIn("Every Breath. A Better Tomorrow.", html)
        self.assertIn("landing_cta_explore", html)
        self.assertIn("landing_cta_dashboard", html)
        self.assertIn("cosmic-orb", html)
        self.assertIn("bhasha-pill-group", html)

    def test_welcome_html_file_structure(self):
        """Ensure templates/welcome.html contains cosmic design system elements."""
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(base, "templates", "welcome.html"), "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("welcome-card", content)
        self.assertIn("feature-card", content)
        self.assertIn("btn-explore", content)
        self.assertIn("btn-dashboard", content)
        self.assertIn("logo.svg", content)

    def test_cinematic_scenes_and_script_elements(self):
        """Ensure all 5 cinematic narrative scenes and motion controls exist in templates/welcome.html."""
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(base, "templates", "welcome.html"), "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("atmosphericCanvas", content)
        self.assertIn('id="scene-1"', content)
        self.assertIn('id="scene-2"', content)
        self.assertIn('id="scene-3"', content)
        self.assertIn('id="scene-4"', content)
        self.assertIn('id="scene-5"', content)
        self.assertIn("landing_story_quote", content)
        self.assertIn("landing_story_sub", content)
        self.assertIn("landing_transform_badge", content)
        self.assertIn("soundToggleBtn", content)
        self.assertIn("timelineSteps", content)
        self.assertIn("skipBtn", content)
        self.assertIn("replayBtn", content)

    def test_cinematic_i18n_keys_in_all_locales(self):
        """Ensure English, Hindi, and Bengali translation files define cinematic landing keys."""
        import json
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        keys = [
            "landing_story_quote",
            "landing_story_sub",
            "landing_transform_title",
            "landing_transform_desc",
            "landing_experience_support",
            "landing_sound_on",
            "landing_sound_off",
            "landing_skip",
            "landing_replay"
        ]
        for locale in ["en", "hi", "bn"]:
            path = os.path.join(base, "static", "js", "i18n", f"{locale}.json")
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for k in keys:
                self.assertIn(k, data, f"Key '{k}' missing from locale '{locale}.json'")
                self.assertTrue(len(data[k]) > 0, f"Key '{k}' is empty in locale '{locale}.json'")


if __name__ == '__main__':
    unittest.main()
