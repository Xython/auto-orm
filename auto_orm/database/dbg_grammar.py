from auto_orm.database import dbg_ast
from rbnf.easy import Language, build_parser, build_language
source_code = """
import std.common.[Name Comment DoubleQuotedStr]
ignore [Comment Space]
Space := R'\s+'
kw cast := 'repr' 'with' 'import' 'db' 'python' 'session' 'engine' 'dbg_is_status_activated' 'deactivate' 'enum'
kv    ::= key=id '=' value=DoubleQuotedStr -> (key, value.value)
engine ::= 'engine'
           '{'
              kvs=(kv (',' kv)*)
           '}' -> Engine(dict(kvs))
id     ::= name=Name -> name.value
python ::= mark='python' codes=(_{is_indented})+ -> Python(recover_codes([mark, *codes])[len('python'):])
field  ::= id=id ':' type=expr ops=option* ['=' value=expr] -> Field(id, type, ops, value)
fields ::= fields<<field (',' fields<<field)* [','] -> fields
repr   ::= '{' names=(id (',' id)*) '}' -> names[::2]
table  ::= id=id
           '{' 
                [fields=fields]
                ['repr' repr=repr] 
           '}' -> Table(id, fields or [], repr)
option ::= ch=('~' | '!' | '?') -> ch.value
relation ::= left=id w1=['^'] 'with' w2=['^'] right=id
             '{' 
                field_lst=(field (',' field)*)
             '}' -> Relation(left, right, (bool(w1), bool(w2)), field_lst[::2])
expr   ::=  | [is_enum='enum'] tks=(~('=' | '{' | '}' | '!' | '?' | '~' | ',' | 'repr' | 'with'))+ 
           -> (EnumValue if is_enum else Value)(recover_codes(tks))  
lexer_helper := R'.'
stmts  ::= stmts=(engine | relation | table | python)+ -> list(stmts)

"""
dbg = Language('dbg')
dbg.namespace.update(dbg_ast.__dict__)
build_language(source_code, dbg, 'dbg-lang.rbnf')
parse = build_parser(dbg)

