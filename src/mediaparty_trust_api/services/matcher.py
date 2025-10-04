import json
import logging

from tqdm import tqdm

# from .import_utils import import_config_yaml

# def configure_logger():
#     logger.setLevel(logging.DEBUG)
#     handler = logging.StreamHandler()
#     formatter = logging.Formatter(
#         "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
#     )
#     handler.setFormatter(formatter)
#     logger.addHandler(handler)


# # Configure the logger
# logger = logging.getLogger(__name__)

# if logger.hasHandlers():
#     logger.handlers.clear()

# configure_logger()


def import_config_yaml():
    config = {
        "explicit_sources_patterns": [
            {
                "name": "QV",
                "pattern": [{"text": '"'}, "*", {"text": '"'}, {"upos": "VERB"}],
            },
            {
                "name": "QVP",
                "pattern": [
                    {"text": '"'},
                    "*",
                    {"text": '"'},
                    {"upos": "VERB"},
                    {"norm_ner": "PER"},
                ],
            },
            {
                "name": "QVPP",
                "pattern": [
                    {"text": '"'},
                    "*",
                    {"text": '"'},
                    {"upos": "VERB"},
                    {"norm_ner": "PER"},
                    {"norm_ner": "PER"},
                ],
            },
            {
                "name": "Q.V",
                "pattern": [
                    {"text": '"'},
                    "*",
                    {"text": '"'},
                    {"text": [",", ":"]},
                    {"upos": "VERB"},
                ],
            },
            {
                "name": "Q.VP",
                "pattern": [
                    {"text": '"'},
                    "*",
                    {"text": '"'},
                    {"text": [",", ":"]},
                    {"upos": "VERB"},
                    {"norm_ner": "PER"},
                ],
            },
            {
                "name": "Q.VPP",
                "pattern": [
                    {"text": '"'},
                    "*",
                    {"text": '"'},
                    {"text": [",", ":"]},
                    {"upos": "VERB"},
                    {"norm_ner": "PER"},
                    {"norm_ner": "PER"},
                ],
            },
            {
                "name": "PVQ",
                "pattern": [
                    {"norm_ner": "PER"},
                    {"upos": "VERB"},
                    {"text": '"'},
                    "*",
                    {"text": '"'},
                ],
            },
            {
                "name": "VQ",
                "pattern": [{"upos": "VERB"}, {"text": '"'}, "*", {"text": '"'}],
            },
            {
                "name": "PPVQ",
                "pattern": [
                    {"norm_ner": "PER"},
                    {"norm_ner": "PER"},
                    {"upos": "VERB"},
                    {"text": '"'},
                    "*",
                    {"text": '"'},
                ],
            },
            {
                "name": "V.Q",
                "pattern": [
                    {"upos": "VERB"},
                    {"text": [",", ":"]},
                    {"text": '"'},
                    "*",
                    {"text": '"'},
                ],
            },
            {
                "name": "PV.Q",
                "pattern": [
                    {"norm_ner": "PER"},
                    {"upos": "VERB"},
                    {"text": [",", ":"]},
                    {"text": '"'},
                    "*",
                    {"text": '"'},
                ],
            },
            {
                "name": "PPV.Q",
                "pattern": [
                    {"norm_ner": "PER"},
                    {"norm_ner": "PER"},
                    {"upos": "VERB"},
                    {"text": [",", ":"]},
                    {"text": '"'},
                    "*",
                    {"text": '"'},
                ],
            },
        ]
    }
    return config


# General functions.
def get_patterns_from_json(patterns_file):
    with open(patterns_file, "r") as f:
        patterns = json.load(f)

    patterns = preprocess_patterns(patterns)

    return patterns


def preprocess_patterns(patterns):
    return {d["name"]: d["pattern"] for d in patterns}


def check_pattern_match(token, pattern):
    if pattern == "*":
        return True
    else:
        attribute_to_check = list(pattern.keys())[0]
        pattern_value = (
            pattern[attribute_to_check]
            if type(pattern[attribute_to_check]) == list
            else [pattern[attribute_to_check]]
        )
        return token[attribute_to_check] in pattern_value


def normalize_ner(ner):
    if ner == "O" or ner is None:
        return "O"
    else:
        return ner.split("-")[1]


class Matcher:
    def __init__(self, patterns, debug=False):
        self.patterns = patterns
        self.debug = debug

    def flatten_stanza_tokens(self, stanza_doc):
        doc_tokens = []
        i = 0

        for sentence in stanza_doc.sentences:
            for token in sentence.tokens:
                t_abs_id = i
                t_id = token.id
                t_len = len(t_id)
                t_sent_id = int(sentence.sent_id)
                t_text = token.text
                t_start = token.start_char
                t_end = token.end_char
                t_ner = token.ner
                t_norm_ner = normalize_ner(token.ner)
                t_checked = False

                if t_len == 1:
                    t_lemma = token.words[0].lemma
                    t_upos = token.words[0].upos
                    t_xpos = token.words[0].xpos
                    t_feats = token.words[0].feats
                    t_head = token.words[0].head
                    t_deprel = token.words[0].deprel

                else:
                    t_lemma = ""  # (token.words[0].lemma, token.words[1].lemma)
                    t_upos = ""  # (token.words[0].upos, token.words[1].upos)
                    t_xpos = ""  # (token.words[0].xpos, token.words[1].xpos)
                    t_feats = ""  # (token.words[0].feats, token.words[1].feats)
                    t_head = ""  # (token.words[0].head, token.words[1].head)
                    t_deprel = ""  # (token.words[0].deprel, token.words[1].deprel)

                new_token = dict(
                    id_length=t_len,
                    token_id=t_id,
                    sent_id=t_sent_id,
                    abs_id=t_abs_id,
                    text=t_text,
                    start_char=t_start,
                    end_char=t_end,
                    ner=t_ner,
                    norm_ner=t_norm_ner,
                    lemma=t_lemma,
                    upos=t_upos,
                    xpos=t_xpos,
                    feats=t_feats,
                    head=t_head,
                    deprel=t_deprel,
                    token_checked=t_checked,
                )
                doc_tokens.append(new_token)
                i += 1

        return doc_tokens

    def get_matches(self, doc_tokens):
        matches = []

        for token in doc_tokens:
            # logger.debug(f"Token analizado {token['abs_id']} - {token['text']}")

            for pattern_name, pattern in self.patterns.items():
                # logger.debug(f"Pattern analizado {pattern}")
                # Cuando se cumple el primer patrón, se agrega el token a la lista de fuentes

                if check_pattern_match(token, pattern[0]):
                    detection = [token]
                    detection_check = [True]
                    start_index = token["abs_id"]

                    # logger.debug(
                    #     f"Deteccion token entrada {token['abs_id']} - {token['text']}"
                    # )

                    i = 1

                    for j, p in enumerate(pattern[1:], 1):
                        # Si todavía no se llegó al final del documento:
                        if (start_index + i) < len(doc_tokens):
                            # logger.debug(
                            #     f"token número -> {start_index + i} de {len(doc_tokens)}"
                            # )
                            # logger.debug(
                            #     f"Se evalua el token  {doc_tokens[start_index + i]['abs_id']} - {doc_tokens[start_index + i]['text']} con la regla {p}"
                            # )

                            # En este lugar tendría que tener el próximo patrón
                            # Agregar todas las palabras hasta que se cumpla el próximo patrón
                            # Ir avanzando en el índice de tokens
                            if p == "*":
                                # logger.debug("Entra en *")

                                while not check_pattern_match(
                                    doc_tokens[start_index + i], pattern[j + 1]
                                ):
                                    # logger.debug(
                                    #     f"Evalua el próximo token {doc_tokens[start_index + i]['abs_id']} -  {doc_tokens[start_index + i]['text']} pattern {pattern[j + 1]}"
                                    # )
                                    detection.append(doc_tokens[start_index + i])
                                    detection_check.append(True)
                                    i += 1

                                    if (start_index + i) == len(doc_tokens):
                                        break

                                i -= 1
                                # logger.debug(
                                #     f"FIN Next token {doc_tokens[start_index + i]['abs_id']} -  {doc_tokens[start_index + i]['text']} pattern {pattern[j + 1]}"
                                # )
                            #     while

                            # elif list(p.keys())[0] == "norm_ner":
                            #     print("Entra en NER")
                            #     print(f"Evalua el próximo token {doc_tokens[start_index + i]['abs_id']} - {doc_tokens[start_index + i]['text']} pattern {p}")
                            #     while check_pattern_match(doc_tokens[start_index + i], p):
                            #         print(f"Dentro NER se evalua el próximo token {doc_tokens[start_index + i]['abs_id']} - {doc_tokens[start_index + i]['text']} pattern {p}")
                            #         detection.append(doc_tokens[start_index + i])
                            #         detection_check.append(True)
                            #         i += 1
                            #         if i == len(doc_tokens):
                            #             break

                            #     i -= 1
                            #     print(f"FIN NER Next token {doc_tokens[start_index + i]['abs_id']} - {doc_tokens[start_index + i]['text']} pattern {p}")

                            elif check_pattern_match(doc_tokens[start_index + i], p):
                                # #logger.debug(
                                #     f"Evalua el próximo token {doc_tokens[start_index + i]['abs_id']} -  {doc_tokens[start_index + i]['text']} pattern {p}"
                                # )
                                detection.append(doc_tokens[start_index + i])
                                detection_check.append(True)

                            else:
                                # logger.debug("NO SE CUMPLE LA REGLA")
                                detection_check.append(False)
                                break

                            i += 1

                        else:
                            # logger.debug("NO HAY MAS TOKENS")
                            detection_check.append(False)
                            break

                    if all(detection_check):
                        # logger.debug("SE CUMPLE LA REGLA")
                        matches.append(
                            {
                                "pattern": pattern_name,
                                "start_char": detection[0]["start_char"],
                                "end_char": detection[-1]["end_char"],
                                "length": detection[-1]["end_char"]
                                - detection[0]["start_char"],
                                "detection": detection,
                            }
                        )

                else:
                    continue

        # logger.info([(d["pattern"], d["start_char"], d["end_char"]) for d in matches])

        return matches

    def postprocess_matches(self, matches):
        drops = []

        # print("Initial Matches")
        # print([(d["pattern"], d["start_char"], d["end_char"]) for d in matches])

        for i, match in enumerate(matches):
            start = match["start_char"]
            end = match["end_char"]
            length = match["length"]
            match_drops = []
            matches_left = [m for j, m in enumerate(matches) if j != i]

            for other_match in matches_left:
                if (
                    start >= other_match["start_char"]
                    and start <= other_match["end_char"]
                ):
                    if length <= other_match["length"]:
                        match_drops.append(1)
                elif (
                    end >= other_match["start_char"] and end <= other_match["end_char"]
                ):
                    if length <= other_match["length"]:
                        match_drops.append(1)
                else:
                    match_drops.append(0)

            drops.append(sum(match_drops))

        matches = [m for i, m in enumerate(matches) if drops[i] == 0]

        # print("Final Matches")
        # print([(d["pattern"], d["start_char"], d["end_char"]) for d in matches])

        return matches

    def run(self, stanza_doc):
        doc_tokens = self.flatten_stanza_tokens(stanza_doc)
        matches = self.get_matches(doc_tokens)
        matches = self.postprocess_matches(matches)

        return matches


class SourceMatcher(Matcher):
    def __init__(self, debug=False):
        self.patterns = preprocess_patterns(self._set_explicit_patterns())
        super().__init__(self.patterns, debug)

    def _set_explicit_patterns(self):
        patterns = import_config_yaml()["explicit_sources_patterns"]

        return patterns

    def get_explicit_sources(self, stanza_doc):
        matches = self.run(stanza_doc)

        sources_list = []

        for detection in matches:
            # Texto General.
            start_char = detection["start_char"]
            end_char = detection["end_char"]
            length = detection["length"]
            pattern = detection["pattern"]
            text = stanza_doc.text[start_char:end_char]

            source = {
                "text": text,
                "start_char": start_char,
                "end_char": end_char,
                "length": length,
                "pattern": pattern,
                "explicit": True,
                "components": {},
            }

            # Obtenemos la lista de tokens de la afirmación y del resto para la cita.
            abs_id_quote = [
                t["abs_id"]
                for t in detection["detection"]
                if t["text"] == "“" or t["text"] == "”" or t["text"] == '"'
            ]
            token_list_quote = [
                t
                for t in detection["detection"]
                if t["abs_id"] >= abs_id_quote[0] and t["abs_id"] <= abs_id_quote[1]
            ]
            token_list_else = [
                t
                for t in detection["detection"]
                if t["abs_id"] < abs_id_quote[0] or t["abs_id"] > abs_id_quote[1]
            ]

            # Afirmación.
            start_char = token_list_quote[0]["start_char"]
            end_char = token_list_quote[-1]["end_char"]
            text = stanza_doc.text[start_char:end_char]
            label = "Afirmacion"

            source["components"]["afirmacion"] = {
                "text": text,
                "start_char": start_char,
                "end_char": end_char,
                "label": label,
            }

            # Conector.
            # Asume 1 solo conector.
            # Asume que siempre tiene que haber conector
            token_conector = [t for t in token_list_else if t["upos"] == "VERB"][0]
            start_char = token_conector["start_char"]
            end_char = token_conector["end_char"]
            text = stanza_doc.text[start_char:end_char]
            label = "Conector"

            source["components"]["conector"] = {
                "text": text,
                "start_char": start_char,
                "end_char": end_char,
                "label": label,
            }

            # Conector.
            # Asume persona en orden consecutivo.
            # Puede no encontrar un referenciado.
            token_src = [t for t in token_list_else if t["norm_ner"] == "PER"]
            if len(token_src) > 0:
                start_char = token_src[0]["start_char"]
                end_char = token_src[-1]["end_char"]
                text = stanza_doc.text[start_char:end_char]
                label = "Referenciado"

                source["components"]["referenciado"] = {
                    "text": text,
                    "start_char": start_char,
                    "end_char": end_char,
                    "label": label,
                }

            sources_list.append(source)

        return sources_list
