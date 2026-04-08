"""
Run this script to populate demo data for Flux.
Usage: docker exec -it flux_backend python seed_demo.py
"""

import sys
import os
sys.path.insert(0, '/app')

from app.core.database import SessionLocal
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember, MemberRole
from app.models.repository import Repository
from app.models.branch import Branch
from app.models.prompt_version import PromptVersion
from app.models.eval import EvalSuite, EvalCase, EvalRun, EvalRunStatus, EvalType
from app.core.security import get_password_hash
import uuid
from datetime import datetime, timedelta


def seed():
    db = SessionLocal()
    try:
        # Check if demo already exists
        existing = db.query(User).filter(User.email == "demo@flux.dev").first()
        if existing:
            print("Demo data already exists. Skipping.")
            return

        print("Creating demo user...")
        demo_user = User(
            id=uuid.uuid4(),
            email="demo@flux.dev",
            hashed_password=get_password_hash("demo1234"),
            name="Demo User",
            created_at=datetime.utcnow() - timedelta(days=7),
        )
        db.add(demo_user)
        db.flush()

        print("Creating demo workspace...")
        workspace = Workspace(
            id=uuid.uuid4(),
            name="Customer Support AI",
            owner_id=demo_user.id,
            created_at=datetime.utcnow() - timedelta(days=7),
        )
        db.add(workspace)
        db.flush()

        member = WorkspaceMember(
            workspace_id=workspace.id,
            user_id=demo_user.id,
            role=MemberRole.owner,
        )
        db.add(member)

        print("Creating demo repository...")
        repo = Repository(
            id=uuid.uuid4(),
            workspace_id=workspace.id,
            name="support-response-prompt",
            description="Customer support response generator — versioned and evaluated",
            created_at=datetime.utcnow() - timedelta(days=7),
        )
        db.add(repo)
        db.flush()

        print("Creating branches...")
        main_branch = Branch(
            id=uuid.uuid4(),
            repository_id=repo.id,
            name="main",
            created_from_version_id=None,
            created_at=datetime.utcnow() - timedelta(days=7),
        )
        db.add(main_branch)
        db.flush()

        print("Creating prompt versions...")
        v1 = PromptVersion(
            id=uuid.uuid4(),
            branch_id=main_branch.id,
            prompt_text="You are a customer support agent. Answer the customer's question.",
            model_config={"model": "gpt-4o-mini", "temperature": 0.7, "max_tokens": 500, "system_message": None},
            commit_message="Initial prompt — basic support agent",
            author_id=demo_user.id,
            eval_score=None,
            created_at=datetime.utcnow() - timedelta(days=6),
        )
        db.add(v1)
        db.flush()

        v2 = PromptVersion(
            id=uuid.uuid4(),
            branch_id=main_branch.id,
            prompt_text="You are a friendly and professional customer support agent for Acme Corp. Always greet the customer warmly, address their concern directly, and end with an offer to help further. Keep responses concise and under 100 words.",
            model_config={"model": "gpt-4o-mini", "temperature": 0.5, "max_tokens": 500, "system_message": None},
            commit_message="Added persona, length constraint, structure",
            author_id=demo_user.id,
            eval_score=None,
            created_at=datetime.utcnow() - timedelta(days=5),
        )
        db.add(v2)
        db.flush()

        v3 = PromptVersion(
            id=uuid.uuid4(),
            branch_id=main_branch.id,
            prompt_text="You are a friendly and professional customer support agent for Acme Corp.\n\nWhen responding:\n1. Greet the customer by acknowledging their issue\n2. Provide a clear, direct solution\n3. Explain any next steps if needed\n4. Close warmly and offer further help\n\nKeep all responses under 100 words. Use simple, clear language. Never use jargon.",
            model_config={"model": "gpt-4o-mini", "temperature": 0.3, "max_tokens": 500, "system_message": None},
            commit_message="Structured response format, lower temperature for consistency",
            author_id=demo_user.id,
            eval_score=72.5,
            created_at=datetime.utcnow() - timedelta(days=4),
        )
        db.add(v3)
        db.flush()

        # Experiment branch
        exp_branch = Branch(
            id=uuid.uuid4(),
            repository_id=repo.id,
            name="experiment/empathetic-tone",
            created_from_version_id=v2.id,
            created_at=datetime.utcnow() - timedelta(days=3),
        )
        db.add(exp_branch)
        db.flush()

        v4 = PromptVersion(
            id=uuid.uuid4(),
            branch_id=exp_branch.id,
            prompt_text="You are an empathetic and warm customer support agent for Acme Corp. You genuinely care about solving each customer's problem.\n\nAlways:\n- Acknowledge how the customer feels\n- Validate their frustration if they express it\n- Offer a clear solution with empathy\n- End with genuine warmth\n\nKeep responses under 120 words.",
            model_config={"model": "gpt-4o-mini", "temperature": 0.6, "max_tokens": 600, "system_message": None},
            commit_message="Experiment: empathetic tone vs professional tone",
            author_id=demo_user.id,
            eval_score=81.0,
            created_at=datetime.utcnow() - timedelta(days=2),
        )
        db.add(v4)
        db.flush()

        v5 = PromptVersion(
            id=uuid.uuid4(),
            branch_id=main_branch.id,
            prompt_text="You are a friendly and professional customer support agent for Acme Corp.\n\nWhen responding:\n1. Greet the customer by acknowledging their specific issue\n2. Provide a clear, direct solution or next step\n3. If the issue is complex, break it into numbered steps\n4. Close warmly and offer further help\n\nTone: Professional but human. Never robotic.\nLength: Under 100 words unless a step-by-step is needed.\nLanguage: Simple and clear. No jargon.",
            model_config={"model": "gpt-4o-mini", "temperature": 0.3, "max_tokens": 600, "system_message": None},
            commit_message="Merged learnings from experiment — added tone and complexity guidance",
            author_id=demo_user.id,
            eval_score=88.5,
            created_at=datetime.utcnow() - timedelta(days=1),
        )
        db.add(v5)
        db.flush()

        print("Creating eval suite...")
        suite = EvalSuite(
            id=uuid.uuid4(),
            repository_id=repo.id,
            name="Core support scenarios",
            created_at=datetime.utcnow() - timedelta(days=5),
        )
        db.add(suite)
        db.flush()

        cases_data = [
            {
                "input": "My order hasn't arrived and it's been 2 weeks.",
                "expected": "Apologize, offer to investigate, provide next steps",
                "eval_type": EvalType.similarity,
            },
            {
                "input": "How do I reset my password?",
                "expected": "Go to login page, click forgot password, check your email",
                "eval_type": EvalType.similarity,
            },
            {
                "input": "I was charged twice for my subscription.",
                "expected": "Apologize for the billing error, confirm refund will be processed within 3-5 business days",
                "eval_type": EvalType.similarity,
            },
        ]

        cases = []
        for c in cases_data:
            case = EvalCase(
                id=uuid.uuid4(),
                suite_id=suite.id,
                input_text=c["input"],
                expected_output=c["expected"],
                eval_type=c["eval_type"],
            )
            db.add(case)
            cases.append(case)
        db.flush()

        print("Creating eval runs...")
        run_v3 = EvalRun(
            id=uuid.uuid4(),
            version_id=v3.id,
            suite_id=suite.id,
            status=EvalRunStatus.completed,
            overall_score=72.5,
            results=[
                {"case_id": str(cases[0].id), "input_text": cases_data[0]["input"], "expected_output": cases_data[0]["expected"], "actual_output": "I apologize for the delay. I'll investigate your order right away. Please share your order number and I'll update you within 24 hours. Happy to help!", "eval_type": "similarity", "score": 0.78, "passed": True},
                {"case_id": str(cases[1].id), "input_text": cases_data[1]["input"], "expected_output": cases_data[1]["expected"], "actual_output": "To reset your password, go to the login page and click 'Forgot Password'. Enter your email and check your inbox for the reset link. Let me know if you need help!", "eval_type": "similarity", "score": 0.82, "passed": True},
                {"case_id": str(cases[2].id), "input_text": cases_data[2]["input"], "expected_output": cases_data[2]["expected"], "actual_output": "I'm sorry about the double charge. I'll look into this immediately. Could you confirm your account email? We'll process a refund if confirmed.", "eval_type": "similarity", "score": 0.57, "passed": False},
            ],
            created_at=datetime.utcnow() - timedelta(days=4),
        )
        db.add(run_v3)

        run_v5 = EvalRun(
            id=uuid.uuid4(),
            version_id=v5.id,
            suite_id=suite.id,
            status=EvalRunStatus.completed,
            overall_score=88.5,
            results=[
                {"case_id": str(cases[0].id), "input_text": cases_data[0]["input"], "expected_output": cases_data[0]["expected"], "actual_output": "I understand how frustrating a delayed order can be. I'll investigate immediately — please share your order number and I'll provide an update within 24 hours. Thank you for your patience!", "eval_type": "similarity", "score": 0.91, "passed": True},
                {"case_id": str(cases[1].id), "input_text": cases_data[1]["input"], "expected_output": cases_data[1]["expected"], "actual_output": "To reset your password: 1. Go to the login page 2. Click 'Forgot Password' 3. Enter your email 4. Check your inbox for the reset link. Let me know if you run into any issues!", "eval_type": "similarity", "score": 0.89, "passed": True},
                {"case_id": str(cases[2].id), "input_text": cases_data[2]["input"], "expected_output": cases_data[2]["expected"], "actual_output": "I sincerely apologize for the double charge. I've flagged this for our billing team and a refund will be processed within 3-5 business days. You'll receive a confirmation email. Is there anything else I can help you with?", "eval_type": "similarity", "score": 0.85, "passed": True},
            ],
            created_at=datetime.utcnow() - timedelta(days=1),
        )
        db.add(run_v5)

        db.commit()
        print("\n✓ Demo data created successfully!")
        print(f"  Demo login: demo@flux.dev / demo1234")
        print(f"  Workspace: Customer Support AI")
        print(f"  Repository: support-response-prompt")
        print(f"  Versions: 5 (3 on main, 2 on experiment branch)")
        print(f"  Eval suite: Core support scenarios (3 test cases)")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()