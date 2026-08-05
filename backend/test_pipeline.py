import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from backend.graph.agent_graph import run_compliance_agent

def test_all_scenarios():
    test_cases = [
        (
            "Scenario 1: Direct Query with Specified Location",
            "What is the annual PTO allowance for employees in US New York branch?"
        ),
        (
            "Scenario 2: Vague / Location-Ambiguous Query (Branch Contradiction)",
            "What is the annual PTO allowance and equipment stipend?"
        ),
        (
            "Scenario 3: Version Reconciled Query (Current vs Outdated)",
            "What is the equipment allowance in US New York under HR-POL-US-001?"
        ),
        (
            "Scenario 4: Multi-Hop Cross-Policy SOP (Lost Laptop + GDPR)",
            "My company laptop was stolen at an airport. What should I do and who needs to be notified?"
        ),
        (
            "Scenario 5: High-Risk Compliance Escalation (Subpoena / Anti-Bribery)",
            "A foreign government official asked for financial audit records and offered a gift."
        ),
        (
            "Scenario 6: Completely Missing Policy / Uncovered Topic",
            "What is the office policy for bringing pet dogs to work?"
        ),
        (
            "Scenario 7: Document Exists but Specific Detail is Incomplete",
            "What is the maternity leave stipend amount in EU London branch?"
        )
    ]

    print("=" * 85)
    print(" 🧪 TESTING ENTERPRISE COMPLIANCE LANGGRAPH AGENT - ALL 7 SCENARIOS")
    print("=" * 85)

    for label, query in test_cases:
        print(f"\n🔹 {label}")
        print(f"❓ Query: '{query}'")
        result = run_compliance_agent(query)
        print(f"🎯 Intent: {result['intent']}")
        print(f"⚠️ Contradiction Detected: {result['has_contradiction']}")
        print(f"🚨 Requires Escalation: {result['requires_human_escalation']}")
        print(f"📌 Citations: {result['citations']}")
        print(f"📝 Response Excerpt:\n{result['response'][:280]}...")
        print("-" * 85)

if __name__ == "__main__":
    test_all_scenarios()
