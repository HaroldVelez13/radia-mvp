import eml_parser

def parse_eml(path: str):
    # T1.1
    with open(path, 'rb') as f:
        raw = f.read()
    parsed = eml_parser.EmlParser().decode_email_bytes(raw)
    return parsed
