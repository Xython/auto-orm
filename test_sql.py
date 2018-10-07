from auto_orm.database.dbg_grammar import *
from auto_orm.database.dbg_emit import *
from rbnf.edsl.rbnf_analyze import check_parsing_complete

test_code = r"""
engine {
     url = "sqlite:///:memory:"
}

Spirit { name: String(30) }
Site   {}

Spirit^ with ^Site {
    score: Float
}


"""
res = parse(test_code)

check_parsing_complete(test_code, res.tokens, res.state)
with open('generated.py', 'w') as f:
    f.write(code_gen(res.result))

