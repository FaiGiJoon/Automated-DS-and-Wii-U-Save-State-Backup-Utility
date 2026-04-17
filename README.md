# Automated-DS-and-Wii-U-Save-State-Backup-Utility
The Automated DS and Wii U Save-State Backup Utility is a localized version-control service designed to protect and manage emulation progress. Unlike standard emulator saves, which often overwrite the same file repeatedly, this utility creates a historical record of gameplay states.

## Game Translator Utility

Included is `translator.py`, a macOS-focused utility that provides a real-time English overlay for Japanese games.

### Features
- Real-time screen capture of a defined region.
- Japanese OCR using Tesseract.
- Natural English translation via local LLM (Ollama).
- Transparent, always-on-top floating window that tracks the emulator window.

### Prerequisites (macOS)
1. Install Tesseract and Japanese language data:
   ```bash
   brew install tesseract tesseract-lang
   ```
2. Install Ollama and pull a model (e.g., llama3):
   ```bash
   ollama pull llama3
   ```
3. Install Python dependencies:
   ```bash
   pip install pytesseract mss requests Pillow pyobjc-framework-Quartz
   ```

### Usage
1. Configure your settings in `config.json` (optional):
   ```json
   {
       "emulator_name": "Cemu",
       "ocr_region_offset": {"top": 400, "left": 100, "width": 600, "height": 150},
       "ollama_model": "llama3"
   }
   ```
2. Run the translator:
   ```bash
   python translator.py
   ```
3. The overlay will appear and track the specified emulator window. Press `Esc` to quit.

## Omni-Translate Framework

The Omni-Translate framework is a modular system for automating the translation of Nintendo ROMs across multiple generations.

### Platforms Supported
- **Cartridge (NES, SNES, N64):** Binary scanning with custom TBL (table) file support.
- **Disc (GameCube, Wii):** Shift-JIS string extraction and injection.
- **Handheld (3DS, Wii U):** MSBT (Message Binary Text) parser and injector.

### Features
- **Manifest-based workflow:** Strings are extracted into a JSON manifest, allowing for manual review and avoiding redundant LLM calls.
- **Byte-safety:** Injections are length-checked to ensure ROM stability and prevent data shifting.
- **Context-aware translation:** Uses local Ollama LLM to provide natural translations.

### Usage (Omni-Translate)
1. **Extract strings:**
   ```bash
   python omni.py --platform handheld --file game.msbt
   ```
2. **Translate strings (requires Ollama):**
   ```bash
   python omni.py --platform handheld --file game.msbt --translate
   ```
3. **Inject translations:**
   ```bash
   python omni.py --platform handheld --file game.msbt --inject --output translated.msbt
   ```

For cartridge-based games with custom encoding, provide a `.tbl` file:
```bash
python omni.py --platform cartridge --file game.nes --tbl japanese.tbl
```
