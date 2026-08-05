# IT Security & Device Protection Standard Operating Procedure
- **Document ID**: SOP-IT-SEC-004
- **Version**: 3.0
- **Status**: CURRENT
- **Effective Date**: 2025-02-15
- **Department**: IT
- **Branch ID**: Global
- **Region**: Global
- **Classification**: Confidential SOP

---

### Section 1: Purpose & Eligibility Scope
This Standard Operating Procedure (SOP) defines mandatory technical security controls and emergency response protocols for managing enterprise hardware endpoints. The scope applies globally (`Global`) across all business units, physical facilities, and operating regions. It covers all full-time employees, part-time staff, third-party contractors, temporary workers, and external partners who are issued company-owned laptops, workstations, mobile devices, or removable storage media. Compliance with this procedure is a mandatory condition of network access and system authorization across the enterprise infrastructure.

### Section 2: Policy Rules & Financial Thresholds
All corporate endpoints must maintain strict cryptographic protection to prevent unauthorized data access. Full-disk 256-bit BitLocker encryption (for Windows systems) or FileVault encryption (for macOS systems) is mandatorily enforced on 100% of enterprise endpoints, managed centrally via corporate Unified Endpoint Management (UEM) agents. Local administrator privileges on endpoint devices are revoked by default; software installation is strictly restricted to pre-approved corporate software catalog items. In the event of a lost, stolen, or physically compromised laptop, the assigned user must immediately execute the Lost Laptop Protocol: report the incident within 1 hour to security-incident@enterprise.com to enable remote cryptographic wipe commands and revoke session tokens.

### Section 3: Approval Hierarchy & Operational Workflow
Security incidents and encryption compliance exceptions follow a strict escalation workflow governed by the Global Information Security Operations Center (SOC):
1. **Tier 1 (SOC Incident Intake)**: Triage initial lost device notification submitted to `security-incident@enterprise.com`, initiate UEM remote lock/wipe, and revoke user Okta credentials within 15 minutes of report receipt.
2. **Tier 2 (InfoSec Lead)**: Assess data classification on the lost asset (e.g., restricted IP, financial records, customer personal data).
3. **Tier 3 (Multi-Hop GDPR Cross-Reference)**: For lost devices containing EU customer PII, IT Security must cross-reference EU HR Policy Section 3 and notify the DPO within 12 hours to comply with GDPR 72-hour reporting rules.

Device hardware replacements resulting from theft incur a $250 departmental replacement charge unless accompanied by an official police theft report.

### Section 4: Exceptions, Compliance Violations & Human Escalations
Disabling, altering, or tampering with full-disk encryption drivers, endpoint detection software, or UEM agents is strictly prohibited and constitutes a major security breach resulting in immediate termination of network access and formal employment review. Delaying the reporting of a missing device beyond the mandatory 1-hour window compromises enterprise containment efforts. Any security incidents involving nation-state threat vectors, compromised administrative root credentials, or potential GDPR regulatory breaches MUST be escalated immediately to the Chief Information Security Officer (CISO) and the Data Protection Officer (DPO).
