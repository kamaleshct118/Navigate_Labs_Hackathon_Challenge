# Engineering Production Deployment & Change Management SOP
- **Document ID**: ENG-SOP-008
- **Version**: 1.0
- **Status**: CURRENT
- **Effective Date**: 2024-12-01
- **Department**: Engineering
- **Branch ID**: Global
- **Region**: Global
- **Classification**: Confidential SOP

---

### Section 1: Purpose & Eligibility Scope
This Standard Operating Procedure (SOP) outlines mandatory engineering change management controls, code review requirements, and deployment scheduling protocols for all software platforms, cloud infrastructure, and core backend databases. The scope applies globally (`Global`) to all software engineers, DevOps specialists, site reliability engineers (SREs), system administrators, and third-party development contractors operating across enterprise technical environments.

### Section 2: Policy Rules & Financial Thresholds
To ensure system stability, high availability, and zero unscheduled downtime for customer-facing services, production changes must strictly adhere to release windows and verification rules. Standard deployments are permitted exclusively during designated maintenance windows: Deployments allowed Tuesday-Thursday 10:00-14:00 UTC. Deployments on Mondays, Fridays, weekends, or public holidays are strictly forbidden. Every Pull Request (PR) targeted for production deployment must undergo automated static analysis scanning, pass unit/integration tests with a minimum 80% code coverage, and receive at least two peer code reviews. Additionally, an automated, tested rollback plan is mandatory for PR approval. A strict Q4 code freeze is active Dec 15 to Jan 2. Emergency hotfixes during code freeze require written approval from VP of Engineering.

### Section 3: Approval Hierarchy & Operational Workflow
Release authorization follows a structured technical change advisory process:
1. **Standard Deployment**: Peer Engineer Review (2 approvals) -> Automated CI/CD Pipeline pass -> Engineering Manager sign-off -> Deployment within 10:00-14:00 UTC window.
2. **Major Release / Architectural Change**: Requires Change Advisory Board (CAB) review and SRE Lead approval 5 business days prior to release.
3. **Freeze Hotfix Approval**: Emergency hotfixes during code freeze require written approval from VP of Engineering following incident severity level 1 (Sev-1) triage.

Post-deployment monitoring must be maintained for at least 60 minutes following deployment execution.

### Section 4: Exceptions, Compliance Violations & Human Escalations
Bypassing CI/CD pipeline checks, forcing unapproved PR merges ("rogue deployments"), or releasing unauthorized changes during the Q4 code freeze without VP sign-off constitutes gross technical misconduct and results in immediate revocation of production access credentials. Unplanned outages caused by non-compliant releases trigger a mandatory post-mortem review. Unresolved architectural deadlocks or critical Sev-1 production outages during freeze windows MUST be escalated immediately to the VP of Engineering and Chief Technology Officer (CTO).
