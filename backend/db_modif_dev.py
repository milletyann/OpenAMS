from sqlalchemy import text
from sqlmodel import SQLModel, Session, create_engine, select

engine = create_engine("sqlite:///data/database.db")

# with Session(engine) as session:
#     result = session.execute(text("PRAGMA table_info(decathlonperformance);"))
#     rows = result.fetchall()
#     for row in rows:
#         print(row)

with Session(engine) as session:

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
        #session.execute(text("ALTER TABLE decathlonperformance RENAME TO decathlonperformance_old;"))
        # session.execute(text("""
        #     CREATE TABLE decathlonperformance (
        #         id INTEGER PRIMARY KEY AUTOINCREMENT,
        #         decathlon_id INTEGER NOT NULL,
        #         user_id INTEGER NOT NULL,
        #         event TEXT NOT NULL,
        #         performance TEXT,
        #         score INTEGER,
        #         date DATE,
        #         FOREIGN KEY(decathlon_id) REFERENCES decathlon(id),
        #         FOREIGN KEY(user_id) REFERENCES user(id)
        #     );
        # """))
        
        # session.execute(text("""
        #     INSERT INTO decathlonperformance (id, user_id, decathlon_id, event, performance, score, date)
        #     SELECT id, user_id, decathlon_id, event, CAST(performance AS TEXT), score, date
        #     FROM decathlonperformance_old;
        # """))
        
        # session.execute(text("DROP TABLE decathlonperformance_old;"))
    # except Exception as e:
    #     print(f"Erreur: {e}")
        
    

    session.commit()
