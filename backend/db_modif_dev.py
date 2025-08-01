from sqlalchemy import text
from sqlmodel import SQLModel, Session, create_engine, select

engine = create_engine("sqlite:///data/database.db")

with Session(engine) as session:
    result = session.execute(text("PRAGMA table_info(coachtraininglinks);"))
    rows = result.fetchall()
    for row in rows:
        print(row)

# with Session(engine) as session:

    # try:
    #     session.execute(text("ALTER TABLE health_check ADD COLUMN single_leg_proprio_test INT"))
    # except Exception as e:
    #     print(f"Erreur lors de l'ajout de la colonne single_leg_proprio_test: {e}")
        
    # try:
    #     session.execute(text("UPDATE health_check SET single_leg_proprio_test = NULL"))
    # except Exception as e:
    #     print(f"Erreur lors de l'initialisation de la colonne single_leg_proprio_test: {e}")

    # try:
    #     session.execute(text("ALTER TABLE health_check RENAME COLUMN sleep_hour TO wakeup_time"))
    # except Exception as e:
    #     print(f"Erreur lors de l'initialisation de la colonne stress_level: {e}")

    # try:
    #     session.execute(text("DELETE FROM health_check WHERE id IS NULL;"))
    # except Exception as e:
    #     print(f"Erreur: {e}")

    # try:
    #     # session.execute(text("PRAGMA table_info(health_check);"))
    #     session.execute(text("ALTER TABLE physicalissueticket DROP COLUMN date_closed;"))
    #     session.execute(text("ALTER TABLE physicalissueticket DROP COLUMN closed_reason;"))
    #     session.execute(text("ALTER TABLE physicalissueticket ADD COLUMN is_closed BOOLEAN DEFAULT FALSE"))
    # except Exception as e:
    #     print(f"Erreur: {e}")

    # session.commit()
