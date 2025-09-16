import argparse, json, random, os
from pathlib import Path
from typing import List, Dict, Tuple
import spacy
from spacy.util import minibatch, compounding
from spacy.training import Example

def load_jsonl(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(l) for l in f]

def to_examples(nlp, data):
    examples = []
    for eg in data:
        doc = nlp.make_doc(eg["text"])
        ents = []
        for s in eg["spans"]:
            span = doc.char_span(s["start"], s["end"], label=s["label"], alignment_mode="contract")
            if span is not None:
                ents.append((span.start_char, span.end_char, span.label_))
        examples.append(Example.from_dict(doc, {"entities": ents}))
    return examples

def _prf_from_scorer(scorer):
    """
    Devuelve (p, r, f) robusto para spaCy 3.x:
    - Si es objeto con atributos -> usa .ents_p/.ents_r/.ents_f
    - Si tiene .scores -> usa .scores['ents_*']
    - Si es dict -> usa claves directas
    """
    # Caso 1: objeto con atributos
    if hasattr(scorer, "ents_f") and hasattr(scorer, "ents_p") and hasattr(scorer, "ents_r"):
        return float(scorer.ents_p or 0), float(scorer.ents_r or 0), float(scorer.ents_f or 0)
    # Caso 2: objeto con .scores
    scores = getattr(scorer, "scores", None)
    if isinstance(scores, dict):
        p = float(scores.get("ents_p", 0) or 0)
        r = float(scores.get("ents_r", 0) or 0)
        f = float(scores.get("ents_f", 0) or 0)
        return p, r, f
    # Caso 3: dict directo
    if isinstance(scorer, dict):
        p = float(scorer.get("ents_p", 0) or 0)
        r = float(scorer.get("ents_r", 0) or 0)
        f = float(scorer.get("ents_f", 0) or 0)
        return p, r, f
    # Fallback
    return 0.0, 0.0, 0.0

def main():
    ap = argparse.ArgumentParser(description="Train spaCy NER with physiotherapy domain labels.")
    ap.add_argument("--train", required=True, help="Path to JSONL with training data (text + spans).")
    ap.add_argument("--output", default="model_trained", help="Output directory for the trained model.")
    ap.add_argument("--base", default="es_core_news_md", help="Base pipeline to start from.")
    ap.add_argument("--mode", choices=["extend","fresh"], default="extend",
                    help="extend: keep existing NER and add labels; fresh: build a brand-new NER.")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--split", type=float, default=0.8, help="Train/dev split ratio.")
    ap.add_argument("--n_iter", type=int, default=30)
    ap.add_argument("--dropout", type=float, default=0.2)
    ap.add_argument("--lr", type=float, default=0.001)
    ap.add_argument("--batch_min", type=float, default=4.0)
    ap.add_argument("--batch_max", type=float, default=32.0)
    args = ap.parse_args()

    random.seed(args.seed)

    data = load_jsonl(args.train)
    if not data:
        raise ValueError(f"No data found in {args.train}")
    random.shuffle(data)
    k = int(len(data) * args.split)
    train_data = data[:k]
    dev_data = data[k:] if k < len(data) else data[:]

    # Load base pipeline
    if args.mode == "fresh":
        nlp = spacy.load(args.base)
        if "ner" in nlp.pipe_names:
            nlp.remove_pipe("ner")
        if "entity_ruler" in nlp.pipe_names:
            nlp.remove_pipe("entity_ruler")
        # Ahora sí, crea un NER nuevo (puedes usar un nombre distinto para evitar colisiones)
        ner = nlp.add_pipe("ner")  # ó: ner = nlp.add_pipe("ner", name="ner_domain")
        target_ner_name = ner.name
    else:
        nlp = spacy.load(args.base)
        # Reutiliza si existe; crea si no
        if "ner" in nlp.pipe_names:
            ner = nlp.get_pipe("ner")
        else:
            ner = nlp.add_pipe("ner")
        target_ner_name = ner.name

    # Collect labels and add to NER
    labels = sorted({s["label"] for eg in data for s in eg["spans"]})
    for label in labels:
        ner.add_label(label)

    # Convert to Examples
    train_examples = to_examples(nlp, train_data)
    dev_examples = to_examples(nlp, dev_data)

    # Optimizer
    if args.mode == "fresh" or target_ner_name not in nlp.pipe_names:
        optimizer = nlp.initialize(get_examples=lambda: train_examples)
    else:
        optimizer = nlp.resume_training()
    try:
        optimizer.learn_rate = args.lr
    except Exception:
        pass

    other_pipes = [p for p in nlp.pipe_names if p != target_ner_name]
    with nlp.disable_pipes(*other_pipes):
        for i in range(args.n_iter):
            losses = {}
            random.shuffle(train_examples)
            batches = spacy.util.minibatch(
                train_examples, size=spacy.util.compounding(args.batch_min, args.batch_max, 1.001)
            )
            for batch in batches:
                nlp.update(batch, sgd=optimizer, drop=args.dropout, losses=losses)
            scorer = nlp.evaluate(dev_examples)
            p, r, f = _prf_from_scorer(scorer)  # usa tu helper robusto de métricas
            print(f"Iter {i+1}/{args.n_iter}  Losses: {losses}  Dev F1: {f:.4f}  (P={p:.4f}, R={r:.4f})")

    out_dir = Path(args.output); out_dir.mkdir(parents=True, exist_ok=True)
    nlp.to_disk(out_dir)
    print(f"✅ Model saved to {out_dir.resolve()}")

    # Save final metrics
    final_scorer = nlp.evaluate(dev_examples) if dev_examples else None
    p, r, f = _prf_from_scorer(final_scorer) if final_scorer else (None, None, None)
    metrics = {
        "labels": labels,
        "n_train": len(train_examples),
        "n_dev": len(dev_examples),
        "ents_p": p,
        "ents_r": r,
        "ents_f": f,
    }
    with open(out_dir / "training_metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    print(f"📊 Metrics saved to {str(out_dir / 'training_metrics.json')}")

if __name__ == "__main__":
    main()