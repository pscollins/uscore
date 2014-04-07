import os

BASE = ".."
DATA = "data"
_RELATIVE_SQLALCHEMY_DB_URI = os.path.join(DATA, "sqlite.db")
SQLALCHEMY_DB_URI = "sqlite:///{}".format(
    os.path.join(BASE, _RELATIVE_SQLALCHEMY_DB_URI))
