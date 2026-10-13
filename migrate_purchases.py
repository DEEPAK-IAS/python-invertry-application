from app.database.connection import engine, Base
from app.models.purchase import Purchase
from app.models.purchase_item import PurchaseItem
from app.models.supplier import Supplier
from app.models.user import User

def run_migration():
    print("Migrating database for Purchases and Purchase Items...")
    Base.metadata.create_all(bind=engine)
    print("Migration successful! New tables created.")

if __name__ == "__main__":
    run_migration()