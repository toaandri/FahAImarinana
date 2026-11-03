"""French/Malagasy language policy and an editable seed newsroom glossary."""
import json
import re
from pathlib import Path
from typing import Literal

Language = Literal['auto', 'fr', 'mg']
GLOSSARY = json.loads((Path(__file__).with_name('journalism_glossary.json')).read_text())


def resolve_language(language: Language, question: str) -> str:
    if language != 'auto':
        return language
    text = question.casefold().replace('’', "'")
    if re.search(r'en (malagasy|malgache)|amin\S* (?:ny )?teny malagasy', text):
        return 'mg'
    if re.search(r'en fran[çc]ais', text):
        return 'fr'
    words = set(re.findall(r'[^\W\d_]+', text))
    mg = words & {'manao', 'ahoana', 'inona', 'iza', 'aiza', 'oviana', 'nahoana', 'azafady',
                  'misaotra', 'salama', 'vaovao', 'marina', 'tsaho', 'porofo', 'loharano',
                  'afaka', 'mba', 'izany', 'ity', 'izay', 'amin', 'momba', 've', 'ny', 'sy'}
    fr = words & {'bonjour', 'merci', 'comment', 'pourquoi', 'quelle', 'quelles', 'est', 'les',
                  'des', 'une', 'pour', 'avec', 'dans', 'information', 'vérifier', 'sources'}
    return 'mg' if len(mg) > len(fr) else 'fr'


def language_instruction(language: str) -> str:
    name = 'malagasy (teny malagasy)' if language == 'mg' else 'français'
    glossary = '; '.join(f"{item['fr']} = {item['mg']}" for item in GLOSSARY)
    return (f'Langue de réponse imposée : {name}. Réponds entièrement dans cette langue, '
            'avec des phrases claires et naturelles. Conserve les noms propres, chiffres, dates et liens. '
            'Ne traduis pas les citations verbatim sans les signaler comme traductions. '
            f'Glossaire journalistique indicatif (à adapter au contexte) : {glossary}. '
            + ("Mampiasà teny malagasy mazava sy voajanahary. Aza mamorona loharano na porofo. "
               "Ohatra: « Vérifiez les faits auprès de deux sources. » = "
               "« Hamarino amin’ny loharano roa ny zava-misy. » " if language == 'mg' else ''))


def expand_research_question(question: str) -> str:
    text = question.casefold()
    terms = [item['fr'] for item in GLOSSARY if item['mg'].casefold() in text]
    return question + ' ' + ' '.join(terms)
