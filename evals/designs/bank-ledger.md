# Ledger for a small fintech

Team: 6 engineers. Product: business accounts with card spending and transfers. Scale range to explain: 1,000 customers up to 500,000 customers.

Components:
- Ledger: double-entry records of every money movement. Balances must never be wrong.
- Payments API used by the mobile app and by partners. Partners retry requests on timeout.
- Card authorization webhook from the card processor, which must answer within 2 seconds.
- Monthly statements as PDFs.
- Analytics on customer spending for the product team.
- The current proposal suggests a multi-region distributed SQL database and an event-sourcing platform from day one.
