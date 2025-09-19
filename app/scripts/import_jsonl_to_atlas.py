# import_jsonl_to_atlas.py
import os, json, datetime, hashlib
from pymongo import MongoClient, InsertOne

from app.core.config import settings

MONGO_URI = settings.MONGO_URI  # p.ej. "mongodb+srv://user:pass@cluster0.abcd.mongodb.net/?retryWrites=true&w=majority"
DB_NAME   = "ner_corpus"
COLL_NAME = "examples"

def import_jsonl(path, dataset_name):
    client = MongoClient(MONGO_URI)
    col = client[DB_NAME][COLL_NAME]

    # Índices (crear una vez)
    col.create_index([("dataset", 1)])
    col.create_index([("spans.label", 1)])
    col.create_index([("dataset", 1), ("line_no", 1)], unique=True)  # evita duplicar importaciones

    bulk = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            obj = json.loads(line)
            labels = sorted({s["label"] for s in obj.get("spans", [])})
            doc = {
                "dataset": dataset_name,
                "line_no": i,
                "text": obj["text"],
                "spans": obj["spans"],
                "labels": labels,
                "char_len": len(obj["text"]),
                "created_at": datetime.datetime.utcnow(),
            }
            bulk.append(InsertOne(doc))
            if len(bulk) >= 1000:
                col.bulk_write(bulk)
                bulk = []
    if bulk:
        col.bulk_write(bulk)
    print(f"OK: importado {path} como dataset='{dataset_name}'")

if __name__ == "__main__":
    import_jsonl("C:/Users/relee/Code/Benedetta/trabajo-grado-v2/backend-v2/app/scripts/train_v2.jsonl", "train_v2")
    import_jsonl("C:/Users/relee/Code/Benedetta/trabajo-grado-v2/backend-v2/app/scripts/train.jsonl", "train_data")
