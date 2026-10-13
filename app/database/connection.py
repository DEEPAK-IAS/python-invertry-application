from __future__ import annotations
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, Session
from app.database.base import Base
from app.config.settings import DATABASE_URL
from app.utils.logger import logger

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# def _migrate_pending_bill_columns():
#     """
#     Base.metadata.create_all() only creates NEW tables — it never adds columns
#     to a table that already exists. Since older installs already have a
#     `sales` table (without paid_amount/due_amount/payment_status), we add
#     those columns here by hand so existing customer databases keep working.
#     """
#     inspector = inspect(engine)
#     if "sales" not in inspector.get_table_names():
#         return  # brand-new DB — create_all() above already made it correctly

#     existing_cols = {c["name"] for c in inspector.get_columns("sales")}
#     first_time = "paid_amount" not in existing_cols

#     with engine.begin() as conn:
#         if "paid_amount" not in existing_cols:
#             conn.execute(text("ALTER TABLE sales ADD COLUMN paid_amount FLOAT DEFAULT 0.0"))
#         if "due_amount" not in existing_cols:
#             conn.execute(text("ALTER TABLE sales ADD COLUMN due_amount FLOAT DEFAULT 0.0"))
#         if "payment_status" not in existing_cols:
#             conn.execute(text("ALTER TABLE sales ADD COLUMN payment_status VARCHAR DEFAULT 'PAID'"))

#         if first_time:
#             # Sales made before this feature existed were fully settled at
#             # the time — treat them as fully paid instead of "due".
#             conn.execute(text(
#                 "UPDATE sales SET paid_amount = total_amount, "
#                 "due_amount = 0.0, payment_status = 'PAID'"
#             ))
#             logger.info("Migrated existing sales -> marked as fully paid (pre pending-bill feature).")

# def _migrate_user_columns():
#     inspector = inspect(engine)
#     if "users" not in inspector.get_table_names():
#         return
#     existing_cols = {c["name"] for c in inspector.get_columns("users")}
#     with engine.begin() as conn:
#         if "company_phone" not in existing_cols:
#             conn.execute(text("ALTER TABLE users ADD COLUMN company_phone VARCHAR"))
            
# def _migrate_invoice_detail_columns():
#     inspector = inspect(engine)
#     if "sales" in inspector.get_table_names():
#         cols = {c["name"] for c in inspector.get_columns("sales")}
#         with engine.begin() as conn:
#             if "customer_gstin" not in cols:
#                 conn.execute(text("ALTER TABLE sales ADD COLUMN customer_gstin VARCHAR"))
#     if "sale_items" in inspector.get_table_names():
#         cols = {c["name"] for c in inspector.get_columns("sale_items")}
#         with engine.begin() as conn:
#             if "size" not in cols:
#                 conn.execute(text("ALTER TABLE sale_items ADD COLUMN size VARCHAR"))
                
# def _migrate_user_columns():
#     inspector = inspect(engine)
#     if "users" not in inspector.get_table_names():
#         return
#     existing_cols = {c["name"] for c in inspector.get_columns("users")}
#     with engine.begin() as conn:
#         if "company_phone" not in existing_cols:
#             conn.execute(text("ALTER TABLE users ADD COLUMN company_phone VARCHAR"))
#         if "preferred_printer" not in existing_cols:
#             conn.execute(text("ALTER TABLE users ADD COLUMN preferred_printer VARCHAR"))
                
def _auto_migrate_missing_columns():
    """
    Generic, additive schema migration.

    Base.metadata.create_all() (used below in init_db()) only creates
    BRAND-NEW tables -- it never alters a table that already exists.
    That's exactly what caused the "no such column: users.company_logo_path"
    crash: the `users` table already existed on disk from before that
    column was added to the User model, so create_all() silently did
    nothing for it.

    Instead of hand-writing one ALTER TABLE per column (the commented-out
    functions above show how easy it is to add a column to a model and
    forget the matching migration), this walks every model table that
    already exists in the database and adds any column the model defines
    but the actual table is missing. It never drops, renames, or
    modifies an existing column, and never touches existing rows, so it
    cannot cause data loss -- worst case a brand-new column is simply
    NULL for old rows, which is what you'd want anyway.

    This is a safety net, not a replacement for a real migration tool.
    See REFACTOR_CHANGELOG.md for the recommended Alembic setup for
    anything more involved than "add a column" (renames, type changes,
    dropping a column, data backfills with logic).
    """
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if table.name not in existing_tables:
                continue  # brand-new table -- create_all() already made it correctly
            existing_cols = {c["name"] for c in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in existing_cols:
                    continue
                try:
                    col_type = column.type.compile(dialect=engine.dialect)
                    conn.execute(text(
                        f'ALTER TABLE {table.name} ADD COLUMN "{column.name}" {col_type}'
                    ))
                    logger.info(f"Auto-migrated: added column {table.name}.{column.name}")
                except Exception as e:
                    # Never let one column's migration failure crash startup --
                    # log it and keep going so the rest of the app still opens.
                    logger.warning(f"Could not add column {table.name}.{column.name}: {e}")


def init_db():
    from app.models import product, customer, supplier, user, sale, purchase, purchase_item  # noqa

    Base.metadata.create_all(bind=engine, checkfirst=True)  # Now creates purchases and purchase_items tables!
    # Inspect existing tables first to prevent redundant creation crashes
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    if "users" not in existing_tables:
        Base.metadata.create_all(bind=engine, checkfirst=True)

    # Adds any column that exists on a model but not yet on the actual
    # table (e.g. company_logo_path on an older database) -- additive
    # only, never touches existing data.
    _auto_migrate_missing_columns()

    logger.info("Database initialized successfully")

def get_session() -> Session:
    return SessionLocal()





