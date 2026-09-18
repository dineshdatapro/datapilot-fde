"""Generate internally consistent demo datasets for DataPilot."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1] / "sample_data"

CITIES = [
    ("Hyderabad", "Telangana", "South"),
    ("Vijayawada", "Andhra Pradesh", "South"),
    ("Visakhapatnam", "Andhra Pradesh", "South"),
    ("Bengaluru", "Karnataka", "South"),
    ("Chennai", "Tamil Nadu", "South"),
    ("Mumbai", "Maharashtra", "West"),
    ("Pune", "Maharashtra", "West"),
    ("Delhi", "Delhi", "North"),
    ("Kolkata", "West Bengal", "East"),
]

PRODUCTS = [
    ("Cotton Kurta", "Apparel"),
    ("Silk Saree", "Apparel"),
    ("Denim Jacket", "Apparel"),
    ("Wireless Earbuds", "Electronics"),
    ("Smartwatch", "Electronics"),
    ("Desk Lamp", "Home"),
    ("Office Chair", "Home"),
    ("Stainless Bottle", "Home"),
    ("Yoga Mat", "Accessories"),
    ("Leather Wallet", "Accessories"),
    ("Notebook Set", "Accessories"),
    ("Coffee Beans", "Grocery"),
]

SEGMENTS = ["Consumer", "Corporate", "Home Office", "Small Business"]
FIRST = [
    "Aarav", "Diya", "Ishaan", "Meera", "Kabir", "Ananya", "Rohan", "Sara",
    "Vikram", "Nisha", "Arjun", "Priya", "Rahul", "Kavya", "Aditya", "Sneha",
]
LAST = [
    "Reddy", "Sharma", "Iyer", "Patel", "Khan", "Nair", "Gupta", "Das",
    "Mehta", "Joshi", "Rao", "Singh", "Banerjee", "Kapoor", "Pillai",
]


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(42)

    n_customers = 800
    city_idx = rng.integers(0, len(CITIES), n_customers)
    customers = pd.DataFrame(
        {
            "customer_id": [f"CUS{i:04d}" for i in range(1, n_customers + 1)],
            "customer_name": [
                f"{FIRST[i % len(FIRST)]} {LAST[(i * 3) % len(LAST)]}"
                for i in range(n_customers)
            ],
            "city": [CITIES[i][0] for i in city_idx],
            "state": [CITIES[i][1] for i in city_idx],
            "segment": rng.choice(SEGMENTS, n_customers, p=[0.45, 0.22, 0.18, 0.15]),
            "signup_date": pd.to_datetime("2022-01-01")
            + pd.to_timedelta(rng.integers(0, 700, n_customers), unit="D"),
        }
    )

    jan = _orders(rng, customers, month=1, n=2200, start_id=10000)
    feb = _orders(rng, customers, month=2, n=2400, start_id=20000)

    customers.to_csv(ROOT / "customers.csv", index=False)
    jan.to_csv(ROOT / "sales_january.csv", index=False)
    feb.to_excel(ROOT / "sales_february.xlsx", index=False, engine="openpyxl")
    print(f"Wrote {ROOT}")
    print(f"  customers: {len(customers)} rows")
    print(f"  sales_january: {len(jan)} rows")
    print(f"  sales_february: {len(feb)} rows")


def _orders(rng: np.random.Generator, customers: pd.DataFrame, month: int, n: int, start_id: int) -> pd.DataFrame:
    cust_ids = customers["customer_id"].tolist()
    # 90% of orders map to known customers so joins work; 10% are guests.
    chosen = rng.choice(cust_ids, n)
    guest_mask = rng.random(n) < 0.08
    for i, is_guest in enumerate(guest_mask):
        if is_guest:
            chosen[i] = f"GST{start_id + i}"

    lookup = customers.set_index("customer_id")
    city_map = {c[0]: c[2] for c in CITIES}

    prod_idx = rng.integers(0, len(PRODUCTS), n)
    qty = rng.integers(1, 8, n)
    unit = rng.integers(350, 8500, n)
    discount = np.round(rng.choice([0, 0.05, 0.1, 0.15, 0.2], n, p=[0.45, 0.25, 0.15, 0.1, 0.05]), 2)
    revenue = np.round(qty * unit * (1 - discount), 2)

    days = rng.integers(1, 29 if month == 2 else 32, n)
    dates = pd.to_datetime({"year": 2024, "month": month, "day": days})

    cities = []
    regions = []
    for cid in chosen:
        if cid in lookup.index:
            city = lookup.loc[cid, "city"]
        else:
            city = CITIES[int(rng.integers(0, len(CITIES)))][0]
        cities.append(city)
        regions.append(city_map[city])

    return pd.DataFrame(
        {
            "order_id": [f"ORD{start_id + i}" for i in range(n)],
            "order_date": dates.dt.strftime("%Y-%m-%d"),
            "customer_id": chosen,
            "product": [PRODUCTS[i][0] for i in prod_idx],
            "category": [PRODUCTS[i][1] for i in prod_idx],
            "region": regions,
            "city": cities,
            "quantity": qty,
            "revenue": revenue,
            "discount": discount,
        }
    )


if __name__ == "__main__":
    main()
