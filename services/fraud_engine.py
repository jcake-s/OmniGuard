"""
OmniGuard Fraud Sentinel Engine
Coordinates data sanitization, Gemini Flash risk scoring, database persistence,
and batch transaction triage.
"""

from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
import pandas as pd

from services.db_service import DatabaseService
from services.gemini_client import FraudEvaluationResult, GeminiService
from utils.masking import sanitize_transaction_payload


class FraudEngine:
    def __init__(self, db: DatabaseService, gemini: GeminiService):
        self.db = db
        self.gemini = gemini

    def process_single_transaction(
        self,
        tx_data: Dict[str, Any],
        user_id: str = "usr_demo_8829"
    ) -> Dict[str, Any]:
        """
        Takes raw transaction input, masks PII, scores with Gemini Flash,
        and saves both transaction and assessment into database.
        """
        # Ensure timestamp and user_id
        if "transaction_time" not in tx_data or not tx_data["transaction_time"]:
            tx_data["transaction_time"] = datetime.now(timezone.utc).isoformat()
        tx_data["user_id"] = user_id

        # 1. PII Masking
        sanitized_tx = sanitize_transaction_payload(tx_data)

        # 2. Gemini Inference with Schema Guarantee
        eval_result: FraudEvaluationResult = self.gemini.evaluate_transaction(sanitized_tx)

        # 3. Persist to Database
        tx_id = self.db.add_transaction(tx_data)

        assessment_record = {
            "transaction_id": tx_id,
            "risk_score": eval_result.risk_score,
            "risk_level": eval_result.risk_level,
            "anomaly_detected": eval_result.anomaly_detected,
            "triggered_indicators": eval_result.triggered_indicators,
            "ai_explanation": eval_result.ai_explanation,
            "recommended_action": eval_result.recommended_action,
            "confidence_score": eval_result.confidence_score,
            "model_version": self.gemini.model_name,
            "resolution_status": "CONFIRMED_FRAUD" if eval_result.risk_level == "CRITICAL" else "PENDING",
        }
        self.db.record_fraud_assessment(assessment_record)

        return {
            "transaction_id": tx_id,
            "transaction": tx_data,
            "evaluation": eval_result.model_dump(),
        }

    def process_batch_transactions(
        self,
        df: pd.DataFrame,
        user_id: str = "usr_demo_8829",
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        Processes a batch of transactions uploaded via CSV, respecting rate limits.
        """
        results = []
        total = len(df)

        for i, (_, row) in enumerate(df.iterrows()):
            if progress_callback:
                progress_callback(
                    (i + 1) / total,
                    f"Evaluating transaction {i+1} of {total}: {row.get('merchant_name', 'Merchant')} (${row.get('amount', 0):,.2f})"
                )

            tx_data = {
                "user_id": user_id,
                "amount": float(row.get("amount", 0.0)),
                "currency": str(row.get("currency", "USD")),
                "merchant_name": str(row.get("merchant_name", "Unknown")),
                "category": str(row.get("category", "General")),
                "transaction_time": str(row.get("transaction_time", datetime.now(timezone.utc).isoformat())),
                "location_city": str(row.get("location_city", "New York")),
                "location_country": str(row.get("location_country", "US")),
                "device_ip": str(row.get("device_ip", "127.0.0.1")),
                "channel": str(row.get("channel", "ONLINE")),
            }

            res = self.process_single_transaction(tx_data, user_id=user_id)
            results.append(res)

        return results

    def get_risk_summary(self, user_id: str = "usr_demo_8829") -> Dict[str, Any]:
        """Calculates aggregate risk metrics for top-level KPI dashboard."""
        txs = self.db.get_transactions(user_id=user_id, limit=200)
        total_tx = len(txs)
        total_amount = sum(float(t.get("amount", 0)) for t in txs)

        flagged_count = 0
        critical_count = 0
        total_risk_score = 0

        for t in txs:
            fa = t.get("fraud_assessment")
            if fa:
                score = fa.get("risk_score", 0)
                total_risk_score += score
                if fa.get("anomaly_detected") or score >= 50:
                    flagged_count += 1
                if fa.get("risk_level") == "CRITICAL":
                    critical_count += 1

        avg_risk = round(total_risk_score / max(total_tx, 1), 1)

        return {
            "total_transactions": total_tx,
            "total_volume_analyzed": total_amount,
            "flagged_alerts": flagged_count,
            "critical_threats": critical_count,
            "average_risk_score": avg_risk,
        }
