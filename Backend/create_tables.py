"""
Script to create all database tables
Run this once to initialize your database
"""
from app.db_config import engine, Base
# Import all models so they register with Base
from app.models import User, UserFinancials

def create_tables():
    """Create all tables in the database"""
    print("🔨 Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully!")
    
    # Print created tables
    print("\n📋 Created tables:")
    for table in Base.metadata.sorted_tables:
        print(f"  - {table.name}")

if __name__ == "__main__":
    create_tables()