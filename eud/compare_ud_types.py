import os
import sys, traceback
from bottle import route, run, request, static_file
import json
import spacy
from spacy.tokens import Doc
from ud2ude.api import Converter
from ud2ude.converter import ConvsCanceler
import ud2ude.conllu_wrapper as cw
import ud2ude.spacy_wrapper as sw
import ssl
import smtplib
import math


@route('/eud/')
@route('/eud/<filepath:path>')
def server_static(filepath="index.html"):
    lastpart = filepath[filepath.rfind('/') + 1:]
    if (" " in lastpart) or ("." not in lastpart):
        filepath = filepath.replace(lastpart, "index.html")
    return static_file(filepath, root='./')


@route('/eud/feedback/', method='POST')
def feedback():
    text_to_send = request.json["text_to_send"]
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    sender_email = "aryehgigi@gmail.com"
    receiver_email = "aryehgigi@gmail.com"
    message = 'Subject: {}\n\n{}'.format("BART feedback", text_to_send)
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message)
    except smtplib.SMTPException:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
        with open("feedback.log", "a") as f:
            f.write(text_to_send + "\n")


@route('/eud/annotate/', method='POST')
def annotate():
    if request.json is None or "sentence" not in request.json:
        return {"error": "No sentence provided"}
    
    sentence = request.json["sentence"]
    eud = request.json["eud"]
    eud_pp = request.json["eud_pp"]
    eud_bart = request.json["eud_bart"]
    conv_iterations = request.json["conv_iterations"]
    remove_eud_info = request.json["remove_eud_info"]
    include_bart_info = request.json["include_bart_info"]
    remove_node_adding_convs = request.json["remove_node_adding_convs"]
    
    basic_doc = Doc(nlp.vocab, words=[t.text for t in nlp(sentence) if not t.is_space])
    extra_doc = Doc(nlp.vocab, words=[t.text for t in nlp(sentence) if not t.is_space])
    basic_con = Converter(False, False, False, 0, False, False, False, False, False, ConvsCanceler())
    extra_con = Converter(eud, eud_pp, eud_bart, int(conv_iterations) if conv_iterations != "inf" else math.inf, remove_eud_info,
                          not include_bart_info, remove_node_adding_convs, False, False, ConvsCanceler())
    
    for doc, con in [(basic_doc, basic_con), (extra_doc, extra_con)]:
        _ = tagger(doc)
        _ = parser(doc)
        _ = con(doc)
    
    odin_basic_out = cw.conllu_to_odin(basic_con.get_parsed_doc(), is_basic=True, push_new_to_end=False)
    odin_plus_out = cw.conllu_to_odin(extra_con.get_parsed_doc(), push_new_to_end=False)
    
    return json.dumps({
        "basic": odin_basic_out,
        "plus": odin_plus_out,
        "conv_done": extra_con.get_max_convs(),
    })


password = input("pass for sending emails: ")
nlp = spacy.load("en_ud_model")
tagger = nlp.get_pipe('tagger')
parser = nlp.get_pipe('parser')
run(host='0.0.0.0', reloader=True, port=5000)
