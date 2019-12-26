import os
from bottle import route, run, request, static_file
import json
import spacy
from spacy.tokens import Doc
from ud2ude.converter import convert, ConvsCanceler
import ud2ude.conllu_wrapper as cw

@route('/eud/')
@route('/eud/<filepath:path>')
def server_static(filepath="index.html"):
    lastpart = filepath[filepath.rfind('/') + 1:]
    if (" " in lastpart) or ("." not in lastpart):
        filepath = filepath.replace(lastpart, "index.html")
    return static_file(filepath, root='./')

@route('/eud/annotate/', method='POST')
def annotate():
    if request.json is None or "sentence" not in request.json:
        return {"error": "No sentence provided"}
    
    sentence = request.json["sentence"]
    eud = request.json["eud"]
    eud_pp = request.json["eud_pp"]
    eud_aryeh = request.json["eud_aryeh"]
    conv_iterations = request.json["conv_iterations"]
    remove_eud_info = request.json["remove_eud_info"]
    remove_extra_info = request.json["remove_extra_info"]
    
    doc = Doc(nlp.vocab, words=[t.text for t in nlp(sentence) if not t.is_space])
    _ = tagger(doc)
    _ = parser(doc)
    conllu_basic_out_formatted = cw.parse_spacy_doc(doc)
    odin_basic_out = cw.conllu_to_odin([conllu_basic_out_formatted], is_basic=True, push_new_to_end=False)
    
    conllu_plus_out_formatted, conv_done = convert([conllu_basic_out_formatted], eud, eud_pp, eud_aryeh, int(conv_iterations), remove_eud_info,
                                                   remove_extra_info, False, ConvsCanceler())
    odin_plus_out = cw.conllu_to_odin(conllu_plus_out_formatted, push_new_to_end=False)
    
    return json.dumps({
        "basic": odin_basic_out,
        "plus": odin_plus_out,
        "conv_done": conv_done,
    })

nlp = spacy.load("en_ud_model")
run(host='localhost', reloader=True, port=5070)
tagger = nlp.get_pipe('tagger')
parser = nlp.get_pipe('parser')
