"""
OmniGuard Database Service Layer
Supports dual-mode operation:
1. Production: Supabase Managed PostgreSQL with Row-Level Security
2. Demo/Offline Mode: High-fidelity in-memory state for instant out-of-the-box operation
Uses strict RFC 4122 UUIDs for all entity primary and foreign keys.
"""

from datetime import datetime, timezone
import os
from typing import Any, Dict, List, Optional
import uuid

from utils.mock_data import (
    DEMO_USER_ID,
    DEFAULT_ACCOUNTS,
    DEFAULT_GOALS,
    DEFAULT_PROFILE,
    generate_seed_transactions,
)

try:
    from supabase import Client, create_client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None
    create_client = None


class DatabaseService:
    def __init__(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None):
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_KEY")
        self.client: Optional[Any] = None
        self.is_connected: bool = False
        self.connection_error: Optional[str] = None
        self.last_db_status: str = "In-Memory Store Active"
        self.last_error: Optional[str] = None

        # In-memory storage for Demo / Offline Fallback mode
        self._memory_profiles: Dict[str, Dict[str, Any]] = {
            DEMO_USER_ID: dict(DEFAULT_PROFILE)
        }
        self._memory_accounts: List[Dict[str, Any]] = [dict(a) for a in DEFAULT_ACCOUNTS]
        self._memory_goals: List[Dict[str, Any]] = [dict(g) for g in DEFAULT_GOALS]
        self._memory_transactions: List[Dict[str, Any]] = generate_seed_transactions()
        self._memory_fraud_assessments: Dict[str, Dict[str, Any]] = {}
        self._memory_advisory_sessions: List[Dict[str, Any]] = []

        # Auto-assess demo seed transactions
        self._preseed_demo_assessments()

        # Attempt Supabase connection if credentials exist
        self._init_supabase()

    def _init_supabase(self):
        if not SUPABASE_AVAILABLE:
            self.connection_error = "supabase-py package is not installed."
            self.last_db_status = "In-Memory (supabase package missing)"
            return

        if not self.supabase_url or not self.supabase_key or "your-project" in self.supabase_url:
            self.is_connected = False
            self.last_db_status = "In-Memory Store (Supabase credentials not configured)"
            return

        try:
            self.client = create_client(self.supabase_url, self.supabase_key)
            # Lightweight health check
            res = self.client.table("profiles").select("id").limit(1).execute()
            self.is_connected = True
            self.connection_error = None
            self.last_db_status = "Supabase PostgreSQL Connected"

            # Auto-ensure demo profile exists in Supabase
            self._ensure_supabase_profile_exists()
        except Exception as e:
            self.is_connected = False
            self.connection_error = f"Supabase connection notice: {str(e)}"
            self.last_db_status = f"In-Memory Fallback ({str(e)[:45]}...)"
            self.last_error = str(e)

    def _ensure_supabase_profile_exists(self):
        """Ensures the demo user exists in Supabase so Foreign Key constraints succeed."""
        if not self.is_connected or not self.client:
            return
        try:
            check = self.client.table("profiles").select("id").eq("id", DEMO_USER_ID).execute()
            if not check.data:
                self.client.table("profiles").insert(DEFAULT_PROFILE).execute()
                for acc in DEFAULT_ACCOUNTS:
                    self.client.table("accounts").insert(acc).execute()
                for goal in DEFAULT_GOALS:
                    self.client.table("financial_goals").insert(goal).execute()
        except Exception as e:
            self.last_error = f"Auto-seed check: {str(e)}"

    def sync_seed_data_to_supabase(self) -> Dict[str, Any]:
        """Manually synchronizes all local seed data and transactions to the connected Supabase instance."""
        if not self.is_connected or not self.client:
            return {"success": False, "message": "Supabase is not connected."}

        try:
            self._ensure_supabase_profile_exists()
            synced_txs = 0
            for tx in self._memory_transactions[:20]:
                payload = {
                    "id": tx["id"],
                    "user_id": tx["user_id"],
                    "account_id": tx.get("account_id"),
                    "amount": float(tx["amount"]),
                    "currency": tx.get("currency", "USD"),
                    "merchant_name": tx["merchant_name"],
                    "category": tx.get("category", "General"),
                    "transaction_time": tx["transaction_time"],
                    "location_city": tx.get("location_city", "Unknown"),
                    "location_country": tx.get("location_country", "US"),
                    "device_ip": tx.get("device_ip", "127.0.0.1"),
                    "channel": tx.get("channel", "ONLINE"),
                }
                self.client.table("transactions").upsert(payload).execute()
                synced_txs += 1
            return {"success": True, "message": f"Successfully synchronized {synced_txs} transactions to Supabase!"}
        except Exception as e:
            return {"success": False, "message": f"Sync failed: {str(e)}"}

    def _preseed_demo_assessments(self):
        for tx in self._memory_transactions:
            tx_id = tx["id"]
            if tx.get("is_fraud_sample"):
                risk = 88 if "wire" in str(tx.get("category", "")).lower() else (94 if "harrods" in str(tx.get("merchant_name", "")).lower() else 82)
                level = "HIGH" if risk < 90 else "CRITICAL"
                indicators = ["Impossible Geo-Velocity", "High Dollar Amount"] if "harrods" in str(tx.get("merchant_name", "")).lower() else (
                    ["Offshore High-Risk Remittance", "Volume Anomaly"] if "wire" in str(tx.get("category", "")).lower() else
                    ["Rapid ATM Velocity Spike", "Card Skim Signature"]
                )
                self._memory_fraud_assessments[tx_id] = {
                    "id": str(uuid.uuid4()),
                    "transaction_id": tx_id,
                    "risk_score": risk,
                    "risk_level": level,
                    "anomaly_detected": True,
                    "triggered_indicators": indicators,
                    "ai_explanation": tx.get("expected_anomaly", "Anomalous transaction velocity detected."),
                    "recommended_action": "BLOCK" if risk >= 90 else "FLAG_FOR_REVIEW",
                    "confidence_score": 0.94,
                    "model_version": "gemini-3-flash",
                    "resolution_status": "PENDING",
                    "evaluated_at": tx["transaction_time"],
                }
            else:
                self._memory_fraud_assessments[tx_id] = {
                    "id": str(uuid.uuid4()),
                    "transaction_id": tx_id,
                    "risk_score": 8,
                    "risk_level": "LOW",
                    "anomaly_detected": False,
                    "triggered_indicators": [],
                    "ai_explanation": "Transaction conforms to verified merchant category and spending cadence.",
                    "recommended_action": "APPROVE",
                    "confidence_score": 0.98,
                    "model_version": "gemini-3-flash",
                    "resolution_status": "RESOLVED",
                    "evaluated_at": tx["transaction_time"],
                }

    # =========================================================================
    # PROFILES & ACCOUNTS
    # =========================================================================

    def get_profile(self, user_id: str = DEMO_USER_ID) -> Dict[str, Any]:
        if self.is_connected and self.client:
            try:
                res = self.client.table("profiles").select("*").eq("id", user_id).limit(1).execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                self.last_error = str(e)
        return self._memory_profiles.get(user_id, DEFAULT_PROFILE)

    def get_accounts(self, user_id: str = DEMO_USER_ID) -> List[Dict[str, Any]]:
        if self.is_connected and self.client:
            try:
                res = self.client.table("accounts").select("*").eq("user_id", user_id).execute()
                if res.data:
                    return res.data
            except Exception as e:
                self.last_error = str(e)
        return [a for a in self._memory_accounts if a["user_id"] == user_id]

    # =========================================================================
    # TRANSACTIONS & ASSESSMENTS
    # =========================================================================

    def get_transactions(
        self,
        user_id: str = DEMO_USER_ID,
        limit: int = 100,
        only_anomalies: bool = False
    ) -> List[Dict[str, Any]]:
        results = []
        if self.is_connected and self.client:
            try:
                q = self.client.table("transactions").select("*, fraud_assessments(*)").eq("user_id", user_id).order("transaction_time", desc=True).limit(limit)
                res = q.execute()
                if res.data:
                    for row in res.data:
                        fa_list = row.get("fraud_assessments") or []
                        fa = fa_list[0] if isinstance(fa_list, list) and fa_list else fa_list
                        row["fraud_assessment"] = fa
                        if only_anomalies and fa and not fa.get("anomaly_detected"):
                            continue
                        results.append(row)
                    if results:
                        return results
            except Exception as e:
                self.last_error = str(e)

        # In-Memory Mode
        for tx in self._memory_transactions:
            if tx.get("user_id") == user_id:
                tx_copy = dict(tx)
                fa = self._memory_fraud_assessments.get(tx["id"])
                tx_copy["fraud_assessment"] = fa
                if only_anomalies and fa and not fa.get("anomaly_detected"):
                    continue
                results.append(tx_copy)
                if len(results) >= limit:
                    break
        return results

    def add_transaction(self, tx: Dict[str, Any]) -> str:
        # Guarantee valid RFC 4122 UUID for primary key
        if "id" not in tx or not self._is_valid_uuid(tx["id"]):
            tx["id"] = str(uuid.uuid4())
        if "transaction_time" not in tx:
            tx["transaction_time"] = datetime.now(timezone.utc).isoformat()
        if "user_id" not in tx:
            tx["user_id"] = DEMO_USER_ID

        if self.is_connected and self.client:
            try:
                db_payload = {
                    "id": tx["id"],
                    "user_id": tx["user_id"],
                    "account_id": tx.get("account_id") if self._is_valid_uuid(tx.get("account_id")) else None,
                    "amount": float(tx["amount"]),
                    "currency": tx.get("currency", "USD"),
                    "merchant_name": tx["merchant_name"],
                    "category": tx.get("category", "General"),
                    "transaction_time": tx["transaction_time"],
                    "location_city": tx.get("location_city", "Unknown"),
                    "location_country": tx.get("location_country", "US"),
                    "device_ip": tx.get("device_ip", "127.0.0.1"),
                    "channel": tx.get("channel", "ONLINE"),
                }
                self.client.table("transactions").insert(db_payload).execute()
            except Exception as e:
                self.last_error = f"Supabase insert transaction: {str(e)}"

        # Always update memory for immediate reactivity
        self._memory_transactions.insert(0, tx)
        return tx["id"]

    def record_fraud_assessment(self, assessment: Dict[str, Any]) -> str:
        tx_id = assessment["transaction_id"]
        if "id" not in assessment or not self._is_valid_uuid(assessment["id"]):
            assessment["id"] = str(uuid.uuid4())
        if "evaluated_at" not in assessment:
            assessment["evaluated_at"] = datetime.now(timezone.utc).isoformat()

        if self.is_connected and self.client:
            try:
                db_payload = {
                    "id": assessment["id"],
                    "transaction_id": tx_id,
                    "risk_score": int(assessment["risk_score"]),
                    "risk_level": assessment["risk_level"],
                    "anomaly_detected": bool(assessment["anomaly_detected"]),
                    "triggered_indicators": assessment.get("triggered_indicators", []),
                    "ai_explanation": assessment["ai_explanation"],
                    "recommended_action": assessment["recommended_action"],
                    "confidence_score": float(assessment.get("confidence_score", 0.95)),
                    "model_version": assessment.get("model_version", "gemini-3-flash"),
                    "resolution_status": assessment.get("resolution_status", "PENDING"),
                    "evaluated_at": assessment["evaluated_at"],
                }
                self.client.table("fraud_assessments").upsert(db_payload).execute()
            except Exception as e:
                self.last_error = f"Supabase insert assessment: {str(e)}"

        self._memory_fraud_assessments[tx_id] = assessment
        return assessment["id"]

    def update_resolution_status(self, transaction_id: str, new_status: str) -> bool:
        if self.is_connected and self.client:
            try:
                self.client.table("fraud_assessments").update(
                    {"resolution_status": new_status}
                ).eq("transaction_id", transaction_id).execute()
            except Exception as e:
                self.last_error = f"Update resolution: {str(e)}"

        if transaction_id in self._memory_fraud_assessments:
            self._memory_fraud_assessments[transaction_id]["resolution_status"] = new_status
            return True
        return False

    # =========================================================================
    # FINANCIAL GOALS & ADVISORY
    # =========================================================================

    def get_financial_goals(self, user_id: str = DEMO_USER_ID) -> List[Dict[str, Any]]:
        if self.is_connected and self.client:
            try:
                res = self.client.table("financial_goals").select("*").eq("user_id", user_id).execute()
                if res.data:
                    return res.data
            except Exception as e:
                self.last_error = str(e)
        return [g for g in self._memory_goals if g["user_id"] == user_id]

    def add_financial_goal(self, goal: Dict[str, Any]) -> str:
        if "id" not in goal or not self._is_valid_uuid(goal["id"]):
            goal["id"] = str(uuid.uuid4())
        if "user_id" not in goal:
            goal["user_id"] = DEMO_USER_ID

        if self.is_connected and self.client:
            try:
                self.client.table("financial_goals").insert(goal).execute()
            except Exception as e:
                self.last_error = str(e)

        self._memory_goals.append(goal)
        return goal["id"]

    def save_advisory_session(self, user_id: str, health_score: int, payload: Dict[str, Any], chat_history: str = "") -> str:
        session_id = str(uuid.uuid4())
        record = {
            "id": session_id,
            "user_id": user_id,
            "health_score": health_score,
            "recommendations_payload": payload,
            "chat_transcript": chat_history,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        if self.is_connected and self.client:
            try:
                self.client.table("advisory_sessions").insert(record).execute()
            except Exception as e:
                self.last_error = str(e)

        self._memory_advisory_sessions.insert(0, record)
        return session_id

    def reset_to_seed_data(self):
        """Resets the in-memory database to original seed state."""
        self._memory_transactions = generate_seed_transactions()
        self._memory_fraud_assessments.clear()
        self._memory_goals = [dict(g) for g in DEFAULT_GOALS]
        self._preseed_demo_assessments()

    @staticmethod
    def _is_valid_uuid(val: Any) -> bool:
        if not val or not isinstance(val, str):
            return False
        try:
            uuid.UUID(val)
            return True
        except (ValueError, AttributeError):
            return False
