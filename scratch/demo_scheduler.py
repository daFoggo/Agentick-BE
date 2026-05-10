import asyncio
import sys
import os

# Adjust python path to allow root imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.dependencies import get_database
from app.services.agent_outreach_service import AgentOutreachService
from app.services.testing_service import TestingService

async def main():
    print("\n>>> Starting Agentick Agent Scheduler Emergency Override Controller...")
    print("=" * 60)
    
    db_conn = get_database()
    
    with db_conn.session() as db:
        # 1. Run Morning Scan
        print("\n[STEP 1] Triggering Instant MORNING SCAN (Risk Analysis) for all tasks...")
        try:
            results = await TestingService.trigger_morning_scan_now(db)
            print(f"SUCCESS: Morning scan complete. Processed tasks: {len(results)}")
            for r in results[:3]: # Show first 3
                 print(f"  - Task {str(r.get('task_id'))[:8]}... Result: {r.get('risk_score', 'Error')}")
        except Exception as e:
            print(f"ERROR in Morning Scan: {e}")

        # 2. Run Agent Outreach
        print("\n[STEP 2] Triggering Instant AGENT OUTREACH (Data Gap & Stale Analysis)...")
        try:
            outreach_service = AgentOutreachService(db=db)
            outreaches = await outreach_service.run_outreach_cycle()
            print(f"SUCCESS: Outreach cycle complete. personalized emails sent: {len(outreaches)}")
            for o in outreaches:
                print(f"  - Sent to {o['email']} because of '{o['outreach_type']}' condition.")
        except Exception as e:
            print(f"ERROR in Outreach: {e}")

        # 3. Run Evening Summary
        print("\n[STEP 3] Triggering Instant EVENING SUMMARY dispatch...")
        try:
            reports = await TestingService.trigger_evening_summary_now(db)
            print(f"SUCCESS: Evening Summary report loop complete. Dispatches: {len(reports)}")
            for rep in reports:
                print(f"  - Project {str(rep['project_id'])[:8]} Status: {rep['status']}")
        except Exception as e:
             print(f"ERROR in Evening Summary: {e}")
        
    print("\n>>> DEMO OVERRIDE COMPLETED SUCCESSFULLY!")
    print("Check your system logs and configured email addresses to see notifications.")

if __name__ == "__main__":
    asyncio.run(main())
