"""
Star Hound Tracker – Main CLI
"""

from python.db import init_db
from python.users import prompt_create_user, prompt_update_user, get_user
from python.jobs import prompt_add_job, list_jobs
from python.applications import prompt_add_application, list_applications
from python.reminders import print_followup_report, prompt_complete_followup
from python.backup import backup_all_tables


def show_main_menu():
    print("\n" + "=" * 40)
    print("       STAR HOUND TRACKER")
    print("=" * 40)
    print("1. User profile")
    print("2. Add job")
    print("3. List top jobs")
    print("4. Add application")
    print("5. List active applications")
    print("6. Follow-up reminders")
    print("7. Complete a follow-up")
    print("8. Save Data")
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
            apps = list_applications()
            print("\n=== Active Applications ===")
            if not apps:
                print("No active applications.")
            for app in apps:
                print(f"{app['status']:18} | {app['title']} @ {app['company']}")

        elif choice == "6":
            print_followup_report(days_ahead=10)

        elif choice == "7":
            prompt_complete_followup()

        elif choice == "8": 
            backup_all_tables() 

        elif choice == "0":
            print("\nGood luck with the hunt! 🐶")
            break

        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()