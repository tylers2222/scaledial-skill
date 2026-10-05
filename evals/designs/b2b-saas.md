# Multi-tenant B2B SaaS (HR software)

Team: 15 engineers. Customers are companies from 20 to 50,000 employees. Some enterprise customers in the EU and in healthcare. Scale range to explain: 50 customer companies up to 5,000.

Components:
- Web app and API for employees and HR staff.
- Database holding employee records, salaries, and documents.
- File storage for contracts and ID documents.
- Background jobs: payroll exports, email notifications, nightly imports from customer HR systems.
- Audit log of every change to an employee record.
- Single sign-on with each customer's identity provider.
- Reporting that HR admins run over their own company's data.
