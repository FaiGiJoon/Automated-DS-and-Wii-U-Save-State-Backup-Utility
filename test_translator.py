import unittest
from unittest.mock import MagicMock, patch
import translator

class TestTranslator(unittest.TestCase):
    @patch('mss.mss')
    def test_capture_screen(self, mock_mss):
        # Mock mss.mss().grab() to return a mock object with .bgra and .size
        mock_sct = mock_mss.return_value.__enter__.return_value
        mock_img = MagicMock()
        mock_img.bgra = b'\x00\x00\x00\x00' * (10 * 10)
        mock_img.size = (10, 10)
        mock_sct.grab.return_value = mock_img

        app = translator.TranslatorApp(setup_ui=False)
        # Mock window bounds
        app.window_bounds = {'X': 100, 'Y': 200, 'Width': 800, 'Height': 600}

        result = app.capture_screen()

        self.assertEqual(result.size, (10, 10))
        # Expected coordinates: base_x + offset_left, base_y + offset_top
        # Default offsets: left=100, top=400
        # Expected: left=200, top=600
        args, kwargs = mock_sct.grab.call_args
        monitor = args[0]
        self.assertEqual(monitor['left'], 200)
        self.assertEqual(monitor['top'], 600)

    @patch('pytesseract.image_to_string')
    def test_perform_ocr(self, mock_ocr):
        mock_ocr.return_value = "  こんにちは  "
        app = translator.TranslatorApp(setup_ui=False)

        result = app.perform_ocr(MagicMock())
        self.assertEqual(result, "こんにちは")
        mock_ocr.assert_called_once()

    @patch('requests.post')
    def test_translate_text(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "Hello"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        app = translator.TranslatorApp(setup_ui=False)
        result = app.translate_text("こんにちは")

        self.assertEqual(result, "Hello")
        mock_post.assert_called_once()

    def test_load_config_defaults(self):
        app = translator.TranslatorApp(setup_ui=False)
        self.assertEqual(app.config["emulator_name"], "Cemu")

if __name__ == '__main__':
    unittest.main()
