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


class Spirit(__base__):
    __tablename__ = 'spirit'
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
        return f"Spirit(id = {self.id!r}, name = {self.name!r})"

    # relationship
    @builtins.property
    def rel_site(self) -> "db.Query[SpiritSite]":
        return db.filter_from_table(SpiritSite,
                                    SpiritSite.spirit_id == self.id)

    # add relation entity
    def add_rel_with_site(self, site: 'Site', *, score: 'float'):
        __session__.add(
            SpiritSite(spirit_id=self.id, site_id=site.id, score=score))

    # auto deactivate
    def deactivate(self) -> int:
        ret = 0
        rels = self.rel_site.all()
        if len(rels) is 1 and rels[0].spirit == self:
            other = rels[0].site.all()
            if other is not None:
                ret += other.deactivate()
        self.dbg_is_status_activated = False
        return ret

    query: db.Query['Spirit']


class Site(__base__):
    __tablename__ = 'site'
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

    # constructor
    def __init__(self, ):
        # noinspection PyArgumentList
        super().__init__()

    # repr
    def __repr__(self):
        return f"Site(id = {self.id!r})"

    # relationship
    @builtins.property
    def rel_spirit(self) -> "db.Query[SpiritSite]":
        return db.filter_from_table(SpiritSite, SpiritSite.site_id == self.id)

    # add relation entity
    def add_rel_with_spirit(self, spirit: 'Spirit', *, score: 'float'):
        __session__.add(
            SpiritSite(site_id=self.id, spirit_id=spirit.id, score=score))

    # auto deactivate
    def deactivate(self) -> int:
        ret = 0
        rels = self.rel_spirit.all()
        if len(rels) is 1 and rels[0].site == self:
            other = rels[0].spirit.all()
            if other is not None:
                ret += other.deactivate()
        self.dbg_is_status_activated = False
        return ret

    query: db.Query['Site']


class SpiritSite(__base__):
    __tablename__ = 'spiritsite'
    # primary keys
    id: int = db.Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False,
        unique=True)
    spirit_id: int = db.Column(db.Integer)
    site_id: int = db.Column(db.Integer)
    # fields
    dbg_is_status_activated: bool = db.Column(
        db.Boolean, nullable=False, default=True)
    score: 'float' = db.Column(Float, nullable=False)

    # constructor
    def __init__(self, *, spirit_id: int, site_id: int, score: 'float'):
        # noinspection PyArgumentList
        super().__init__(spirit_id=spirit_id, site_id=site_id, score=score)

    # relationship
    @builtins.property
    def spirit(self) -> "db.typing.Optional[Spirit]":
        return db.filter_from_table(Spirit,
                                    Spirit.id == self.spirit_id).first()

    @builtins.property
    def site(self) -> "db.typing.Optional[Site]":
        return db.filter_from_table(Site, Site.id == self.site_id).first()

    # repr
    def __repr__(self):
        return f"SpiritSite(spirit_id = {self.spirit_id!r}, site_id = {self.site_id!r}, score = {self.score!r})"

    query: db.Query['SpiritSite']


__base__.metadata.create_all(bind=engine)
session = __session__
