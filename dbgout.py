from auto_orm.database.types import *
import auto_orm.database.infrastructure as db
import builtins
engine = db.create_engine(
    "sqlite:///:memory:",
    convert_unicode=True,
)
__session__ = db.scoped_session(
    db.sessionmaker(autocommit=False, autoflush=False, bind=engine))
__base__ = db.declarative_base()
__base__.query = __session__.query_property()

print('start engine')


class User(__base__):
    __tablename__ = 'user'
    # primary keys
    id: int = db.Column(
        Integer,
        db.Sequence('user_id_seq'),
        primary_key=True,
        autoincrement=True,
        nullable=False)
    # fields
    dbg_is_status_activated = db.Column(
        db.Boolean, nullable=False, default=True)
    a: int = db.Column(Integer, nullable=False)
    b: int = db.Column(Integer, nullable=False)

    # constructor
    def __init__(self, *, a: int = (1 + 2), b: int = (2 + 3)):
        super().__init__(a=a, b=b)

    # repr
    def __repr__(self):
        return f"User(id = {self.id}, a = {self.a}, b = {self.b})"

    # relationship
    @builtins.property
    def rel_card(self) -> "db.Query[UserCard]":
        return db.filter_from_table(UserCard, UserCard.user_id == self.id)

    # auto deactivate
    def deactivate(self) -> int:
        ret = 0
        rel = self.rel_card
        rev_rels = rel.all()
        if len(rev_rels) is 1 and rev_rels[0] == self:
            for each in rel.card.all():
                ret += each.deactivate()
            rel.dbg_is_status_activated = False
            ret += 1
        self.dbg_is_status_activated = False
        return ret + 1


class Card(__base__):
    __tablename__ = 'card'
    # primary keys
    id: int = db.Column(
        Integer,
        db.Sequence('card_id_seq'),
        primary_key=True,
        autoincrement=True,
        nullable=False)
    # fields
    dbg_is_status_activated = db.Column(
        db.Boolean, nullable=False, default=True)
    content: String(30) = db.Column(String(30), nullable=False, unique=True)

    # constructor
    def __init__(self, *, content: String(30)):
        super().__init__(content=content)

    # repr
    def __repr__(self):
        return f"Card(id = {self.id}, content = {self.content})"

    # relationship
    @builtins.property
    def rel_user(self) -> "db.Query[UserCard]":
        return db.filter_from_table(UserCard, UserCard.card_id == self.id)

    # auto deactivate
    def deactivate(self) -> int:
        ret = 0
        rel = self.rel_user
        rev_rels = rel.card.all()
        if len(rev_rels) is 1 and rev_rels[0] == self:
            for each in rel.user.all():
                ret += each.deactivate()
            rel.dbg_is_status_activated = False
            ret += 1
        self.dbg_is_status_activated = False
        return ret + 1


class UserCard(__base__):
    __tablename__ = 'usercard'
    # primary keys
    user_id = db.Column(db.Integer, primary_key=True)
    card_id = db.Column(db.Integer, primary_key=True)
    # fields
    dbg_is_status_activated: bool = db.Column(
        db.Boolean, nullable=False, default=True)
    content: String(30) = db.Column(String(30), nullable=False)

    # constructor
    def __init__(self, *, content: String(30)):
        super().__init__(content=content)

    # relationship
    @builtins.property
    def user(self) -> "db.typing.Optional[User]":
        return db.filter_from_table(User, User.id == self.user_id).first()

    @builtins.property
    def card(self) -> "db.typing.Optional[Card]":
        return db.filter_from_table(Card, Card.id == self.card_id).first()

    # repr
    def __repr__(self):
        return f"UserCard(user_id = {self.user_id}, card_id = {self.card_id}, content = {self.content})"


__base__.metadata.create_all(bind=engine)
session = __session__
