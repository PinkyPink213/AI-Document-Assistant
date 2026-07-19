from sqlmodel import create_engine, SQLModel, Session   

DATABASE_URL = (
    "postgresql+psycopg://postgres:password@localhost:5432/enterprise_ai"
)

engine = create_engine(
    DATABASE_URL,
    echo=True,
)


def get_session():
    with Session(engine) as session:
        yield session