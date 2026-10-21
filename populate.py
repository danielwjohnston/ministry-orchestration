import os
import database

def populate():
    # Ensure correct DB
    os.environ["BODY_ORCH_DB"] = "body_orchestrator.db"
    
    # Update Org Identity
    database.update_organization(
        1,
        "Connection Christian Church", 
        "4241 Tanglewood Ln, Odessa, TX 79762", 
        "Admin / Church Office"
    )
    
    org = database.get_organization(1)
    org_id = org['id']
    
    # Add Ministries
    ministries = [
        ("Tutoring Ministry", "Provides academic support and mentoring to local students."),
        ("Summer Lunch Feeding Ministry", "Ensures children have access to meals during summer break."),
        ("West Texas Food Bank Support", "Partnership to distribute food to those experiencing food insecurity."),
        ("Crisis Center Support", "Support for the local Crisis Center and Women's Shelter."),
        ("Meals on Wheels", "Delivering meals to homebound seniors."),
        ("Non-Profit Hosting", "Hosts Big Brothers Big Sisters and Centers Counseling on campus.")
    ]
    for m in ministries:
        database.add_ministry(org_id, m[0], m[1])
        
    # Add Capabilities
    capabilities = [
        ("Facilities", "15,000 square feet of dedicated space for non-profit organizations."),
        ("Language", "Fully bilingual (English and Spanish) services and resources."),
        ("Community Network", "Established partnerships with major local non-profits (Food Bank, Crisis Center).")
    ]
    for c in capabilities:
        database.add_capability(org_id, c[0], c[1])
        
    # Add Needs
    needs = [
        ("Volunteers", "Need volunteers for the Summer Lunch Feeding Ministry and Tutoring programs."),
        ("Funding", "Ongoing financial support for facility maintenance to continue hosting non-profits for free or reduced cost."),
        ("Mentors", "Big Brothers Big Sisters is seeking more adult mentors from the congregation.")
    ]
    for n in needs:
        database.add_need(org_id, n[0], n[1])

if __name__ == "__main__":
    populate()
    print("Database populated successfully.")
