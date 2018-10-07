from auto_orm.database.dbg_grammar import *
from auto_orm.database.dbg_emit import *
from rbnf.edsl.rbnf_analyze import check_parsing_complete
from Redy.Tools.PathLib import Path
from wisepy.talking import Talking

dbg_lang = Talking()

python_ex = Talking()


@dbg_lang
def gen(i: 'input filename', o: 'output filename'):
    """
    generate python source code for dbg-lang
    """
    with Path(i).open('r') as fr:
        code = fr.read()
    res = parse(code)
    check_parsing_complete(code, res.tokens, res.state)

    with Path(o).open('w') as fw:
        fw.write(code_gen(res.result))


def dbg_lang_cli():
    dbg_lang.on()


def python_ex_cli():
    python_ex.on()
