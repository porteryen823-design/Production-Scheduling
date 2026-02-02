import sys
import os
import io

# Windows unicode fix
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Load .env manually and map MYSQL_ vars to DB_ vars for config.py
from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), '.env'))

os.environ['DB_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
os.environ['DB_PORT'] = os.getenv('MYSQL_PORT', '3306')
os.environ['DB_USER'] = os.getenv('MYSQL_USER', 'root')
os.environ['DB_PASSWORD'] = os.getenv('MYSQL_PASSWORD', '1234')
os.environ['DB_NAME'] = os.getenv('MYSQL_DATABASE', 'Scheduling')

# Add project root to sys.path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'backend', 'src'))

from sqlalchemy import select
from infra.db.database import SessionLocal
from domain.models.simulation_planning_job import SimulationPlanningJob
from domain.models.dynamic_scheduling_job import DynamicSchedulingJob

def check_join():
    print(f"Connecting to DB at {os.environ['DB_HOST']}:{os.environ['DB_PORT']} as {os.environ['DB_USER']}")
    db = SessionLocal()
    try:
        # Construct the query
        statement = select(
            SimulationPlanningJob.key_value,
            SimulationPlanningJob.remark,
            DynamicSchedulingJob.ScheduleId,
            DynamicSchedulingJob.PlanSummary
        ).join(
            DynamicSchedulingJob,
            SimulationPlanningJob.ScheduleId == DynamicSchedulingJob.ScheduleId
        )

        results = db.execute(statement).all()

        print(f"\n{'Key Value':<20} | {'Remark':<30} | {'Schedule Id':<20} | {'Plan Summary':<30}")
        print("-" * 110)
        
        if not results:
            print("No matching records found.")
            # Also check SimulationPlanningJob content just in case join failed but data exists
            print("\nChecking SimulationPlanningJob raw data (first 5)...")
            try:
                raw_stm = select(SimulationPlanningJob).limit(5)
                raw_res = db.execute(raw_stm).scalars().all()
                if not raw_res:
                     print("SimulationPlanningJob table is empty.")
                for r in raw_res:
                    print(f"ID: {r.id}, Key: {r.key_value}, SchID: {r.ScheduleId}")
            except Exception as e:
                print(f"Error checking raw data: {e}")
            return

        for row in results:
            key_val = str(row.key_value) if row.key_value else ""
            rem = str(row.remark) if row.remark else ""
            sch_id = str(row.ScheduleId) if row.ScheduleId else ""
            summary = str(row.PlanSummary)[:30] if row.PlanSummary else "" # Truncate summary
            
            print(f"{key_val:<20} | {rem:<30} | {sch_id:<20} | {summary:<30}")

    except Exception as e:
        print(f"Error executing query: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_join()
