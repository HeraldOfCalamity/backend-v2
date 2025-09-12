import spacy
nlp = spacy.load("es_core_news_md")
ruler = nlp.add_pipe("entity_ruler", before="ner")
ruler.add_patterns([{"label":"SYMPTOM","pattern":"dolor de cabeza"}])
doc = nlp("Paciente con dolor de cabeza y fiebre.")
print([(ent.text, ent.label_) for ent in doc.ents])