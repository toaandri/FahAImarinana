"""Minimal newsroom registry for disposable AUTO_CREATE_TABLES development mode."""
from sqlalchemy import select, text
from ..models import Newsroom


def bootstrap_newsrooms(connection):
    for identifier,slug,name,dataset in (
        (1,'default-real','Rédaction principale','real'),
        (2,'legacy-quarantine','Archives non classifiées','quarantine'),
    ):
        if connection.scalar(select(Newsroom.__table__.c.id).where(Newsroom.__table__.c.id==identifier)) is None:
            connection.execute(Newsroom.__table__.insert().values(id=identifier,slug=slug,name=name,dataset=dataset,status='active'))
    if connection.dialect.name=='postgresql':
        connection.execute(text("SELECT setval(pg_get_serial_sequence('newsrooms','id'), (SELECT max(id) FROM newsrooms), true)"))
