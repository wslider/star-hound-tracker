"""
Star Hound Tracker – Main CLI
"""

from python.db import init_db
from python.users import prompt_create_user, prompt_update_user, get_user
from python.jobs import prompt_add_job, list_jobs
from python.applications import prompt_add_application, list_applications, prompt_update_application
from python.reminders import print_followup_report, prompt_complete_followup
from python.backup import backup_all_tables, backup_sample_data
from python.viz import generate_visualizations


def show_main_menu():
    print("\n" + "=" * 40)
    print("       STAR HOUND TRACKER")
    print("=" * 40)
    print("1. User profile")
    print("2. Add job")
    print("3. List top jobs")
    print("4. Add application")
    print("5. Update application")
    print("6. List active applications")
    print("7. Follow-up reminders")
    print("8. Complete a follow-up")
    print("9. Save Data")
    print("10. Generate Visualizations")
    print("11. Generate Complete Report")
    print("0. Exit")
    print("=" * 40)


def handle_user_profile():
    user = get_user(1)
    if user is None:
        print("\nNo user profile found. Let's create one.")
        prompt_create_user()
    else:
        print("\nCurrent profile:")
        for k, v in user.items():
            print(f"  {k}: {v}")
        print("\n1. Update profile")
        print("0. Back")
        choice = input("Choice: ").strip()
        if choice == "1":
            prompt_update_user()


def main():
    print("=== Star Hound Tracker ===")
    init_db()

    while True:
        show_main_menu()
        choice = input("\nEnter choice: ").strip()

        if choice == "1":
            handle_user_profile()

        elif choice == "2":
            prompt_add_job()

        elif choice == "3":
            jobs = list_jobs(limit=15)
            print("\n=== Top Jobs ===")
            if not jobs:
                print("No jobs yet.")
            for job in jobs:
                print(f"{job['job_score']:5.1f}  |  {job['title']} @ {job['company']}  ({job['job_id']})")

        elif choice == "4":
            prompt_add_application()

        elif choice == "5":
            prompt_update_application()

        elif choice == "6":
            apps = list_applications()
            print("\n=== Active Applications ===")
            if not apps:
                print("No active applications.")
            for app in apps:
                print(f"{app['status']:18} | {app['title']} @ {app['company']}")

        elif choice == "7":
            print_followup_report(days_ahead=10)

        elif choice == "8":
            prompt_complete_followup()

        elif choice == "9": 
            backup_all_tables()
            backup_sample_data()

        elif choice == "10":
            print("1. Real data charts")
            print("2. Sample data charts")
            sub = input("Choice: ").strip()
            if sub == "1":
                generate_visualizations(sample=False)
            else:
                generate_visualizations(sample=True)

        elif choice == "11":
            print("Report generation in development.")

        elif choice == "0":
            print("\nGood luck with the hunt! 🐶")
            break

        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()