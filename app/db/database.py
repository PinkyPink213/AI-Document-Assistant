from sqlmodel import create_engine, Session  
from app.core.config  import settings

engine = create_engine(
    settings.postgres_url,
    echo=True,
)
        
# def create_db_and_tables():
#     SQLModel.metadata.create_all(engine)
    
def get_session():
    with Session(engine) as session:
        yield session