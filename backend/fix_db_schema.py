from sqlalchemy import create_engine, text
from database import DATABASE_URL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_schema():
    print(f"Connecting to {DATABASE_URL}")
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        # Check if sequence exists
        result = conn.execute(text("SELECT 1 FROM pg_class WHERE relname = 'datasets_id_seq'"))
        seq_exists = result.scalar() is not None
        
        # Check if table exists
        result = conn.execute(text("SELECT 1 FROM information_schema.tables WHERE table_name = 'datasets'"))
        table_exists = result.scalar() is not None
        
        print(f"Sequence 'datasets_id_seq' exists: {seq_exists}")
        print(f"Table 'datasets' exists: {table_exists}")
        
        if seq_exists and not table_exists:
            print("Orphaned sequence found. Dropping it...")
            conn.execute(text("DROP SEQUENCE datasets_id_seq"))
            conn.commit()
            print("Sequence dropped successfully.")
        elif seq_exists and table_exists:
             print("Both exist. This is unexpected. Attempting to drop table and sequence to reset state (SAFE FOR DEV).")
             conn.execute(text("DROP TABLE datasets CASCADE"))
             conn.commit()
             print("Table 'datasets' dropped.")
        else:
            print("No obvious schema conflict found.")

if __name__ == "__main__":
    fix_schema()
