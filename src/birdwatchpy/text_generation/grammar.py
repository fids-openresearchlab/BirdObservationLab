from typing import List, Union

from nltk import CFG
from nltk.parse.generate import generate
from pcfg import PCFG

from birdwatchpy.text_generation.productions import TerminalProduction, SentenceProduction


def cfg_str_from_productions(productions: List[Union[TerminalProduction, SentenceProduction]]):
    grammar_str = ""
    grammar_str_extension = """
        QQ -> '?'
        CC -> ','
        PP -> '.'
                """
    for prod in productions:
        if isinstance(prod, TerminalProduction):
            grammar_str += f"\n{prod.left} -> '" + "' | '".join(prod.right) + "'"
        elif isinstance(prod, SentenceProduction):
            grammar_str += f"\n{prod.left} -> " + " | ".join(prod.right)
    grammar_str += grammar_str_extension

    return grammar_str


def create_normalized_PCFG_str(productions_dict: dict):
    prob_grammar_str = ""

    for left, productions in productions_dict.items():
        weighted_sum = sum([prod.weight for prod in productions])
        for prod in productions:
            if isinstance(prod, TerminalProduction):
                prob_grammar_str += f"""{left} -> '{prod.right if isinstance(prod.right, SentenceProduction) else f'{prod.right}'}' [{prod.weight / weighted_sum if prod.weight != 0 else 0:.20f}]\n"""
            elif isinstance(prod, SentenceProduction):
                prob_grammar_str += f"""{left} -> {prod.right if isinstance(prod.right, SentenceProduction) else f'{prod.right}'} [{prod.weight / weighted_sum if prod.weight != 0 else 0:.20f}]\n"""

    return prob_grammar_str


def cfg_from_str(cfg_str: str):
    return CFG.fromstring(cfg_str)


def pcfg_from_str(pcfg_str: str):
    return PCFG.fromstring(pcfg_str)


def generate_pcfg_sentences(pcfg_grammar, count: int):
    return [sentence for sentence in pcfg_grammar.generate(count)]


def write_all_sentence_possibilities(grammar, output_path: str = "all_possible_sentences.txt"):
    f = open(output_path, "w")
    for n, sent in enumerate(generate(grammar, n=10000000), 1):
        print("%3d. %s" % (n, " ".join(sent)))
        f.write("%3d. %s" % (n, " ".join(sent)) + "\n")
    f.close()


def sentence_beautification(txt: str) -> str:
    txt = txt.replace('.', '.;')
    txt = txt.replace('?', '?;')
    txt = txt.replace('!', '!;')
    splited_sentences = txt.split(';')
    splited_sentences = [sentence.strip(' ') for sentence in splited_sentences]
    print(txt)
    print(splited_sentences)
    return ' '.join([sentence[0].upper() + sentence[1:] for sentence in splited_sentences if sentence != ''])
