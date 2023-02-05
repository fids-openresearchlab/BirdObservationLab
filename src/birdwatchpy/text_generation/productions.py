import json
from copy import deepcopy
from dataclasses import field, dataclass
from collections import namedtuple
import csv
from pathlib import Path
from typing import List, Union, Tuple

from nltk import CFG, PCFG
from nltk.parse.generate import generate, demo
from nltk.tree import Tree

from birdwatchpy.utils import get_project_root


@dataclass
class TerminalProduction:
    """Class that keeps a TerminalProduction."""
    left: str = ""
    right: list = field(default_factory=list)
    category: str = ""
    singular_Plural: str = ""
    N_M_F: str = ""
    weight: float = 1
    processor: str = ""
    processor_args: dict = field(default_factory=dict)

@dataclass
class SentenceProduction:
    left: str = ""
    right: list = field(default_factory=list)
    weight: float = 1
    processor: str = ""
    processor_args: dict = field(default_factory=dict)

def load_sentence_prods_from_csv(sentence_prod_path: Path) -> List[SentenceProduction]:
    with open(sentence_prod_path.as_posix(), mode='r') as file:
        csvFile = csv.reader(file, delimiter=';')
        header = str(next(csvFile))

        sentence_productions_list = []
        for line in csvFile:
            if len(line) == 0:
                continue

            if len(line) >= 5 and line[4] != '':
                processor_arg_list = [arg.split(':') for arg in line[4].split(',')]
                processor_arg_dict = {arg_name.replace(' ', ''): arg_value.replace(' ', '') for arg_name, arg_value in
                                      processor_arg_list}
            else:
                processor_arg_dict = {}

            sentence_productions_list.append(SentenceProduction(
                left=line[0].strip(" ") if len(line) >= 1 else "",
                right=line[1].split(',') if len(line) >= 2 else "",
                weight=float(line[2]) if len(line) >= 3 and line[2] != "" else 1,
                processor=line[3] if len(line) >= 4 else "",
                processor_args=processor_arg_dict,
            ))

    return sentence_productions_list

def load_terminal_prods_from_csv(terminal_prod_path: Path) -> List[TerminalProduction]:
    with open(terminal_prod_path.as_posix(), mode='r') as file:
        csvFile = csv.reader(file, delimiter=';')
        header = str(next(csvFile))

        terminal_productions_list = []
        for line in csvFile:
            if len(line) >= 8 and line[7] != '':
                processor_arg_list = [arg.split(':') for arg in line[7].split(',')]
                processor_arg_dict = {arg_name.replace(' ', ''): arg_value.replace(' ', '') for arg_name, arg_value in
                                      processor_arg_list}
            else:
                processor_arg_dict = {}

            terminal_productions_list.append(
                TerminalProduction(
                    left=line[0].strip(" ") if len(line) >= 1 else "",
                    right=line[1].split(',') if len(line) >= 2 else "",
                    category=line[2] if len(line) >= 3 else "",
                    singular_Plural=line[3] if len(line) >= 4 else "",
                    N_M_F=line[4] if len(line) > 5 else "",
                    weight=float(line[5]) if len(line) >= 6 and line[5] != "" else 1,
                    processor=line[6] if len(line) >= 7 else "",
                    processor_args=processor_arg_dict,
                )
            )
    return terminal_productions_list

def load_productions() -> Tuple[List[SentenceProduction], List[TerminalProduction]]:
    sentence_prods = load_sentence_prods_from_csv(
        get_project_root() / 'birdwatchpy' / 'text_generation' / 'sentence_prod.csv')
    terminal_prods = load_terminal_prods_from_csv(
        get_project_root() / 'birdwatchpy' / 'text_generation' / 'terminal_prod.csv')

    return sentence_prods, terminal_prods

def as_one_to_one_productions_list(productions: Union[TerminalProduction, SentenceProduction]):
    o_to_o_prods = []
    for prod in deepcopy(productions):
        assert (isinstance( prod.right, list))
        for right in prod.right:
            new_prod = prod
            new_prod.right = right.strip(" ")
            o_to_o_prods.append(new_prod)
    return o_to_o_prods


def create_productions_dict(productions: List[Union[SentenceProduction, TerminalProduction]]) -> dict:
    d = {}
    for prod in productions:
        if prod is None:
            continue
        # Add name to dict if not exists
        if prod.left not in d:
            d[prod.left] = []
        d[prod.left].append(prod)
    return d
