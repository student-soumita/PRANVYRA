import os
import json
import unittest

class TestI18nDictionaries(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cls.i18n_dir = os.path.join(cls.base_dir, "static", "js", "i18n")
        cls.en_path = os.path.join(cls.i18n_dir, "en.json")
        cls.hi_path = os.path.join(cls.i18n_dir, "hi.json")
        cls.bn_path = os.path.join(cls.i18n_dir, "bn.json")

    def test_translation_files_exist(self):
        self.assertTrue(os.path.exists(self.en_path), "en.json must exist")
        self.assertTrue(os.path.exists(self.hi_path), "hi.json must exist")
        self.assertTrue(os.path.exists(self.bn_path), "bn.json must exist")

    def test_json_parses_validly(self):
        with open(self.en_path, "r", encoding="utf-8") as f:
            en_data = json.load(f)
        with open(self.hi_path, "r", encoding="utf-8") as f:
            hi_data = json.load(f)
        with open(self.bn_path, "r", encoding="utf-8") as f:
            bn_data = json.load(f)

        self.assertIsInstance(en_data, dict)
        self.assertIsInstance(hi_data, dict)
        self.assertIsInstance(bn_data, dict)

    def test_complete_key_parity_across_languages(self):
        with open(self.en_path, "r", encoding="utf-8") as f:
            en_dict = json.load(f)
        with open(self.hi_path, "r", encoding="utf-8") as f:
            hi_dict = json.load(f)
        with open(self.bn_path, "r", encoding="utf-8") as f:
            bn_dict = json.load(f)

        en_keys = set(en_dict.keys())
        hi_keys = set(hi_dict.keys())
        bn_keys = set(bn_dict.keys())

        missing_in_hi = en_keys - hi_keys
        missing_in_bn = en_keys - bn_keys
        extra_in_hi = hi_keys - en_keys
        extra_in_bn = bn_keys - en_keys

        self.assertEqual(len(missing_in_hi), 0, f"Keys in en.json missing in hi.json: {missing_in_hi}")
        self.assertEqual(len(missing_in_bn), 0, f"Keys in en.json missing in bn.json: {missing_in_bn}")
        self.assertEqual(len(extra_in_hi), 0, f"Keys in hi.json missing in en.json: {extra_in_hi}")
        self.assertEqual(len(extra_in_bn), 0, f"Keys in bn.json missing in en.json: {extra_in_bn}")

    def test_no_empty_translations(self):
        for path, lang in [(self.en_path, "en"), (self.hi_path, "hi"), (self.bn_path, "bn")]:
            with open(path, "r", encoding="utf-8") as f:
                d = json.load(f)
            for k, v in d.items():
                self.assertTrue(isinstance(v, str) and len(v.strip()) > 0, 
                                f"Empty or non-string translation for '{k}' in {lang}.json")

    def test_voice_companion_keys_defined(self):
        """Verifies all mandatory voice companion keys exist and are non-empty across EN, HI, BN."""
        required_voice_keys = [
            "voice_input",
            "voice_output",
            "start_listening",
            "stop_listening",
            "listening",
            "processing_voice",
            "speaking",
            "pause_speech",
            "resume_speech",
            "stop_speech",
            "microphone_permission_denied",
            "microphone_not_found",
            "speech_recognition_unsupported",
            "speech_synthesis_unsupported",
            "language_voice_unavailable",
            "voice_input_error",
            "voice_output_error",
            "recognized_text",
            "send_message",
            "voice_privacy_notice"
        ]
        for path, lang in [(self.en_path, "en"), (self.hi_path, "hi"), (self.bn_path, "bn")]:
            with open(path, "r", encoding="utf-8") as f:
                d = json.load(f)
            for vk in required_voice_keys:
                self.assertIn(vk, d, f"Missing voice key '{vk}' in {lang}.json")
                self.assertGreater(len(d[vk].strip()), 0, f"Voice key '{vk}' in {lang}.json cannot be empty")

    def test_expert_roles_keys_defined(self):
        with open(self.en_path, "r", encoding="utf-8") as f:
            en_dict = json.load(f)
        roles = [
            "ai_role_auto",
            "ai_role_atmo",
            "ai_role_mobility",
            "ai_role_indoor",
            "ai_role_sustain",
            "ai_role_analyst"
        ]
        for r in roles:
            self.assertIn(r, en_dict)

if __name__ == "__main__":
    unittest.main()

