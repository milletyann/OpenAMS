from sqlalchemy import text
from sqlmodel import SQLModel, Session, create_engine, select

engine = create_engine("sqlite:///data/database.db")
#engine = create_engine("sqlite:///data/season2526.db")

# with Session(engine) as session:
#     result = session.execute(text("PRAGMA table_info(decathlonperformance);"))
#     rows = result.fetchall()
#     for row in rows:
#         print(row)

with Session(engine) as session:

    # SUPPRIMER UNE LIGNE PRÉCISE
    # try:
    #     session.execute(text("DELETE FROM health_check WHERE date = '2025-08-10'"))
    # except Exception as e:
    #     print(f"Erreur lors de la suppression de la ligne: {e}")
    #     session.rollback()

    # AJOUTER UNE COLONNE
    # try:
    #     session.execute(text("ALTER TABLE health_check ADD COLUMN single_leg_proprio_test INT"))
    # except Exception as e:
    #     print(f"Erreur lors de l'ajout de la colonne single_leg_proprio_test: {e}")
        
    # MODIFIER TOUTES LES VALEURS D'UNE COLONNE
    # try:
    #     session.execute(text("UPDATE health_check SET single_leg_proprio_test = NULL"))
    #     session.execute(text("UPDATE health_check SET single_leg_proprio_test = 125 WHERE date = '2025-08-06'"))
    # except Exception as e:
    #     print(f"Erreur lors de l'initialisation de la colonne single_leg_proprio_test: {e}")

    # RENOMMER UNE COLONNE
    # try:
    #     session.execute(text("ALTER TABLE health_check RENAME COLUMN sleep_hour TO wakeup_time"))
    # except Exception as e:
    #     print(f"Erreur lors de l'initialisation de la colonne stress_level: {e}")

    # SUPPRIMER LES LIGNES REMPLISSANT UNE CERTAINE CONDITION
    # try:
    #     session.execute(text("DELETE FROM user WHERE name IS 'Antoine blabla';"))
    # except Exception as e:
    #     print(f"Erreur: {e}")

    # DUPLIQUER UNE TABLE SANS CERTAINES COLONNES
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
