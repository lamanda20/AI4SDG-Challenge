import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, engine, Base
import models, crud, schemas

# Crée les tables si elles n'existent pas
Base.metadata.create_all(bind=engine)

FAKE_PATIENTS = [
    # Patient 1 : Diabétique épuisé, risque d'abandon élevé
    schemas.ClientCreate(
        name="Karim Benali",
        email="karim@sportrx.com",
        password="pass1234",
        role="client",
        age=55,
        gender="Male",
        chronic_condition="Type 2 Diabetes",
        biometrics=schemas.BiometricsCreate(
            hrv=28,
            daily_steps=2800,
            mood_score=3,
            recent_feedback="Je suis épuisé, j'ai mal aux jambes et je n'ai pas envie de bouger.",
            hba1c=8.1,
            blood_pressure="135/88",
            bmi=29.4,
            vo2_max=28.5
        )
    ),
    # Patient 2 : Hypertendue motivée, bonne récupération
    schemas.ClientCreate(
        name="Samira Ouali",
        email="samira@sportrx.com",
        password="pass1234",
        role="client",
        age=47,
        gender="Female",
        chronic_condition="Hypertension",
        biometrics=schemas.BiometricsCreate(
            hrv=62,
            daily_steps=7500,
            mood_score=8,
            recent_feedback="Je me sens bien aujourd'hui, prête pour ma séance !",
            blood_pressure="145/92",
            bmi=26.1,
            vo2_max=36.0
        )
    ),
    # Patient 3 : Dépression légère + sédentarité
    schemas.ClientCreate(
        name="Youssef Chaoui",
        email="youssef@sportrx.com",
        password="pass1234",
        role="client",
        age=38,
        gender="Male",
        chronic_condition="Mild Depression",
        biometrics=schemas.BiometricsCreate(
            hrv=40,
            daily_steps=1500,
            mood_score=4,
            recent_feedback="Je n'ai pas dormi, je me sens vide et sans énergie.",
            bmi=23.8,
            vo2_max=30.0
        )
    ),
    # Patient 4 : Cancer en rémission, prudence nécessaire
    schemas.ClientCreate(
        name="Nadia Ferhat",
        email="nadia@sportrx.com",
        password="pass1234",
        role="client",
        age=62,
        gender="Female",
        chronic_condition="Cancer Remission",
        biometrics=schemas.BiometricsCreate(
            hrv=45,
            daily_steps=4000,
            mood_score=6,
            recent_feedback="Je veux reprendre une activité douce, mais j'ai peur de me blesser.",
            bmi=22.0,
            vo2_max=25.0
        )
    ),
]


def seed():
    db = SessionLocal()
    try:
        existing = db.query(models.User).count()
        if existing > 0:
            print(f"⚠️  La base contient déjà {existing} utilisateur(s). Seed ignoré.")
            return

        for patient_data in FAKE_PATIENTS:
            user = crud.create_client(db=db, client=patient_data)
            print(f"  ✅ Créé : [{user.id}] {user.name} — {user.chronic_condition}")

        print(f"\n🎉 {len(FAKE_PATIENTS)} patients insérés avec succès !")
    finally:
        db.close()


if __name__ == "__main__":
    print("Insertion des faux patients...\n")
    seed()
