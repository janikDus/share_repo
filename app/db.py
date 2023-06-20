# app/db.py

import databases
import ormar
import sqlalchemy

from .config import settings

database = databases.Database(settings.db_url)
metadata = sqlalchemy.MetaData()


class BaseMeta(ormar.ModelMeta):
    metadata = metadata
    database = database


class Reality(ormar.Model):
    class Meta(BaseMeta):
        tablename = "sreality"

    id: int = ormar.Integer(primary_key=True)
    adv_name: str = ormar.String(max_length=128, unique=False, nullable=False)
    adv_img_link: str = ormar.String(max_length=256, unique=False, nullable=False)
    active: bool = ormar.Boolean(default=True, nullable=False)


engine = sqlalchemy.create_engine(settings.db_url)
metadata.create_all(engine)

