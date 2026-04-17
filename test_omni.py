import unittest
from unittest.mock import MagicMock, patch
import os
import json
from omni.core.engine import TranslationEngine, check_byte_safety
from omni.modules.handheld import HandheldModule
from omni.modules.cartridge import CartridgeModule

class TestOmniTranslate(unittest.TestCase):
    def test_byte_safety(self):
        # Case 1: Translation is shorter
        safe, size, limit = check_byte_safety("こんにちは", "Hello")
        self.assertTrue(safe)

        # Case 2: Translation is longer
        # "こんにちは" is 15 bytes in UTF-8
        # This string is longer than 15 bytes
        safe, size, limit = check_byte_safety("こんにちは", "This is a very long translation indeed")
        self.assertFalse(safe)

    @patch('requests.post')
    def test_translation_engine(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "Translated Text"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        engine = TranslationEngine()
        result = engine.translate("こんにちは")
        self.assertEqual(result, "Translated Text")

    def test_cartridge_module_ascii(self):
        # Create a dummy binary file with ASCII text
        test_file = "test_cart.bin"
        with open(test_file, 'wb') as f:
            f.write(b'\x00\x00\x00' + b'HELLO WORLD' + b'\x00\x00')

        module = CartridgeModule(test_file)
        manifest = module.extract_strings()

        self.assertIn('3', manifest)
        self.assertEqual(manifest['3']['original'], 'HELLO WORLD')

        os.remove(test_file)

    def test_handheld_msbt_detection(self):
        # Create a dummy file that is NOT an MSBT
        test_file = "test_not_msbt.msbt"
        with open(test_file, 'wb') as f:
            f.write(b'NOTMSBT')

        module = HandheldModule(test_file)
        with self.assertRaises(ValueError):
            module.extract_strings()

        os.remove(test_file)

if __name__ == '__main__':
    unittest.main()
