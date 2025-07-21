from sqlalchemy import text
from sqlmodel import Session, create_engine, select

engine = create_engine("sqlite:///data/database.db")

with Session(engine) as session:
    
    for table_name in ["decathlonperformance", "decathlonathletelink", "decathlon"]:
        try:
            session.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
        except Exception as e:
            print(f"Erreur de suppression de {table_name}: {e}")

    session.commit()