# iniciar servidor
uvicorn app.main:app --reload

# Entrenar modelo
python -m eval_model

# Extender el NER existente (por defecto)
python -m app.scripts.train_model --train app/scripts/train.jsonl --output app/scripts/model_trained --mode extend
python -m app.scripts.train_model --train app/scripts/train.jsonl --output app/scripts/model_trained --mode extend --dropout 0.4 --n_iter 10

# O crear un NER nuevo desde cero
python -m app.scripts.train_model --train app/scripts/train.jsonl --output app/scripts/model_trained --mode fresh