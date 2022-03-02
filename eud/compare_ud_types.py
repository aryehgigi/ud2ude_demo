import os
import sys, traceback
from bottle import route, run, request, static_file
import json
import spacy
from spacy.tokens import Doc
from pybart.api import Converter
import pybart.conllu_wrapper as cw
import ssl
import smtplib
import math
from pip._vendor import pkg_resources


nlp = None
pybart_version = None
password = None


@route('/eud/')
@route('/eud/<filepath:path>')
def server_static(filepath="index.html"):
    lastpart = filepath[filepath.rfind('/') + 1:]
    if (" " in lastpart) or ("." not in lastpart):
        filepath = filepath.replace(lastpart, "index.html")
    return static_file(filepath, root='./')


@route('/eud/feedback.log/', method='POST')
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


@route('/eud/version/', method='POST')
def version():
    return json.dumps({
        "version": pybart_version,
    })


udv_map = {"nsubjpass": "nsubj:pass", "csubjpass": "csubj:pass", "auxpass": "aux:pass", "dobj": "obj", "mwe": "fixed",
           "nmod:agent": "obl:agent", "nmod:tmod": "obl:tmod"}


def fix_doc(doc):
    for t in doc:
        if t.dep_ in udv_map:
            t.dep_ = udv_map[t.dep_]
        elif t.dep_ == "nmod" and t.head.pos_ in ["VERB", "AUX", "ADV", "ADJ"]:
            t.dep_ = "obl"


@route('/eud/annotate/', method='POST')
def annotate():
    if request.json is None or "sentence" not in request.json:
        return {"error": "No sentence provided"}

    sentence = request.json["sentence"]
    print(f"\n\tThe following sentence was posted: {sentence}\n")
    # client_ip = request.environ.get('HTTP_X_FORWARDED_FOR') or request.environ.get('REMOTE_ADDR')
    with open("logs.txt", "a+") as logger:
        logger.write(f"The following sentence was posted: {sentence}\n")
    eud = request.json["eud"]
    eud_pp = request.json["eud_pp"]
    eud_bart = request.json["eud_bart"]
    conv_iterations = request.json["conv_iterations"]
    remove_eud_info = request.json["remove_eud_info"]
    include_bart_info = request.json["include_bart_info"]
    remove_node_adding_convs = request.json["remove_node_adding_convs"]
    udv2 = request.json["udv"]

    basic_doc = Doc(nlp.vocab, words=[t.text for t in nlp(sentence) if not t.is_space])
    extra_doc = Doc(nlp.vocab, words=[t.text for t in nlp(sentence) if not t.is_space])
    basic_con = Converter(False, False, False, 0, False, False, False, False, False, ud_version=2 if udv2 else 1)
    extra_con = Converter(eud, eud_pp, eud_bart, int(conv_iterations) if conv_iterations != "inf" else math.inf, remove_eud_info,
                          not include_bart_info, remove_node_adding_convs, False, False, ud_version=2 if udv2 else 1)

    for doc, con in [(basic_doc, basic_con), (extra_doc, extra_con)]:
        for name, proc in nlp.pipeline:
            doc = proc(doc)
        if udv2:
            fix_doc(doc)
        doc = con(doc)

    odin_basic_out = cw.conllu_to_odin(basic_con.get_converted_sents(), is_basic=True, push_new_to_end=False)
    odin_plus_out = cw.conllu_to_odin(extra_con.get_converted_sents(), push_new_to_end=False)

    return json.dumps({
        "basic": odin_basic_out,
        "plus": odin_plus_out,
        "conv_done": extra_con.get_max_convs(),
    })


if __name__ == "__main__":
    nlp = spacy.load("en_ud_model_trf")
    pybart_version = [p.version for p in pkg_resources.working_set if p.project_name.lower() == "pybart-nlp"][0]
    # password = input("pass for sending emails: ")
    run(host='0.0.0.0', reloader=True, port=5000)
