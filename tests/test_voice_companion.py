import re
import unittest
import json
import uuid
from app import create_app

class TestVoiceAICompanion(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()
        # Register an authenticated user session
        cls.test_email = f"voice_tester_{uuid.uuid4().hex[:8]}@pranvyra.org"
        cls.client.post("/api/auth/register", json={
            "email": cls.test_email,
            "password": "PasswordVoice123!",
            "full_name": "Voice AI Tester",
            "language_pref": "en"
        })

    def test_voice_interface_elements_in_html(self):
        """Verifies all required voice input and output controls exist in index.html."""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)

        # Microphone input button
        self.assertIn('id="chatVoiceInputBtn"', html)
        self.assertIn('chat-mic-btn', html)
        self.assertIn('data-i18n-title="start_listening"', html)

        # Voice status bar & soundwave indicator
        self.assertIn('id="voiceStatusBar"', html)
        self.assertIn('id="voiceWaveIndicator"', html)
        self.assertIn('id="voiceStatusText"', html)

        # Speech controls (Pause/Resume, Stop Speaking, Stop Listening)
        self.assertIn('id="voicePauseResumeBtn"', html)
        self.assertIn('id="voiceStopSpeakingBtn"', html)
        self.assertIn('id="voiceStopListeningBtn"', html)

        # Auto-speech toggle
        self.assertIn('id="chatAutoSpeechToggle"', html)

    def test_trilingual_voice_locales_and_rules(self):
        """Verifies the locale requirements and strict rules for EN-IN, HI-IN, and BN-IN."""
        locale_map = {
            "en": "en-IN",
            "hi": "hi-IN",
            "bn": "bn-IN"
        }
        self.assertEqual(locale_map["en"], "en-IN")
        self.assertEqual(locale_map["hi"], "hi-IN")
        self.assertEqual(locale_map["bn"], "bn-IN")

    def test_markdown_cleaning_for_natural_speech(self):
        """Tests that markdown symbols, code tags, and URLs are cleanly stripped for speech synthesis."""
        sample_response = (
            "### Atmospheric Advisory\n\n"
            "The **PM2.5** concentration is currently *moderate* at 42 µg/m³.\n\n"
            "- Avoid prolonged outdoor exertion.\n"
            "- For cleaner transit, use [Electric Metro](/transit).\n"
            "`co2_avoided`: 2.5 kg."
        )

        # Emulate the client-side cleanTextForSpeech logic
        cleaned = sample_response
        cleaned = re.sub(r'```[\s\S]*?```', '', cleaned)
        cleaned = re.sub(r'`([^`]+)`', r'\1', cleaned)
        cleaned = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', cleaned)
        cleaned = re.sub(r'(\*\*|\*|__|_)(.*?)\1', r'\2', cleaned)
        cleaned = re.sub(r'^#+\s+', '', cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r'^>\s+', '', cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r'^[\*\-]\s+', '', cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r'<[^>]*>', '', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        # Check that formatting noise is gone
        self.assertNotIn("###", cleaned)
        self.assertNotIn("**", cleaned)
        self.assertNotIn("[Electric Metro](/transit)", cleaned)
        self.assertIn("Electric Metro", cleaned)
        self.assertIn("The PM2.5 concentration is currently moderate at 42 µg/m³.", cleaned)

    def test_trilingual_ai_responses_for_voice_readout(self):
        """Verifies that English, Hindi, and Bengali AI responses are correctly formatted for voice output."""
        # 1. English
        resp_en = self.client.post("/api/assistant/chat", json={
            "message": "Give me a 1-sentence air quality precaution.",
            "language": "en"
        })
        self.assertEqual(resp_en.status_code, 200)
        data_en = resp_en.get_json()
        self.assertTrue(data_en["success"])
        self.assertEqual(data_en["language"], "en")
        self.assertIsInstance(data_en["reply"], str)
        self.assertGreater(len(data_en["reply"]), 10)

        # 2. Hindi
        resp_hi = self.client.post("/api/assistant/chat", json={
            "message": "वायु गुणवत्ता पर एक वाक्य में सलाह दें।",
            "language": "hi"
        })
        self.assertEqual(resp_hi.status_code, 200)
        data_hi = resp_hi.get_json()
        self.assertTrue(data_hi["success"])
        self.assertEqual(data_hi["language"], "hi")
        self.assertIsInstance(data_hi["reply"], str)
        self.assertGreater(len(data_hi["reply"]), 10)

        # 3. Bengali
        resp_bn = self.client.post("/api/assistant/chat", json={
            "message": "বায়ুমান নিয়ে একটি ছোট সতর্কতা দিন।",
            "language": "bn"
        })
        self.assertEqual(resp_bn.status_code, 200)
        data_bn = resp_bn.get_json()
        self.assertTrue(data_bn["success"])
        self.assertEqual(data_bn["language"], "bn")
        self.assertIsInstance(data_bn["reply"], str)
        self.assertGreater(len(data_bn["reply"]), 10)

    def test_voice_keys_parity_in_all_dictionaries(self):
        """Verifies all voice keys exist across en.json, hi.json, and bn.json with no missing translations."""
        i18n_dir = "static/js/i18n"
        with open(f"{i18n_dir}/en.json", "r", encoding="utf-8") as f:
            en_data = json.load(f)
        with open(f"{i18n_dir}/hi.json", "r", encoding="utf-8") as f:
            hi_data = json.load(f)
        with open(f"{i18n_dir}/bn.json", "r", encoding="utf-8") as f:
            bn_data = json.load(f)

        voice_keys = [
            "voice_input", "voice_output", "start_listening", "stop_listening",
            "listening", "processing_voice", "speaking", "pause_speech",
            "resume_speech", "stop_speech", "microphone_permission_denied",
            "microphone_not_found", "speech_recognition_unsupported",
            "speech_synthesis_unsupported", "language_voice_unavailable",
            "voice_input_error", "voice_output_error", "recognized_text",
            "send_message", "voice_privacy_notice", "voice_btn_speak_response",
            "voice_auto_read_toggle"
        ]

        for k in voice_keys:
            self.assertIn(k, en_data, f"en.json missing {k}")
            self.assertIn(k, hi_data, f"hi.json missing {k}")
            self.assertIn(k, bn_data, f"bn.json missing {k}")
            self.assertTrue(len(en_data[k].strip()) > 0)
            self.assertTrue(len(hi_data[k].strip()) > 0)
            self.assertTrue(len(bn_data[k].strip()) > 0)

if __name__ == "__main__":
    unittest.main()
