"""Seed N random realistic Indian expenses for a given user over the past M months."""

import random
import sys
from datetime import date, timedelta

from database.db import get_db

CATEGORIES = {
    "Food": {
        "weight": 5,
        "min": 50,
        "max": 800,
        "descriptions": [
            "Lunch at office canteen",
            "Chai and samosa at tapri",
            "Dinner at Haldiram's",
            "Groceries from D-Mart",
            "Breakfast at Indian Coffee House",
            "Swiggy order",
            "Zomato dinner",
            "Thali at local restaurant",
            "Mumbai street food",
            "Sunday biryani",
        ],
    },
    "Transport": {
        "weight": 4,
        "min": 20,
        "max": 500,
        "descriptions": [
            "Uber to airport",
            "Auto rickshaw ride",
            "Ola to office",
            "Rapido bike taxi",
            "Petrol refill",
            "Metro card recharge",
            "Train ticket to Pune",
            "BMTC bus pass",
        ],
    },
    "Bills": {
        "weight": 2,
        "min": 200,
        "max": 3000,
        "descriptions": [
            "Electricity bill (BSES)",
            "Airtel postpaid bill",
            "Jio Fiber broadband",
            "Tata Play DTH recharge",
            "Gas cylinder refill",
            "Water bill",
            "Housing society maintenance",
        ],
    },
    "Health": {
        "weight": 1,
        "min": 100,
        "max": 2000,
        "descriptions": [
            "Pharmacy - Apollo",
            "Doctor consultation",
            "Lab tests",
            "Dental checkup",
            "Gym monthly fee",
            "Yoga class",
        ],
    },
    "Entertainment": {
        "weight": 1,
        "min": 100,
        "max": 1500,
        "descriptions": [
            "PVR movie tickets",
            "BookMyShow concert",
            "Netflix subscription",
            "Spotify Premium",
            "Board game cafe",
            "Weekend getaway",
        ],
    },
    "Shopping": {
        "weight": 3,
        "min": 200,
        "max": 5000,
        "descriptions": [
            "Amazon order",
            "Flipkart sale purchase",
            "Myntra clothing",
            "New running shoes",
            "Laptop accessories",
            "Meesho order",
            "Decathlon sports gear",
        ],
    },
    "Other": {
        "weight": 2,
        "min": 50,
        "max": 1000,
        "descriptions": [
            "Gift for friend",
            "Donation to temple",
            "Haircut at salon",
            "Courier via DTDC",
            "Birthday cake from Monginis",
            "Mobile recharge",
        ],
    },
}


def weighted_category_choices():
    """Return a list of categories repeated by their weight for random.choice()."""
    pool = []
    for cat, meta in CATEGORIES.items():
        pool.extend([cat] * meta["weight"])
    return pool


def random_past_date(months):
    """Random date within the past `months` calendar months (inclusive of today)."""
    today = date.today()
    # Earliest day = first of (today.month - months + 1) — clamp year properly.
    year = today.year
    month = today.month - (months - 1)
    while month <= 0:
        month += 12
        year -= 1
    earliest = date(year, month, 1)
    span_days = (today - earliest).days
    return earliest + timedelta(days=random.randint(0, span_days))


def generate_expense():
    category = random.choice(weighted_category_choices())
    meta = CATEGORIES[category]
    amount = round(random.uniform(meta["min"], meta["max"]), 2)
    description = random.choice(meta["descriptions"])
    expense_date = random_past_date(MONTHS)
    return (USER_ID, amount, category, expense_date.isoformat(), description)


def main():
    conn = get_db()
    try:
        # Step 2: confirm user exists.
        user = conn.execute(
            "SELECT id FROM users WHERE id = ?", (USER_ID,)
        ).fetchone()
        if user is None:
            print(f"No user found with id {USER_ID}.")
            sys.exit(1)

        expenses = [generate_expense() for _ in range(COUNT)]

        # Single transaction: commit on success, rollback on any failure.
        try:
            conn.executemany(
                "INSERT INTO expenses "
                "(user_id, amount, category, date, description) "
                "VALUES (?, ?, ?, ?, ?)",
                expenses,
            )
            conn.commit()
        except Exception as exc:
            conn.rollback()
            print(f"Insert failed, rolled back: {exc}")
            sys.exit(1)

        # Date range from the data we just inserted.
        dates = sorted(e[3] for e in expenses)
        date_min, date_max = dates[0], dates[-1]

        print(f"Inserted {COUNT} expenses for user_id={USER_ID}.")
        print(f"Date range: {date_min}  to  {date_max}")
        print("Sample of 5 inserted records:")
        sample = random.sample(expenses, min(5, len(expenses)))
        for user_id, amount, category, d, desc in sample:
            print(f"  {d}  Rs.{amount:>7.2f}  {category:<14} {desc}")
    finally:
        conn.close()


if __name__ == "__main__":
    # Step 1: parse + validate args.
    if len(sys.argv) != 4:
        print("Usage: /seed-expenses <user_id> <count> <months>")
        print("Example: /seed-expenses 1 50 6")
        sys.exit(1)
    try:
        USER_ID = int(sys.argv[1])
        COUNT = int(sys.argv[2])
        MONTHS = int(sys.argv[3])
    except ValueError:
        print("Usage: /seed-expenses <user_id> <count> <months>")
        print("Example: /seed-expenses 1 50 6")
        sys.exit(1)
    main()
