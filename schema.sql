-- =====================================================================
-- OMNIGUARD COMPLETE DATABASE SCHEMA (SUPABASE POSTGRESQL)
-- Run this script in your Supabase Project -> SQL Editor -> New Query
-- =====================================================================

-- 1. Enable UUID Extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. User Profiles Table
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    risk_tolerance TEXT DEFAULT 'MODERATE' CHECK (risk_tolerance IN ('CONSERVATIVE', 'MODERATE', 'AGGRESSIVE')),
    monthly_income NUMERIC(12, 2) DEFAULT 0.00,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Financial Accounts Table
CREATE TABLE IF NOT EXISTS public.accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    account_number_mask TEXT NOT NULL,
    account_type TEXT NOT NULL CHECK (account_type IN ('CHECKING', 'SAVINGS', 'CREDIT_CARD', 'INVESTMENT')),
    current_balance NUMERIC(14, 2) DEFAULT 0.00,
    currency VARCHAR(3) DEFAULT 'USD',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Transactions Table (Core Financial Ledger)
CREATE TABLE IF NOT EXISTS public.transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    account_id UUID REFERENCES public.accounts(id) ON DELETE SET NULL,
    amount NUMERIC(12, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    merchant_name TEXT NOT NULL,
    category TEXT NOT NULL,
    transaction_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    location_city TEXT DEFAULT 'Unknown',
    location_country TEXT DEFAULT 'US',
    device_ip TEXT DEFAULT '127.0.0.1',
    channel TEXT DEFAULT 'ONLINE' CHECK (channel IN ('POS_SWIPE', 'POS_CHIP', 'ONLINE', 'ATM_WITHDRAWAL', 'WIRE_TRANSFER')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Fraud Assessments Table (AI Risk Evaluations)
CREATE TABLE IF NOT EXISTS public.fraud_assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_id UUID NOT NULL UNIQUE REFERENCES public.transactions(id) ON DELETE CASCADE,
    risk_score INT NOT NULL CHECK (risk_score BETWEEN 0 AND 100),
    risk_level TEXT NOT NULL CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    anomaly_detected BOOLEAN NOT NULL DEFAULT FALSE,
    triggered_indicators TEXT[] DEFAULT '{}',
    ai_explanation TEXT NOT NULL,
    recommended_action TEXT NOT NULL CHECK (recommended_action IN ('APPROVE', 'FLAG_FOR_REVIEW', 'BLOCK', 'REQUIRE_2FA')),
    confidence_score NUMERIC(4, 3) DEFAULT 0.950,
    model_version TEXT DEFAULT 'gemini-3-flash',
    resolution_status TEXT DEFAULT 'PENDING' CHECK (resolution_status IN ('PENDING', 'CONFIRMED_FRAUD', 'FALSE_POSITIVE', 'RESOLVED')),
    evaluated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. Financial Goals Table (Savings & Budgets)
CREATE TABLE IF NOT EXISTS public.financial_goals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    goal_name TEXT NOT NULL,
    target_amount NUMERIC(12, 2) NOT NULL,
    current_amount NUMERIC(12, 2) DEFAULT 0.00,
    target_date DATE NOT NULL,
    category TEXT DEFAULT 'SAVINGS',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. Advisory Sessions Table (AI Recommendations Log)
CREATE TABLE IF NOT EXISTS public.advisory_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    health_score INT NOT NULL CHECK (health_score BETWEEN 0 AND 100),
    recommendations_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    chat_transcript TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================================
-- PERFORMANCE INDEXES
-- =====================================================================
CREATE INDEX IF NOT EXISTS idx_transactions_user_time ON public.transactions(user_id, transaction_time DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_category ON public.transactions(category);
CREATE INDEX IF NOT EXISTS idx_fraud_assessments_risk ON public.fraud_assessments(risk_score DESC, risk_level);
CREATE INDEX IF NOT EXISTS idx_fraud_assessments_status ON public.fraud_assessments(resolution_status);

-- =====================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- Enables anonymous client access for the Streamlit demo application
-- =====================================================================
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.fraud_assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.financial_goals ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.advisory_sessions ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if re-running
DROP POLICY IF EXISTS "Allow anon read profiles" ON public.profiles;
DROP POLICY IF EXISTS "Allow anon insert profiles" ON public.profiles;
DROP POLICY IF EXISTS "Allow anon read accounts" ON public.accounts;
DROP POLICY IF EXISTS "Allow anon insert accounts" ON public.accounts;
DROP POLICY IF EXISTS "Allow anon read transactions" ON public.transactions;
DROP POLICY IF EXISTS "Allow anon insert transactions" ON public.transactions;
DROP POLICY IF EXISTS "Allow anon read fraud_assessments" ON public.fraud_assessments;
DROP POLICY IF EXISTS "Allow anon insert fraud_assessments" ON public.fraud_assessments;
DROP POLICY IF EXISTS "Allow anon update fraud_assessments" ON public.fraud_assessments;
DROP POLICY IF EXISTS "Allow anon read financial_goals" ON public.financial_goals;
DROP POLICY IF EXISTS "Allow anon insert financial_goals" ON public.financial_goals;
DROP POLICY IF EXISTS "Allow anon read advisory_sessions" ON public.advisory_sessions;
DROP POLICY IF EXISTS "Allow anon insert advisory_sessions" ON public.advisory_sessions;

-- Policies for public anon key access
CREATE POLICY "Allow anon read profiles" ON public.profiles FOR SELECT USING (true);
CREATE POLICY "Allow anon insert profiles" ON public.profiles FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow anon read accounts" ON public.accounts FOR SELECT USING (true);
CREATE POLICY "Allow anon insert accounts" ON public.accounts FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow anon read transactions" ON public.transactions FOR SELECT USING (true);
CREATE POLICY "Allow anon insert transactions" ON public.transactions FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow anon read fraud_assessments" ON public.fraud_assessments FOR SELECT USING (true);
CREATE POLICY "Allow anon insert fraud_assessments" ON public.fraud_assessments FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow anon update fraud_assessments" ON public.fraud_assessments FOR UPDATE USING (true);

CREATE POLICY "Allow anon read financial_goals" ON public.financial_goals FOR SELECT USING (true);
CREATE POLICY "Allow anon insert financial_goals" ON public.financial_goals FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow anon read advisory_sessions" ON public.advisory_sessions FOR SELECT USING (true);
CREATE POLICY "Allow anon insert advisory_sessions" ON public.advisory_sessions FOR INSERT WITH CHECK (true);

-- =====================================================================
-- INITIAL SEED DATA (Demo User & Default Accounts)
-- =====================================================================
INSERT INTO public.profiles (id, email, full_name, risk_tolerance, monthly_income)
VALUES (
    'a0000000-0000-0000-0000-000000000001',
    'alex.mercer@fintech-demo.io',
    'Alex Mercer',
    'MODERATE',
    6800.00
)
ON CONFLICT (id) DO UPDATE SET full_name = EXCLUDED.full_name;

INSERT INTO public.accounts (id, user_id, account_number_mask, account_type, current_balance, currency)
VALUES 
    ('a0000000-0000-0000-0000-000000000101', 'a0000000-0000-0000-0000-000000000001', '****-****-****-4821', 'CHECKING', 4250.75, 'USD'),
    ('a0000000-0000-0000-0000-000000000102', 'a0000000-0000-0000-0000-000000000001', '****-****-****-9104', 'SAVINGS', 18450.00, 'USD'),
    ('a0000000-0000-0000-0000-000000000103', 'a0000000-0000-0000-0000-000000000001', '****-****-****-7319', 'CREDIT_CARD', 1120.40, 'USD')
ON CONFLICT (id) DO NOTHING;

INSERT INTO public.financial_goals (id, user_id, goal_name, target_amount, current_amount, target_date, category)
VALUES
    ('a0000000-0000-0000-0000-000000000201', 'a0000000-0000-0000-0000-000000000001', '6-Month Emergency Reserve', 20000.00, 18450.00, '2026-12-31', 'EMERGENCY_FUND'),
    ('a0000000-0000-0000-0000-000000000202', 'a0000000-0000-0000-0000-000000000001', 'Japan Travel & Leisure', 4500.00, 1750.00, '2027-04-15', 'VACATION')
ON CONFLICT (id) DO NOTHING;
