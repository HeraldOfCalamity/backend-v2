from typing import Any, Dict, List

from app.core.nlp import get_nlp
from app.infrastructure.schemas.historial import NerSpan


def extract_ner(text: str) -> Dict[str, List[str]]:
    if not text:
        return {}
    
    nlp = get_nlp()
    doc = nlp(text)

    out: Dict[str, List[str]] = {}

    for ent in doc.ents:
        label = ent.label_
        value = ent._.norm_label or ent.text
        bucket = out.setdefault(label, [])
        if value not in bucket:
            bucket.append(value)

    return out

def extract_ner_spans(text: str) -> List[Dict[str, any]]:
    if not text: 
        return []
    
    nlp = get_nlp()
    doc = nlp(text)
    return [
        {"text": e.text, "label": e.label_, "start": e.start_char, "end": e.end_char, "norm": e._.norm_label}
        for e in doc.ents
    ]

def spans_to_models(spans: List[Dict[str, Any]]) -> List[NerSpan]:
    out: List[NerSpan] = []
    for s in spans:
        out.append(NerSpan(
            label=s["label"],
            text=s["text"],
            start=int(s["start"]),
            end=int(s["end"]),
            norm=s.get("norm"),
            source="rules",
            confidence=None
        ))
    return out