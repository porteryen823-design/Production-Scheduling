import os
import sys
from dotenv import load_dotenv
load_dotenv()

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'backend', 'src'))

from infra.db.database import SessionLocal
from domain.models import UISetting

def test_query():
    db = SessionLocal()
    try:
        parameter_name = "gantt_show_marker"
        query = db.query(UISetting)
        if parameter_name:
            query = query.filter(UISetting.parameter_name.ilike(f"%{parameter_name}%"))
        results = query.offset(0).limit(100).all()
        print(f"Found {len(results)} results")
        for r in results:
            print(f"ID: {r.id}, Name: {r.parameter_name}, Created: {r.created_at}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_query()
