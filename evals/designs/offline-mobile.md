# Offline-first field inspection app

Team: 3 engineers. Inspectors work in places with no network for hours, then sync. Scale range to explain: 1 customer with 40 inspectors up to 300 customers with 25,000 inspectors.

Components:
- Mobile app with local storage of forms, photos, and checklists.
- Sync between devices and the server when a network is available.
- Conflict handling when two inspectors edit the same inspection offline.
- Server API and database.
- Photo upload, often in bulk after a day offline.
- Customer admin web portal with reports.
- Push notifications for new assignments.
