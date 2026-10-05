# Photo-sharing app

Team: 5 engineers. Users upload photos from phones and follow each other. Scale range to explain: 10,000 users up to 20 million users, worldwide.

Components:
- Upload service that receives full-size photos (average 4 MB).
- Storage for originals and resized versions.
- Feed: shows each user recent photos from accounts they follow.
- Image resizing into 4 sizes after upload.
- Search over captions and usernames.
- Likes and comments counters shown on every photo.
- Current design: all photos stored as files on the application servers' disks, served by the application.
