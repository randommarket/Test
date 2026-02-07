from datetime import date

from app.auth.security import hash_password
from app.db.session import SessionLocal
from app.models.entities import Actual, Company, Organization, Scenario, User


def run():
    db = SessionLocal()
    org = Organization(name="Demo Org")
    db.add(org)
    db.commit()
    db.refresh(org)
    user = User(org_id=org.id, email="demo@example.com", hashed_password=hash_password("demo"), role="org_admin")
    db.add(user)
    companies = [
        Company(org_id=org.id, name="Atlas Labs", sector="AI"),
        Company(org_id=org.id, name="Beacon Health", sector="Health"),
        Company(org_id=org.id, name="Crest Retail", sector="Retail"),
    ]
    db.add_all(companies)
    db.commit()
    for company in companies:
        db.add(
            Scenario(
                company_id=company.id,
                name="Base",
                revenue_growth=0.05,
                gross_margin=0.6,
                opex_growth=0.03,
            )
        )
        for month in range(1, 7):
            db.add(
                Actual(
                    company_id=company.id,
                    period=date(2024, month, 1),
                    category="Revenue",
                    amount=10000 + month * 500,
                )
            )
            db.add(
                Actual(
                    company_id=company.id,
                    period=date(2024, month, 1),
                    category="COGS",
                    amount=3000 + month * 200,
                )
            )
            db.add(
                Actual(
                    company_id=company.id,
                    period=date(2024, month, 1),
                    category="Sales & Marketing",
                    amount=2000 + month * 150,
                )
            )
            db.add(
                Actual(
                    company_id=company.id,
                    period=date(2024, month, 1),
                    category="Cash",
                    amount=50000 - month * 2000,
                )
            )
    db.commit()
    db.close()


if __name__ == "__main__":
    run()
