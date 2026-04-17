import os
import struct
from mac_rom_tagger import parse_gba_header, parse_iso_header

def create_dummy_gba(path, title, code):
    # GBA header: Title at 0xA0 (12 bytes), Code at 0xAC (4 bytes)
    data = bytearray(200)
    title_bytes = title.encode('ascii')[:12]
    data[0xA0:0xA0+len(title_bytes)] = title_bytes
    code_bytes = code.encode('ascii')[:4]
    data[0xAC:0xAC+len(code_bytes)] = code_bytes
    with open(path, 'wb') as f:
        f.write(data)

def create_dummy_iso(path, title, code):
    # GC header: Code at 0x00 (6 bytes), Title at 0x20 (64 bytes)
    data = bytearray(1024)
    code_bytes = code.encode('ascii')[:6]
    data[0:len(code_bytes)] = code_bytes
    title_bytes = title.encode('ascii')[:64]
    data[0x20:0x20+len(title_bytes)] = title_bytes
    with open(path, 'wb') as f:
        f.write(data)

def test_parsing():
    gba_path = 'test.gba'
    iso_path = 'test.iso'

    try:
        create_dummy_gba(gba_path, "POKEMON EMER", "BPEE")
        title, code = parse_gba_header(gba_path)
        print(f"GBA - Title: '{title}', Code: '{code}'")
        assert title == "POKEMON EMER"
        assert code == "AGB-BPEE"

        create_dummy_iso(iso_path, "Super Mario Sunshine", "GMSJ01")
        title, code = parse_iso_header(iso_path)
        print(f"ISO - Title: '{title}', Code: '{code}'")
        assert title == "Super Mario Sunshine"
        assert code == "GMSJ01"

        print("Parsing tests passed!")

    finally:
        if os.path.exists(gba_path): os.remove(gba_path)
        if os.path.exists(iso_path): os.remove(iso_path)

if __name__ == "__main__":
    test_parsing()
