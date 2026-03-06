from db.database import engine, Base
from db.models import User, Operation

Base.metadata.create_all(bind=engine)
