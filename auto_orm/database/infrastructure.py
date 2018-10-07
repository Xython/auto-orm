from .hinting import *
from sqlalchemy import (create_engine, Integer, String, DateTime, ForeignKey,
                        Sequence, SmallInteger, Enum, Date, Table, Column,
                        Boolean, and_)
from sqlalchemy.orm import scoped_session, sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, date, time
from decimal import Decimal
import typing


def filter_from_table(table, cond):
    return table.query.filter(
        and_(cond, table.dbg_is_status_activated == True))
