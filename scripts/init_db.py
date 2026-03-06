from app.db.session import Base, engine
from app.models import models  # noqa: F401

Base.metadata.create_all(bind=engine)
print('DB initialized')
