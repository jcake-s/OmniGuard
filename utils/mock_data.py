"""
OmniGuard Mock Data & Synthetic Financial Generator
Provides pre-seeded, realistic banking datasets with injected fraud anomalies
using RFC 4122 UUIDs for complete PostgreSQL/Supabase compatibility.
"""

from datetime import datetime, timedelta, timezone
import random
from typing import Any, Dict, List
import uuid

DEMO_USER_ID = "a0000000-0000-0000-0000-000000000001"
DEMO_ACCOUNT_CHECKING = "a0000000-0000-0000-0000-000000000101"
DEMO_ACCOUNT_SAVINGS = "a0000000-0000-0000-0000-000000000102"
DEMO_ACCOUNT_CREDIT = "a0000000-0000-0000-0000-000000000103"

DEFAULT_PROFILE = {
    "id": DEMO_USER_ID,
    "email": "alex.mercer@fintech-demo.io",
    "full_name": "Alex Mercer",
    "risk_tolerance": "MODERATE",
    "monthly_income": 6800.00,
    "created_at": (datetime.now(timezone.utc) - timedelta(days=90)).isoformat(),
}

DEFAULT_ACCOUNTS = [
    {
        "id": DEMO_ACCOUNT_CHECKING,
        "user_id": DEMO_USER_ID,
        "account_number_mask": "****-****-****-4821",
        "account_type": "CHECKING",
        "current_balance": 4250.75,
        "currency": "USD",
    },
    {
        "id": DEMO_ACCOUNT_SAVINGS,
        "user_id": DEMO_USER_ID,
        "account_number_mask": "****-****-****-9104",
        "account_type": "SAVINGS",
        "current_balance": 18450.00,
        "currency": "USD",
    },
    {
        "id": DEMO_ACCOUNT_CREDIT,
        "user_id": DEMO_USER_ID,
        "account_number_mask": "****-****-****-7319",
        "account_type": "CREDIT_CARD",
        "current_balance": 1120.40,
        "currency": "USD",
    },
]

DEFAULT_GOALS = [
    {
        "id": "a0000000-0000-0000-0000-000000000201",
        "user_id": DEMO_USER_ID,
        "goal_name": "6-Month Emergency Reserve",
        "target_amount": 20000.00,
        "current_amount": 18450.00,
        "target_date": "2026-12-31",
        "category": "EMERGENCY_FUND",
    },
    {
        "id": "a0000000-0000-0000-0000-000000000202",
        "user_id": DEMO_USER_ID,
        "goal_name": "Japan Travel & Leisure",
        "target_amount": 4500.00,
        "current_amount": 1750.00,
        "target_date": "2027-04-15",
        "category": "VACATION",
    },
]


def generate_seed_transactions() -> List[Dict[str, Any]]:
    """
    Generates a realistic 30-day baseline transaction ledger
    interspersed with 3 classic fraud attack vectors.
    All transaction IDs are valid UUIDs for clean DB serialization.
    """
    now = datetime.now(timezone.utc)
    base_txs: List[Dict[str, Any]] = []

    routine_merchants = [
        ("Whole Foods Market", "Groceries", 85.40, 142.10, "New York", "US", "POS_CHIP"),
        ("Trader Joe's", "Groceries", 45.20, 95.80, "New York", "US", "POS_CHIP"),
        ("Blue Bottle Coffee", "Dining", 6.50, 14.50, "New York", "US", "POS_CHIP"),
        ("Uber Technologies", "Transport", 18.25, 42.00, "New York", "US", "ONLINE"),
        ("Con Edison Utility", "Utilities", 115.00, 160.00, "New York", "US", "ONLINE"),
        ("Netflix Streaming", "Entertainment", 22.99, 22.99, "Los Gatos", "US", "ONLINE"),
        ("Spotify Premium", "Entertainment", 11.99, 11.99, "Stockholm", "SE", "ONLINE"),
        ("Equinox Fitness", "Health & Wellness", 280.00, 280.00, "New York", "US", "ONLINE"),
        ("Sweetgreen Midtown", "Dining", 16.50, 23.75, "New York", "US", "POS_CHIP"),
        ("Amazon.com", "Shopping", 32.10, 185.00, "Seattle", "US", "ONLINE"),
    ]

    for day_offset in range(28, 0, -1):
        tx_day = now - timedelta(days=day_offset)
        daily_count = random.randint(1, 3)
        for _ in range(daily_count):
            m_name, cat, min_amt, max_amt, city, country, channel = random.choice(routine_merchants)
            amt = round(random.uniform(min_amt, max_amt), 2)
            tx_time = tx_day.replace(
                hour=random.randint(8, 21),
                minute=random.randint(0, 59),
                second=random.randint(0, 59)
            )
            base_txs.append({
                "id": f"b0000000-0000-0000-0000-{len(base_txs)+1:012d}",
                "user_id": DEMO_USER_ID,
                "account_id": DEMO_ACCOUNT_CHECKING if cat in ["Groceries", "Utilities"] else DEMO_ACCOUNT_CREDIT,
                "amount": amt,
                "currency": "USD",
                "merchant_name": m_name,
                "category": cat,
                "transaction_time": tx_time.isoformat(),
                "location_city": city,
                "location_country": country,
                "device_ip": "72.229.28.185",
                "channel": channel,
                "is_fraud_sample": False,
            })

    # Injected Fraud Case 1: Geolocation Mismatch / Impossible Travel
    t1 = now - timedelta(days=4, hours=6)
    base_txs.append({
        "id": "c0000000-0000-0000-0000-000000000001",
        "user_id": DEMO_USER_ID,
        "account_id": DEMO_ACCOUNT_CREDIT,
        "amount": 18.50,
        "currency": "USD",
        "merchant_name": "Joe & The Juice Midtown",
        "category": "Dining",
        "transaction_time": t1.isoformat(),
        "location_city": "New York",
        "location_country": "US",
        "device_ip": "72.229.28.185",
        "channel": "POS_CHIP",
        "is_fraud_sample": False,
    })
    base_txs.append({
        "id": "c0000000-0000-0000-0000-000000000002",
        "user_id": DEMO_USER_ID,
        "account_id": DEMO_ACCOUNT_CREDIT,
        "amount": 1840.00,
        "currency": "USD",
        "merchant_name": "Harrods Luxury Dept",
        "category": "Shopping",
        "transaction_time": (t1 + timedelta(minutes=25)).isoformat(),
        "location_city": "London",
        "location_country": "GB",
        "device_ip": "185.220.101.44",
        "channel": "POS_SWIPE",
        "is_fraud_sample": True,
        "expected_anomaly": "Impossible travel time from New York to London (25 min difference), magnetic stripe swipe fallback.",
    })

    # Injected Fraud Case 2: Sudden High-Ticket Wire to High-Risk Jurisdiction
    t2 = now - timedelta(days=2, hours=3)
    base_txs.append({
        "id": "c0000000-0000-0000-0000-000000000003",
        "user_id": DEMO_USER_ID,
        "account_id": DEMO_ACCOUNT_CHECKING,
        "amount": 7950.00,
        "currency": "USD",
        "merchant_name": "BitEx OTC Global Remittance",
        "category": "Wire Transfer",
        "transaction_time": t2.isoformat(),
        "location_city": "Victoria",
        "location_country": "SC",
        "device_ip": "45.154.255.89",
        "channel": "WIRE_TRANSFER",
        "is_fraud_sample": True,
        "expected_anomaly": "Unprecedented high-dollar outbound wire to an offshore crypto exchange; 180% above standard monthly balance velocity.",
    })

    # Injected Fraud Case 3: ATM Velocity Spike
    t3 = now - timedelta(hours=14)
    for idx, (amt, delay_min) in enumerate([(20.00, 0), (500.00, 2), (800.00, 4), (800.00, 6)]):
        base_txs.append({
            "id": f"c0000000-0000-0000-0000-00000000001{idx+1}",
            "user_id": DEMO_USER_ID,
            "account_id": DEMO_ACCOUNT_CHECKING,
            "amount": amt,
            "currency": "USD",
            "merchant_name": "ATM NCR-CashExpress #402",
            "category": "ATM Withdrawal",
            "transaction_time": (t3 + timedelta(minutes=delay_min)).isoformat(),
            "location_city": "Miami",
            "location_country": "US",
            "device_ip": "104.28.19.112",
            "channel": "ATM_WITHDRAWAL",
            "is_fraud_sample": True if idx > 0 else False,
            "expected_anomaly": "Rapid successive ATM withdrawal attempts in quick succession (card skimming / cloning signature).",
        })

    base_txs.sort(key=lambda x: x["transaction_time"], reverse=True)
    return base_txs


def get_demo_csv_string() -> str:
    """Returns a ready-to-download demo CSV file for testing batch upload."""
    txs = generate_seed_transactions()[:15]
    lines = ["amount,currency,merchant_name,category,transaction_time,location_city,location_country,device_ip,channel"]
    for t in txs:
        lines.append(
            f"{t['amount']},{t['currency']},\"{t['merchant_name']}\",{t['category']},"
            f"{t['transaction_time']},{t['location_city']},{t['location_country']},{t['device_ip']},{t['channel']}"
        )
    return "\n".join(lines)
