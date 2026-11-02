import re
import unicodedata

def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value)
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()

def tokenize(value: str) -> list[str]:
    return [token for token in re.findall(r"\w{4,}", value.casefold())]
