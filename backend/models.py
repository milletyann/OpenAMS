from typing import Optional
from sqlmodel import SQLModel, Field, create_engine, Session, select

class AthleteBase(SQLModel):
    name: str
    age: int
    sport: str
    sexe: str

class AthleteCreate(AthleteBase):
    pass

class Athlete(AthleteBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


# C'ÉTAIT JUSTE POUR TESTER SI LA BDD FONCTIONNE
# # Step 1: Create the database engine
# engine = create_engine("sqlite:///backend/data/athletes.db")

# # Step 2: Create the tables in the database
# SQLModel.metadata.create_all(engine)

# # Step 3: Add a sample athlete
# with Session(engine) as session:
#     athlete = Athlete(name="Usain Bolt", sport='Athletisme', age=36, sexe='M')
#     session.add(athlete)
#     session.commit()
    

# # Step 4: Test if it worked
# with Session(engine) as session:
#     statement = select(Athlete)
#     results = session.exec(statement).all()

#     for athlete in results:
#         print(athlete)