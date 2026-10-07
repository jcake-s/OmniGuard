"""
OmniGuard Wealth Advisory Engine
Performs financial ledger aggregation, calls Gemini Flash for holistic cash-flow
and budget optimization, and manages interactive copilot sessions.
"""

from typing import Any, Dict, List
import pandas as pd

from services.db_service import DatabaseService
from services.gemini_client import FinancialHealthEvaluation, GeminiService


class AdvisoryEngine:
    def __init__(self, db: DatabaseService, gemini: GeminiService):
        self.db = db
        self.gemini = gemini

    def get_full_financial_evaluation(self, user_id: str = "usr_demo_8829") -> FinancialHealthEvaluation:
        """Retrieves user financial state and requests structured guidance from Gemini Flash."""
        profile = self.db.get_profile(user_id=user_id)
        accounts = self.db.get_accounts(user_id=user_id)
        transactions = self.db.get_transactions(user_id=user_id, limit=100)
        goals = self.db.get_financial_goals(user_id=user_id)

        eval_res = self.gemini.generate_wealth_advisory(
            profile=profile,
            accounts=accounts,
            transactions=transactions,
            goals=goals,
        )

        # Persist evaluation record
        self.db.save_advisory_session(
            user_id=user_id,
            health_score=eval_res.health_score,
            payload=eval_res.model_dump(),
        )

        return eval_res

    def get_category_spending_df(self, user_id: str = "usr_demo_8829") -> pd.DataFrame:
        """Returns a formatted DataFrame of 30-day spending aggregated by category."""
        transactions = self.db.get_transactions(user_id=user_id, limit=150)
        records = []
        for t in transactions:
            if not t.get("is_fraud_sample"):
                records.append({
                    "category": t.get("category", "Uncategorized"),
                    "amount": float(t.get("amount", 0.0)),
                    "merchant": t.get("merchant_name", "Unknown"),
                })

        if not records:
            return pd.DataFrame(columns=["category", "amount", "merchant"])

        df = pd.DataFrame(records)
        grouped = df.groupby("category")["amount"].sum().reset_index()
        grouped = grouped.sort_values(by="amount", ascending=False)
        return grouped

    def get_goals_progress_df(self, user_id: str = "usr_demo_8829") -> pd.DataFrame:
        """Returns a DataFrame tracking current vs target amounts for all user goals."""
        goals = self.db.get_financial_goals(user_id=user_id)
        rows = []
        for g in goals:
            current = float(g.get("current_amount", 0.0))
            target = float(g.get("target_amount", 1.0))
            pct = min(100.0, round((current / max(target, 1.0)) * 100, 1))
            rows.append({
                "Goal": g.get("goal_name"),
                "Current ($)": current,
                "Target ($)": target,
                "Completion (%)": pct,
                "Target Date": g.get("target_date"),
                "Category": g.get("category"),
            })
        return pd.DataFrame(rows)

    def handle_copilot_chat(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        user_id: str = "usr_demo_8829"
    ) -> str:
        """Processes conversational inquiry with comprehensive user ledger context."""
        profile = self.db.get_profile(user_id=user_id)
        accounts = self.db.get_accounts(user_id=user_id)
        transactions = self.db.get_transactions(user_id=user_id, limit=30)
        goals = self.db.get_financial_goals(user_id=user_id)

        context_data = {
            "profile": profile,
            "total_liquid_balance": sum(float(a.get("current_balance", 0)) for a in accounts),
            "recent_transactions_count": len(transactions),
            "goals": [g.get("goal_name") for g in goals],
        }

        return self.gemini.ask_copilot(
            user_message=user_message,
            conversation_history=conversation_history,
            context_data=context_data,
        )
