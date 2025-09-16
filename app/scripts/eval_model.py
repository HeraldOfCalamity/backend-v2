import json, spacy, os
from typing import List, Dict, Tuple, Set
from pathlib import Path

# Import the rules pipeline builder
from app.application.services import pt_ner_rules

DOMAIN_LABELS: Set[str] = {
    "SYMPTOM","PAIN_QUALITY","PAIN_INTENSITY","BODY_PART","MOVEMENT",
    "FUNCTIONAL_LIMITATION","DIAGNOSIS","TREATMENT","EXERCISE","FREQUENCY",
    "SCALE","MEASURE","DURATION","ROM","LATERALITY","TEST"
}

def load_gold(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(l) for l in f]

def spans_from_doc(doc) -> List[Tuple[int,int,str]]:
    out = []
    for e in doc.ents:
        if e.label_ in DOMAIN_LABELS:
            out.append((e.start_char, e.end_char, e.label_))
    return out

def score(preds: List[List[Tuple[int,int,str]]], golds: List[List[Tuple[int,int,str]]]) -> Dict[str, float]:
    # exact match on (start,end,label)
    tp = 0
    fp = 0
    fn = 0
    for p, g in zip(preds, golds):
        p_set = set(p)
        g_set = set(g)
        tp += len(p_set & g_set)
        fp += len(p_set - g_set)
        fn += len(g_set - p_set)
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec  = tp / (tp + fn) if (tp + fn) else 0.0
    f1   = 2*prec*rec/(prec+rec) if (prec+rec) else 0.0
    return {"precision": round(prec,4), "recall": round(rec,4), "f1": round(f1,4), "tp": tp, "fp": fp, "fn": fn}

def eval_model(nlp, gold):
    preds = []
    golds = []
    for eg in gold:
        doc = nlp(eg["text"])
        preds.append(spans_from_doc(doc))
        golds.append([(s["start"], s["end"], s["label"]) for s in eg["spans"]])
    return score(preds, golds)

def main():
    gold = load_gold("C:/Users/relee/Code/Benedetta/trabajo-grado-v2/backend-v2/app/scripts/gold_fixed.jsonl")

    # 1) Baseline ML (generic Spanish NER)
    try:
        ml = spacy.load("es_core_news_md")  # will likely not contain your domain labels
    except Exception as e:
        print("Baseline ML not available:", e)
        ml = None

    # 2) Rules pipeline (entity_ruler)
    try:
        rules = pt_ner_rules.build_pt_pipeline()
    except Exception as e:
        print("Rules pipeline could not be built:", e)
        rules = None

    # 3) Trained model (if present)
    model_dir = os.environ.get("BENEDDETTA_MODEL_DIR", "C:/Users/relee/Code/Benedetta/trabajo-grado-v2/backend-v2/app/scripts/model_trained_v2")
    trained = None
    if Path(model_dir).exists():
        try:
            trained = spacy.load(model_dir)
        except Exception as e:
            print("Trained model could not be loaded:", e)
            trained = None
    else:
        print(f"Trained model directory not found: {model_dir}")

    results = {}
    if ml:
        results["baseline_ml"] = eval_model(ml, gold)
    if rules:
        results["rules"] = eval_model(rules, gold)
    if trained:
        results["trained"] = eval_model(trained, gold)

    print(json.dumps(results, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()