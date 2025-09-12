from functools import lru_cache
from app.application.services.pt_ner_rules import build_pt_pipeline

@lru_cache(maxsize=1)
def get_nlp():
    return build_pt_pipeline()
