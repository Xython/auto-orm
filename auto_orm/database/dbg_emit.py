from .dbg_ast import *
from Redy.Magic.Pattern import Pattern
from string import Template
from textwrap import dedent, indent
from yapf.yapflib.yapf_api import FormatCode
import typing as t

_Code = t.List[t.Union[str, '_Code', t.Callable[[], '_Code']]]
T = t.TypeVar('T')

type_map = {
    'Integer': 'int',
    'BigInteger': 'int',
    'SmallInteger': 'int',
    'Boolean': 'bool',
    'DateTime': 'db.datetime',
    'Date': 'db.date',
    'Float': 'float',
    'LargeBinary': 'bytes',
    'String': 'str',
    'Text': 'str',
    'Time': 'db.time',
    'Unicode': 'str',
    'Numeric': 'db.Decimal'
}


def dumps(codes: _Code, indent=''):
    if callable(codes):
        return dumps(codes(), indent)
    if isinstance(codes, str):
        return indent + codes
    if isinstance(codes, list):
        return f'\n'.join(map(lambda it: dumps(it, indent + '    '), codes))
    raise TypeError


class Proc:
    codes: _Code

    def __init__(self, codes: _Code):
        self.codes = codes

    def __add__(self, other: 'Proc'):
        return Proc([*self.codes, other])

    def __xor__(self, other):
        return Proc([*self.codes, *other])

    def __str__(self):
        return dumps(self.codes)


class RichList(t.List[T]):
    def any(self, predicate=None):
        if predicate is None:
            return any(self)
        return any(map(predicate, self))

    def find_all(self, predicate):
        return RichList(each for each in self if predicate(each))


class Context:
    current_table: str
    tables: RichList[Table]
    relations: RichList[Relation]

    def __init__(self, current_table: str, tables, relations):
        self.current_table = current_table
        self.tables = tables
        self.relations = relations

    def update(self, current_table=None, tables=None, relations=None):
        return Context(current_table or self.current_table, tables
                       or self.tables, relations or self.relations)


def maybe_comp(xs, fs):
    return [f(x) for f, x in zip(fs, xs) if x is not None]


@Pattern
def emit(node, proc: Proc, ctx: Context):
    return type(node)


def _as_hinted(ty_str: str):

    # for string only:
    if ty_str.startswith('String('):
        return ': str'

    hint = type_map.get(ty_str.strip()) or ty_str

    return f': {hint!r}'


def _make_parameters(fields: t.List[Field]):

    for each in fields:
        hint = _as_hinted(each.type.v)
        annotation = f'{each.name}{hint} = {each.default.v}' if each.default else f'{each.name}{hint}'
        yield annotation


@emit.case(Table)
def emit(node: Table, proc: Proc, ctx: Context):
    table_name = node.name
    proc += f'class {table_name}(__base__):'

    proc += [
        f'__tablename__ = {table_name.lower()!r}',
        "# primary keys",
    ]

    ctx = ctx.update(current_table=table_name)

    ## primary key
    proc_ = Proc([])
    proc_ += 'id: int = db.Column(Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)'

    ## fields
    proc_ += '# fields'

    proc_ += 'dbg_is_status_activated = db.Column(db.Boolean, nullable=False, default=True)'

    args = ','.join(_make_parameters(node.fields))
    for each in node.fields:
        proc_, ctx = emit(each, proc_, ctx)

    proc_ += '# constructor'
    proc_ ^= [
        'def __init__(self, {}):'.format(f'*, {args}' if args else ''),
        [
            '# noinspection PyArgumentList', 'super().__init__({})'.format(
                ', '.join(f'{each.name}={each.name}' for each in node.fields))
        ]
    ]

    ## repr
    proc_ += '# repr'
    proc_ += 'def __repr__(self):'
    fields = []
    for each in node.reprs or ('id', *(each.name for each in node.fields)):
        fields.append(
            Template('$field = {self.$field!r}').substitute(field=each))
    proc_ += [
        Template('return f"$tb($fields)"').substitute(
            tb=table_name, fields=', '.join(fields))
    ]

    ## relationships
    @ctx.relations.find_all
    def all_rels(rel: Relation):
        return rel.right == table_name or rel.left == table_name

    all_rels: t.List[Relation]
    if any(all_rels):
        proc_ += '# relationship'

    for rel in all_rels:
        rel_name = f'{rel.left}{rel.right}'
        self, other = rel.left, rel.right
        if rel.right == table_name:
            self, other = other, self
        proc_ += '@builtins.property'
        proc_ += f'def rel_{other.lower()}(self) -> "db.Query[{rel_name}]":'
        proc_ += [
            f'return db.filter_from_table({rel_name}, {rel_name}.{self.lower()}_id == self.id)'
        ]

        proc_ += '# add relation entity'
        add_rel_fn_params = ','.join(_make_parameters(rel.fields))
        add_rel_fn_args = ','.join(
            f'{each.name} = {each.name}' for each in rel.fields)
        proc_ += f'def add_rel_with_{other.lower()}(self, {other.lower()}: {other!r}, *, {add_rel_fn_params}):'
        proc_ += [
            f'__session__.add({rel_name}({self.lower()}_id = self.id, {other.lower()}_id = {other.lower()}.id, {add_rel_fn_args}))'
        ]

    proc_ += '# auto deactivate'
    proc_ += 'def deactivate(self) -> int:'
    proc_ += ['ret = 0']

    for rel in all_rels:
        # rel_name = f'{rel.left}{rel.right}'
        self, other = rel.left, rel.right
        weight = rel.weight
        if rel.right == table_name:
            self, other = other, self
            weight = reversed(weight)
        self_w, other_w = weight

        if not self_w:
            # 被主导
            proc_ += [
                f'for rel in self.rel_{other.lower()}.all():',
                ['rel.dbg_is_status_activated = False', 'ret += 1']
            ]
        elif other_w:
            # 双边主导
            proc_ += [
                f'rels = self.rel_{other.lower()}.all()',
                f'if len(rels) is 1 and rels[0].{self.lower()} == self:',
                [
                    f'other = rels[0].{other.lower()}.all()',
                    'if other is not None:',
                    ['ret += other.deactivate()'],
                ],
            ]
        else:
            # 主导对方
            proc_ += [
                f'for each in self.rel_{other.lower()}.all():',
                [
                    f'other = each.{other.lower()}', 'if other is not None:',
                    ['ret += other.deactivate()']
                ]
            ]
    proc_ += ['self.dbg_is_status_activated = False', 'return ret']

    proc += proc_.codes
    proc += [f'query : db.Query[{table_name!r}]']
    return proc, ctx


def emit_field(node: t.Union[Field], proc: Proc, ctx: Context):
    kws = []

    if '~' in node.option:
        seq_name = f'{ctx.current_table.lower()}_id_seq'
        kws.append(f'db.Sequence({seq_name!r})')

    if '?' in node.option:
        kws.append('nullable=True')
    else:
        kws.append('nullable=False')

    if '!' in node.option:
        kws.append('unique=True')

    kwargs = ', '.join(kws)
    hint = _as_hinted(node.type.v)
    ty = node.type

    if isinstance(ty, EnumValue):
        v = f'db.Enum({ty.v})'
    else:
        v = ty.v

    proc += f'{node.name}{hint} = db.Column({v}, {kwargs})'
    return proc, ctx


@emit.case(Field)
def emit(node, proc, ctx):
    return emit_field(node, proc, ctx)


@emit.case(Relation)
def emit(node: Relation, proc: Proc, ctx: Context):
    rel_name = f'{node.left}{node.right}'
    proc += f'class {rel_name}(__base__):'

    proc += [
        f'__tablename__ = {rel_name.lower()!r}',
        '# primary keys',
        'id: int = db.Column(Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)',
        f'{node.left.lower()}_id: int = db.Column(db.Integer)',
        f'{node.right.lower()}_id: int = db.Column(db.Integer)',
    ]

    proc_ = Proc([])

    ctx = ctx.update(current_table=rel_name)
    proc_ += '# fields'
    proc_ += 'dbg_is_status_activated: bool = db.Column(db.Boolean, nullable=False, default=True)'

    args = _make_parameters(node.fields)

    for each in node.fields:
        proc_, ctx = emit(each, proc_, ctx)

    proc_ += '# constructor'
    proc_ ^= [
        'def __init__(self, *, {}_id: int, {}_id: int, {}):'.format(
            node.left.lower(), node.right.lower(), ','.join(args)),
        [
            '# noinspection PyArgumentList',
            'super().__init__({0}_id={0}_id, {1}_id={1}_id, {2})'.format(
                node.left.lower(), node.right.lower(),
                ', '.join(f'{each.name}={each.name}' for each in node.fields))
        ]
    ]

    proc_ += '# relationship'

    def add_rel(rel_to: str):
        return [
            '@builtins.property',
            f'def {rel_to.lower()}(self) -> "db.typing.Optional[{rel_to}]":',
            [
                f'return db.filter_from_table({rel_to}, {rel_to}.id == self.{rel_to.lower()}_id).first()'
            ]
        ]

    proc_ ^= add_rel(node.left)
    proc_ ^= add_rel(node.right)

    proc_ += '# repr'
    proc_ += 'def __repr__(self):'

    fields = []

    for each in (f'{node.left.lower()}_id', f'{node.right.lower()}_id',
                 *[each.name for each in node.fields]):
        fields.append(
            Template('$field = {self.$field!r}').substitute(field=each))
    proc_ += [
        Template('return f"$rel($fields)"').substitute(
            rel=rel_name, fields=', '.join(fields))
    ]

    proc += proc_.codes
    proc += [f'query : db.Query[{rel_name!r}]']
    return proc, ctx


@emit.case(Engine)
def emit(node: Engine, proc: Proc, ctx: Context):
    configs = {**node.configs}
    url = configs['url']
    del configs['url']
    proc += 'engine = db.create_engine({url}, convert_unicode=True, {ops})'.format(
        url=url, ops=', '.join(f"{k} = {v}" for k, v in configs.items()))
    proc += '__session__: db.Session = db.scoped_session(db.sessionmaker(autocommit=False, autoflush=False, bind=engine))'
    proc ^= [
        '__base__ = db.declarative_base()',
        '# noinspection PyUnresolvedReferences',
        '__base__.query = __session__.query_property()'
    ]
    return proc, ctx


@emit.case(Python)
def emit(node: Python, proc: Proc, ctx: Context):
    proc += indent(dedent(node.codes), '    ')
    proc += '\n'
    return proc, ctx


def code_gen(asts: list):
    relations = RichList()
    tables = RichList()
    for each in asts:
        if isinstance(each, Relation):

            relations.append(each)
        elif isinstance(each, Table):
            tables.append(each)
        elif isinstance(each, (Python, Engine)):
            pass
        else:
            raise TypeError(type(each))

    ctx = Context('', tables, relations)
    proc = Proc([
        'from auto_orm.database.types import *',
        'import auto_orm.database.infrastructure as db',
        'import builtins',
    ])
    for each in asts:
        proc, ctx = emit(each, proc, ctx)
    proc += '__base__.metadata.create_all(bind=engine)'
    proc += 'session = __session__'

    return FormatCode(dedent(dumps(proc.codes)))[0]
