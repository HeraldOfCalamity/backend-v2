# app/application/services/pt_ner_rules.py

from typing import Dict, Iterable, List
import spacy
from spacy.language import Language
from spacy.tokens import Span

# ===================== Listas dominio fisioterapia/kinesiología =====================

SYMPTOMS = [
    "dolor", "rigidez", "pesadez", "parestesias", "hormigueo", "calambres",
    "debilidad", "inflamación", "edema", "inestabilidad", "bloqueo", "chirridos",
    "crepitación", "limitación", "fatiga", "contractura", "espasmo",
    "mareos", "cefalea", "vértigo", 
]

PAIN_QUALITY = [
    "punzante","sordo","quemante","ardor","opresivo","lancinante",
    "urente","cortante","palpitante","difuso","localizado"
]

PAIN_INTENSITY = [
    "leve","moderado","moderada","severo","severa","intenso","intensa",
    "muy leve","muy intenso","muy intensa"
]

BODY_PARTS = [
    "rodilla","tobillo","cadera","hombro","codo","muñeca","mano",
    "columna cervical","columna dorsal","columna lumbar","columna",
    "sacro","sacroilíaca","columna sacra","pelvis","escápula","omóplato",
    "cervical","lumbar","dorsal","región lumbar","región cervical",
    "ligamento cruzado anterior","lca","ligamento cruzado posterior","lcp",
    "menisco interno","menisco externo",
    "tendón de aquiles","rotuliano","tendón rotuliano",
    "manguito rotador","supraespinoso","infraespinoso","subescapular",
    "bíceps","tríceps","isquiotibiales","cuádriceps","glúteos","gemelos",
    "banda iliotibial","fascia plantar"
]

MOVEMENTS = [
    "flexión","extensión","abducción","aducción","rotación interna","rotación externa",
    "pronosupinación","dorsiflexión","plantiflexión","inclinación lateral"
]

FUNCTIONAL_LIMITATIONS = [
    "dificultad para caminar","dificultad para subir escaleras","dificultad para correr",
    "dificultad para levantar peso","incapacidad para cargar","limitación para agacharse",
    "dolor al dormir","dolor nocturno","dolor al estar sentado","dolor al estar de pie"
]

DIAGNOSES = [
    "lumbalgia","cervicalgia","gonalgia","coxalgia","lumbociatalgia",
    "radiculopatía","herniación discal","hernia discal",
    "síndrome femoropatelar","condromalacia rotuliana",
    "tendinitis rotuliana","tendinopatía rotuliana",
    "tendinopatía del manguito rotador","impingement subacromial","síndrome subacromial",
    "epicondilitis lateral","epitrocleitis","fascitis plantar",
    "esguince de tobillo","esguince","ruptura del lca","lesión del lca"
]

TREATMENTS = [
    "tens","electroterapia","ultrasonido","crioterapia","termoterapia",
    "masoterapia","terapia manual","movilización articular","manipulación",
    "punción seca","kinesiotaping","taping","vendaje neuromuscular"
]

EXERCISES = [
    "isométricos de cuádriceps","isométricos","propiocepción",
    "puente glúteo","clamshell","plancha","sentadilla",
    "ejercicios excéntricos","excéntricos de isquiotibiales","estiramientos"
]

FREQUENCY = ["intermitente","constante","nocturno","nocturna","diurno","diurna"]

LATERALITY = ["derecha","izquierda","bilateral","ambas","derecho","izquierdo"]

TESTS = [
    "lachman","pivot shift","apley","mcmurray","drawer anterior","drawer posterior",
    "valgo","varo","ober","thompson","speed","yergason","jerk"
]

# ===================== Helpers: pasar a patrones por tokens =====================

def phrase_to_token_pattern(phrase: str) -> List[Dict]:
    # División simple por espacios: para nuestro dominio es suficiente.
    # Cada token se compara por LOWER → no depende de mayúsculas/acentos.
    return [{"LOWER": tok} for tok in phrase.split()]

def simple_patterns(label: str, items: Iterable[str]) -> List[Dict]:
    # Devuelve SIEMPRE patrones por tokens (Matcher) → evita W012
    return [{"label": label, "pattern": phrase_to_token_pattern(it)} for it in items]

def make_scale_patterns() -> List[Dict]:
    base: List[Dict] = []
    scales = ["eva", "vas", "nrs"]

    # Casos comunes de tokenización española: "7/10" viene como UN token
    for s in scales:
        base += [
            # "EVA 7/10"
            {"label":"SCALE","pattern":[{"LOWER": s}, {"TEXT": {"REGEX": r"^\d{1,2}/(10|100)$"}}]},
            # "EVA : 7/10"
            {"label":"SCALE","pattern":[{"LOWER": s}, {"TEXT": ":"}, {"TEXT": {"REGEX": r"^\d{1,2}/(10|100)$"}}]},
            # "7/10 en EVA"
            {"label":"SCALE","pattern":[{"TEXT": {"REGEX": r"^\d{1,2}/(10|100)$"}}, {"LOWER":"en"}, {"LOWER": s}]},
            # Por si viniera como 3 tokens: "7", "/", "10"
            {"label":"SCALE","pattern":[{"LOWER": s}, {"TEXT": {"REGEX": r"^\d{1,2}$"}}, {"TEXT": "/"}, {"TEXT": {"REGEX": r"^(10|100)$"}}]},
            {"label":"SCALE","pattern":[{"TEXT": {"REGEX": r"^\d{1,2}$"}}, {"TEXT": "/"}, {"TEXT": {"REGEX": r"^(10|100)$"}}, {"LOWER":"en"}, {"LOWER": s}]},
        ]
    return base

def make_measure_patterns() -> List[Dict]:
    return [
        {"label":"MEASURE","pattern":[{"TEXT":{"REGEX":"^\\d{1,3}$"}},{"TEXT":{"REGEX":"^°$|^grados?$"}}]},
        {"label":"MEASURE","pattern":[{"TEXT":{"REGEX":"^\\d{1,3}$"}},{"TEXT":{"REGEX":"^%$"}}]},
        {"label":"MEASURE","pattern":[{"TEXT":{"REGEX":"^[0-5]$"}},{"TEXT":"/"},{"TEXT":{"REGEX":"^[0-5]$"}}]},
        {"label":"MEASURE","pattern":[{"TEXT":{"REGEX":"^[0-5]$"}},{"LOWER":"de"},{"TEXT":{"REGEX":"^[0-5]$"}}]},
    ]

def make_duration_patterns() -> List[Dict]:
    unidades = ["día","días","semana","semanas","mes","meses","año","años"]
    return [
        {"label":"DURATION","pattern":[{"LOWER":"hace"},{"TEXT":{"REGEX":"^\\d{1,3}$"}},{"LOWER":{"IN":unidades}}]},
        {"label":"DURATION","pattern":[{"LOWER":"desde"},{"LOWER":"hace"},{"TEXT":{"REGEX":"^\\d{1,3}$"}},{"LOWER":{"IN":unidades}}]},
        {"label":"DURATION","pattern":[{"TEXT":{"REGEX":"^\\d{1,3}$"}},{"LOWER":{"IN":unidades}},{"LOWER":"de"},{"LOWER":"evolución"}]},
    ]

def make_rom_patterns() -> List[Dict]:
    # Para movimientos largos (“rotación interna”), usamos el primer token del listado para el inicio
    base_inits = [m.split()[0] for m in MOVEMENTS]
    return [
        # "flexión de rodilla 120°"
        {"label":"ROM","pattern":[{"LOWER":{"IN":base_inits}},{"LOWER":"de"},{"LOWER":{"IN":["hombro","cadera","rodilla","codo","columna","tobillo"]}},{"TEXT":{"REGEX":"^\\d{1,3}$"}},{"TEXT":{"REGEX":"^°$|^grados?$"}}]},
        # "flexión 120°"
        {"label":"ROM","pattern":[{"LOWER":{"IN":base_inits}},{"TEXT":{"REGEX":"^\\d{1,3}$"}},{"TEXT":{"REGEX":"^°$|^grados?$"}}]},
    ]

def make_laterality_patterns() -> List[Dict]:
    return [{"label":"LATERALITY","pattern": phrase_to_token_pattern(w)} for w in LATERALITY]

# ===================== Construcción del pipeline =====================

def build_pt_pipeline() -> Language:
    # Desactivamos el NER estadístico para evitar MISC/PER/ORG, etc.
    nlp = spacy.load("es_core_news_md", disable=["ner"])

    # Extensión opcional normalizada
    if not Span.has_extension("norm_label"):
        Span.set_extension("norm_label", default=None)

    # EntityRuler: al usar patrones por tokens, emplea Matcher (sin W012)
    ruler = nlp.add_pipe(
        "entity_ruler",
        config={
            "overwrite_ents": False,  # puedes poner True si quieres que reglas reemplacen overlaps
            "validate": True
        }
    )

    patterns: List[Dict] = []
    patterns += simple_patterns("SYMPTOM", SYMPTOMS)
    patterns += simple_patterns("PAIN_QUALITY", PAIN_QUALITY)
    patterns += simple_patterns("PAIN_INTENSITY", PAIN_INTENSITY)
    patterns += simple_patterns("BODY_PART", BODY_PARTS)
    patterns += simple_patterns("MOVEMENT", MOVEMENTS)
    patterns += simple_patterns("FUNCTIONAL_LIMITATION", FUNCTIONAL_LIMITATIONS)
    patterns += simple_patterns("DIAGNOSIS", DIAGNOSES)
    patterns += simple_patterns("TREATMENT", TREATMENTS)
    patterns += simple_patterns("EXERCISE", EXERCISES)
    patterns += simple_patterns("FREQUENCY", FREQUENCY)
    patterns += make_laterality_patterns()
    patterns += make_scale_patterns()
    patterns += make_measure_patterns()
    patterns += make_duration_patterns()
    patterns += make_rom_patterns()

    ruler.add_patterns(patterns)

    # Normalizaciones simples
    norm_map = {
        "lca": "ligamento cruzado anterior",
        "lcp": "ligamento cruzado posterior",
        "derecho": "derecha",
        "izquierdo": "izquierda",
    }

    @Language.component("pt_span_normalizer")
    def pt_span_normalizer(doc):
        for ent in list(doc.ents):
            text_norm = ent.text.lower()
            if ent.label_ in {"BODY_PART", "LATERALITY"} and text_norm in norm_map:
                ent._.norm_label = norm_map[text_norm]
        return doc

    nlp.add_pipe("pt_span_normalizer", last=True)
    return nlp

# if __name__ == "__main__":
#     nlp = build_pt_pipeline()
#     txt = (
#         "Paciente con dolor punzante en rodilla derecha desde hace 3 semanas, "
#         "limitación para subir escaleras. EVA 7/10. Pruebas: Lachman positivo. "
#         "Diagnóstico probable: síndrome femoropatelar. Tratamiento con TENS y ejercicios isométricos de cuádriceps. "
#         "ROM: flexión de rodilla 120 grados"
#     )
#     doc = nlp(txt)
#     print([(e.text, e.label_, e._.norm_label) for e in doc.ents])
