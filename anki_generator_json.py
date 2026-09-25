import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import re
import genanki
import csv
import json
import random
import html

ANKI_BASIC_MODEL_ID = 1731695950189
MODEL = genanki.Model(
    ANKI_BASIC_MODEL_ID,
    'Básico',
    fields=[
        {'name': 'Frente'},
        {'name': 'Verso'}
    ],
    templates=[
        {
            'name': 'Cartão 1',
            'qfmt': '{{Frente}}',
            'afmt': '{{FrontSide}}<hr id="answer">{{Verso}}',
        },
    ]
)
BASE_DIR = os.path.join(os.path.dirname(__file__), '..')


def _cards_from_json(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        items = json.load(f)
    cards = []
    for item in items:
        parts = []
        if item.get('assunto'):
            # Aplica o html.escape antes de trocar \n por <br>
            parts.append(html.escape(item['assunto']))
        
        parts.append(html.escape(item['enunciado']))
        
        alternativas = item.get('alternativas', [])
        if alternativas:
            alt_text = '\n'.join(f"{chr(65+i)}) {alt}" for i, alt in enumerate(alternativas))
            parts.append(html.escape(alt_text))
            
        front = '<br>'.join(p.replace('\n', '<br>') for p in parts)
        back = html.escape(item['gabarito']).replace('\n', '<br>')
        cards.append((front, back))
    return cards


def generate_apkg(deck_name, input_path, output_path):
    deck_id = random.randrange(1 << 30, 1 << 31)
    deck = genanki.Deck(deck_id, deck_name)

    if input_path.endswith('.json'):
        cards = _cards_from_json(input_path)
    else:
        cards = []
        with open(input_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=',')
            for row in reader:
                if len(row) >= 2:
                    # Aplica o html.escape na frente e no verso do CSV
                    front = html.escape(row[0].strip()).replace('\n', '<br>')
                    back = html.escape(row[1].strip()).replace('\n', '<br>')
                    cards.append((front, back))

    for front, back in cards:
        deck.add_note(genanki.Note(model=MODEL, fields=[front, back]))

    genanki.Package(deck).write_to_file(output_path)
    return output_path

def deck_name_from_pdf(nome_pdf):
    nome = re.sub(r'^Caderno Erradas_\s*', '', nome_pdf)
    nome = re.sub(r'\b(Douglas|Luiz|Danilo)\b', '', nome, flags=re.IGNORECASE)
    return 'Erros::' + ' '.join(nome.split())


def generate_apkg_from_questoes(deck_name, questoes, output_path):
    deck_id = random.randrange(1 << 30, 1 << 31)
    deck = genanki.Deck(deck_id, deck_name)
    for item in questoes:
        parts = []
        parts.append(html.escape(item['enunciado']))
        alternativas = item.get('alternativas', [])
        if alternativas:
            alt_text = '\n'.join(f"{chr(65+i)}) {alt}" for i, alt in enumerate(alternativas))
            parts.append(html.escape(alt_text))
        front = '<br>'.join(p.replace('\n', '<br>') for p in parts)
        back = html.escape(item['gabarito']).replace('\n', '<br>')
        deck.add_note(genanki.Note(model=MODEL, fields=[front, back]))
    genanki.Package(deck).write_to_file(output_path)
    return output_path


if __name__ == "__main__":
    pass
