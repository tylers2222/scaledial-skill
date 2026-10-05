# Internal tool for a 20-person operations team

Team: 1 engineer, part time. The tool tracks supplier orders and sends reminder emails. Scale range to explain: 20 users up to 200 users.

Components in the proposed design:
- React front end served from a CDN.
- API split into 4 services (orders, suppliers, notifications, auth), each in its own container.
- Container orchestration cluster with autoscaling.
- Message broker between the services.
- Relational database with a read replica.
- Cache layer in front of the database.
- Scheduled job that sends reminder emails every morning.
- Centralized logging and metrics stack.
