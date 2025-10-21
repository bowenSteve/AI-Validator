from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()

from .upload import Upload
from .comparison import Comparison

__all__ = ['db', 'Upload', 'Comparison']