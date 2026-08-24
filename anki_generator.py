import os
import html
import random
import tempfile

import genanki

CENTERED = '<div style="text-align:center">'

REVERSED_MODEL = genanki.Model(
    1731695950190,
    'Básico e Invertido',
    fields=[{'name': 'Frente'}, {'name': 'Verso'}],
    templates=[
        {'name': 'Cartão 1', 'qfmt': CENTERED + '{{Frente}}</div>', 'afmt': CENTERED + '{{FrontSide}}<hr id="answer">{{Verso}}</div>'},
        {'name': 'Cartão 2', 'qfmt': CENTERED + '{{Verso}}</div>', 'afmt': CENTERED + '{{FrontSide}}<hr id="answer">{{Frente}}</div>'},
    ]
)


def generate_apkg_from_pairs(deck_name, pairs):
    """Gera um .apkg em memória a partir de uma lista de tuplas (frente, verso) e retorna os bytes."""
    deck = genanki.Deck(random.randrange(1 << 30, 1 << 31), deck_name)
    for front, back in pairs:
        deck.add_note(genanki.Note(model=REVERSED_MODEL, fields=[html.escape(front), html.escape(back)]))
    with tempfile.NamedTemporaryFile(suffix='.apkg', delete=False) as tmp:
        tmp_path = tmp.name
    import random as _random
    notes = deck.notes
    _random.shuffle(notes)
    deck.notes = notes
    genanki.Package(deck).write_to_file(tmp_path)
    with open(tmp_path, 'rb') as f:
        data = f.read()
    os.remove(tmp_path)
    return data
