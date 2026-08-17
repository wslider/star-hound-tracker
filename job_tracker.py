import sys
from python.db import init_db


def main():
    print("=== Star Hound Tracker ===")
    print("Personal job-search tracker\n")

    init_db()          # creates data/jobs.db + tables if needed

    # Temporary simple flow while we build
    print("Database ready. Let the job hunting begin!")
    # TODO: user selection / creation
    # TODO: main menu loop

if __name__ == "__main__":
    main()