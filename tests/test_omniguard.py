"""
OmniGuard Unit & Integration Test Suite
Validates PII masking, Database Service, Gemini Client Fallbacks, and Fraud Engines.
"""

import unittest
from utils.masking import (
    mask_card_number,
    mask_ssn,
    mask_phone,
    mask_email,
    sanitize_transaction_payload,
)
from utils.mock_data import generate_seed_transactions, get_demo_csv_string
from services.db_service import DatabaseService
from services.gemini_client import GeminiService
from services.fraud_engine import FraudEngine
from services.advisory_engine import AdvisoryEngine


class TestOmniGuard(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseService()
        self.gemini = GeminiService(api_key=None, model_name="gemini-3-flash")
        self.fraud_engine = FraudEngine(db=self.db, gemini=self.gemini)
        self.advisory_engine = AdvisoryEngine(db=self.db, gemini=self.gemini)

    def test_pii_masking_card(self):
        raw = "Card charge on 4111-2222-3333-4821 approved"
        masked = mask_card_number(raw)
        self.assertIn("****-****-****-4821", masked)
        self.assertNotIn("4111-2222", masked)

    def test_pii_masking_ssn(self):
        raw = "User SSN is 123-45-6789"
        masked = mask_ssn(raw)
        self.assertEqual(masked, "User SSN is ***-**-6789")

    def test_pii_masking_phone_and_email(self):
        raw_email = "test.user@bankdomain.com"
        masked_email = mask_email(raw_email)
        self.assertTrue(masked_email.startswith("tes***@"))

        raw_phone = "Call (212) 555-1234"
        masked_phone = mask_phone(raw_phone)
        self.assertIn("(***) ***-1234", masked_phone)

    def test_sanitize_transaction_payload(self):
        payload = {
            "card_pan": "4111222233334821",
            "merchant": "Amazon.com",
            "amount": 120.50,
            "notes": "Charged to 4111-2222-3333-4821 for user 123-45-6789",
        }
        sanitized = sanitize_transaction_payload(payload)
        self.assertIn("****-****-****-4821", sanitized["notes"])
        self.assertIn("***-**-6789", sanitized["notes"])
        self.assertEqual(sanitized["amount"], 120.50)

    def test_seed_transactions_generator(self):
        txs = generate_seed_transactions()
        self.assertGreaterEqual(len(txs), 20)
        # Check presence of injected fraud samples
        fraud_samples = [t for t in txs if t.get("is_fraud_sample")]
        self.assertGreaterEqual(len(fraud_samples), 3)

        csv_str = get_demo_csv_string()
        self.assertIn("merchant_name", csv_str)
        self.assertIn("amount", csv_str)

    def test_db_service_operations(self):
        profile = self.db.get_profile()
        self.assertEqual(profile["id"], "usr_demo_8829")

        accounts = self.db.get_accounts()
        self.assertGreaterEqual(len(accounts), 2)

        tx_id = self.db.add_transaction({
            "merchant_name": "Test Cafe",
            "amount": 12.00,
            "category": "Dining",
        })
        self.assertTrue(tx_id.startswith("tx_"))

        # Verify retrieval
        txs = self.db.get_transactions(limit=10)
        self.assertGreaterEqual(len(txs), 1)

    def test_fraud_engine_evaluation(self):
        # Test clean transaction
        clean_tx = {
            "amount": 14.50,
            "merchant_name": "Joe Coffee",
            "category": "Dining",
            "channel": "POS_CHIP",
            "location_city": "New York",
            "location_country": "US",
        }
        res_clean = self.fraud_engine.process_single_transaction(clean_tx)
        eval_clean = res_clean["evaluation"]
        self.assertEqual(eval_clean["risk_level"], "LOW")
        self.assertEqual(eval_clean["recommended_action"], "APPROVE")
        self.assertFalse(eval_clean["anomaly_detected"])

        # Test high-risk offshore wire
        wire_tx = {
            "amount": 9500.00,
            "merchant_name": "Crypto OTC BitEx Remittance",
            "category": "Wire Transfer",
            "channel": "WIRE_TRANSFER",
            "location_city": "Victoria",
            "location_country": "SC",
        }
        res_wire = self.fraud_engine.process_single_transaction(wire_tx)
        eval_wire = res_wire["evaluation"]
        self.assertIn(eval_wire["risk_level"], ["HIGH", "CRITICAL"])
        self.assertTrue(eval_wire["anomaly_detected"])
        self.assertIn(eval_wire["recommended_action"], ["FLAG_FOR_REVIEW", "BLOCK"])

    def test_advisory_engine(self):
        eval_res = self.advisory_engine.get_full_financial_evaluation()
        self.assertGreaterEqual(eval_res.health_score, 0)
        self.assertLessEqual(eval_res.health_score, 100)
        self.assertGreaterEqual(len(eval_res.category_insights), 1)
        self.assertGreaterEqual(len(eval_res.actionable_steps), 2)

        chat_reply = self.advisory_engine.handle_copilot_chat(
            user_message="How can I save money on dining?",
            conversation_history=[]
        )
        self.assertIsInstance(chat_reply, str)
        self.assertGreater(len(chat_reply), 20)


if __name__ == "__main__":
    unittest.main()
