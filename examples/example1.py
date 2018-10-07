from auto_orm.database.types import *
import auto_orm.database.infrastructure as db
import builtins
engine = db.create_engine(
    "sqlite:///:memory:",
    convert_unicode=True,
)
__session__: db.Session = db.scoped_session(
    db.sessionmaker(autocommit=False, autoflush=False, bind=engine))
__base__ = db.declarative_base()
# noinspection PyUnresolvedReferences
__base__.query = __session__.query_property()

print('start engine')


class User(__base__):
    __tablename__ = 'user'
    # primary keys
    id: int = db.Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False,
        unique=True)
    # fields
    dbg_is_status_activated = db.Column(
        db.Boolean, nullable=False, default=True)
    a: 'int' = db.Column(Integer, nullable=False)
    b: 'int' = db.Column(Integer, nullable=False)

    # constructor
    def __init__(self, *, a: 'int' = (1 + 2), b: 'int' = (2 + 3)):
        # noinspection PyArgumentList
        super().__init__(a=a, b=b)

    # repr
    def __repr__(self):
        return f"User(id = {self.id!r}, a = {self.a!r}, b = {self.b!r})"

    # relationship
    @builtins.property
    def rel_card(self) -> "db.Query[UserCard]":
        return db.filter_from_table(UserCard, UserCard.user_id == self.id)

    # add relation entity
    def add_rel_with_card(self, card: 'Card', *, content: str):
        __session__.add(
            UserCard(user_id=self.id, card_id=card.id, content=content))

    @builtins.property
    def rel_spot(self) -> "db.Query[UserSpot]":
        return db.filter_from_table(UserSpot, UserSpot.user_id == self.id)

    # add relation entity
    def add_rel_with_spot(self, spot: 'Spot', *, item: 'str'):
        __session__.add(UserSpot(user_id=self.id, spot_id=spot.id, item=item))

    # auto deactivate
    def deactivate(self) -> int:
        ret = 0
        rels = self.rel_card.all()
        if len(rels) is 1 and rels[0].user == self:
            other = rels[0].card.all()
            if other is not None:
                ret += other.deactivate()
        for rel in self.rel_spot.all():
            rel.dbg_is_status_activated = False
            ret += 1
        self.dbg_is_status_activated = False
        return ret

    query: db.Query['User']


class Card(__base__):
    __tablename__ = 'card'
    # primary keys
    id: int = db.Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False,
        unique=True)
    # fields
    dbg_is_status_activated = db.Column(
        db.Boolean, nullable=False, default=True)
    content: str = db.Column(String(30), nullable=False, unique=True)

    # constructor
    def __init__(self, *, content: str):
        # noinspection PyArgumentList
        super().__init__(content=content)

    # repr
    def __repr__(self):
        return f"Card(id = {self.id!r}, content = {self.content!r})"

    # relationship
    @builtins.property
    def rel_user(self) -> "db.Query[UserCard]":
        return db.filter_from_table(UserCard, UserCard.card_id == self.id)

    # add relation entity
    def add_rel_with_user(self, user: 'User', *, content: str):
        __session__.add(
            UserCard(card_id=self.id, user_id=user.id, content=content))

    @builtins.property
    def rel_spot(self) -> "db.Query[CardSpot]":
        return db.filter_from_table(CardSpot, CardSpot.card_id == self.id)

    # add relation entity
    def add_rel_with_spot(self, spot: 'Spot', *, info: 'str'):
        __session__.add(CardSpot(card_id=self.id, spot_id=spot.id, info=info))

    # auto deactivate
    def deactivate(self) -> int:
        ret = 0
        rels = self.rel_user.all()
        if len(rels) is 1 and rels[0].card == self:
            other = rels[0].user.all()
            if other is not None:
                ret += other.deactivate()
        for each in self.rel_spot.all():
            other = each.spot
            if other is not None:
                ret += other.deactivate()
        self.dbg_is_status_activated = False
        return ret

    query: db.Query['Card']


class Spot(__base__):
    __tablename__ = 'spot'
    # primary keys
    id: int = db.Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False,
        unique=True)
    # fields
    dbg_is_status_activated = db.Column(
        db.Boolean, nullable=False, default=True)
    name: str = db.Column(String(30), nullable=False)

    # constructor
    def __init__(self, *, name: str):
        # noinspection PyArgumentList
        super().__init__(name=name)

    # repr
    def __repr__(self):
        return f"Spot(id = {self.id!r}, name = {self.name!r})"

    # relationship
    @builtins.property
    def rel_user(self) -> "db.Query[UserSpot]":
        return db.filter_from_table(UserSpot, UserSpot.spot_id == self.id)

    # add relation entity
    def add_rel_with_user(self, user: 'User', *, item: 'str'):
        __session__.add(UserSpot(spot_id=self.id, user_id=user.id, item=item))

    @builtins.property
    def rel_card(self) -> "db.Query[CardSpot]":
        return db.filter_from_table(CardSpot, CardSpot.spot_id == self.id)

    # add relation entity
    def add_rel_with_card(self, card: 'Card', *, info: 'str'):
        __session__.add(CardSpot(spot_id=self.id, card_id=card.id, info=info))

    # auto deactivate
    def deactivate(self) -> int:
        ret = 0
        for each in self.rel_user.all():
            other = each.user
            if other is not None:
                ret += other.deactivate()
        for rel in self.rel_card.all():
            rel.dbg_is_status_activated = False
            ret += 1
        self.dbg_is_status_activated = False
        return ret

    query: db.Query['Spot']


class UserCard(__base__):
    __tablename__ = 'usercard'
    # primary keys
    id: int = db.Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False,
        unique=True)
    user_id: int = db.Column(db.Integer)
    card_id: int = db.Column(db.Integer)
    # fields
    dbg_is_status_activated: bool = db.Column(
        db.Boolean, nullable=False, default=True)
    content: str = db.Column(String(30), nullable=False)

    # constructor
    def __init__(self, *, user_id: int, card_id: int, content: str):
        # noinspection PyArgumentList
        super().__init__(user_id=user_id, card_id=card_id, content=content)

    # relationship
    @builtins.property
    def user(self) -> "db.typing.Optional[User]":
        return db.filter_from_table(User, User.id == self.user_id).first()

    @builtins.property
    def card(self) -> "db.typing.Optional[Card]":
        return db.filter_from_table(Card, Card.id == self.card_id).first()

    # repr
    def __repr__(self):
        return f"UserCard(user_id = {self.user_id!r}, card_id = {self.card_id!r}, content = {self.content!r})"

    query: db.Query['UserCard']


class UserSpot(__base__):
    __tablename__ = 'userspot'
    # primary keys
    id: int = db.Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False,
        unique=True)
    user_id: int = db.Column(db.Integer)
    spot_id: int = db.Column(db.Integer)
    # fields
    dbg_is_status_activated: bool = db.Column(
        db.Boolean, nullable=False, default=True)
    item: 'str' = db.Column(Text, nullable=False)

    # constructor
    def __init__(self, *, user_id: int, spot_id: int, item: 'str'):
        # noinspection PyArgumentList
        super().__init__(user_id=user_id, spot_id=spot_id, item=item)

    # relationship
    @builtins.property
    def user(self) -> "db.typing.Optional[User]":
        return db.filter_from_table(User, User.id == self.user_id).first()

    @builtins.property
    def spot(self) -> "db.typing.Optional[Spot]":
        return db.filter_from_table(Spot, Spot.id == self.spot_id).first()

    # repr
    def __repr__(self):
        return f"UserSpot(user_id = {self.user_id!r}, spot_id = {self.spot_id!r}, item = {self.item!r})"

    query: db.Query['UserSpot']


class CardSpot(__base__):
    __tablename__ = 'cardspot'
    # primary keys
    id: int = db.Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False,
        unique=True)
    card_id: int = db.Column(db.Integer)
    spot_id: int = db.Column(db.Integer)
    # fields
    dbg_is_status_activated: bool = db.Column(
        db.Boolean, nullable=False, default=True)
    info: 'str' = db.Column(Text, nullable=False)

    # constructor
    def __init__(self, *, card_id: int, spot_id: int, info: 'str'):
        # noinspection PyArgumentList
        super().__init__(card_id=card_id, spot_id=spot_id, info=info)

    # relationship
    @builtins.property
    def card(self) -> "db.typing.Optional[Card]":
        return db.filter_from_table(Card, Card.id == self.card_id).first()

    @builtins.property
    def spot(self) -> "db.typing.Optional[Spot]":
        return db.filter_from_table(Spot, Spot.id == self.spot_id).first()

    # repr
    def __repr__(self):
        return f"CardSpot(card_id = {self.card_id!r}, spot_id = {self.spot_id!r}, info = {self.info!r})"

    query: db.Query['CardSpot']


__base__.metadata.create_all(bind=engine)
session = __session__
