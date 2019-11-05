import os
from bottle import route, run, request, static_file
import json
import spacy
#from spacy_conll import Spacy2ConllParser
from ud2ude_aryehgigi.converter import convert
import ud2ude_aryehgigi.conllu_wrapper as cw

#ARBITRARY_PATH = "sentence.txt"


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
    
    # spacyconll.parseprint(input_str=sentence, output_file=ARBITRARY_PATH, is_tokenized=True)
    # with open(ARBITRARY_PATH, "r") as f:
    #     conllu_basic_out = f.read()
    # os.remove(ARBITRARY_PATH)
    
    conllu_basic_out_formatted = cw.parse_spacy_doc(nlp(sentence))
    odin_basic_out = cw.conllu_to_odin([conllu_basic_out_formatted], is_basic=True, push_new_to_end=False)
    
    conllu_plus_out_formatted, conv_done = convert([conllu_basic_out_formatted], eud, eud_pp, eud_aryeh, int(conv_iterations), remove_eud_info, remove_extra_info)
    odin_plus_out = cw.conllu_to_odin(conllu_plus_out_formatted, push_new_to_end=False)

    return json.dumps({
        "basic": odin_basic_out,
        "plus": odin_plus_out,
        "conv_done": conv_done,
    })


# TODO:
#   1. add to a main function
#   2. copy the model to the project and remove the absolute local path
nlp = spacy.load("en_ud_model")
#spacyconll = Spacy2ConllParser(nlp=nlp)
run(host='localhost', reloader=True, port=5070)
