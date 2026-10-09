# Privacy notice

Career Network Copilot is a human-controlled networking assistant. Its
recommendations are assistance, not endorsements, and users remain responsible
for respectful outreach.

The application is designed to store only information needed for a user's
career profile, contacts, source evidence, drafts, and outreach tracking.
Resumes and account data are private by default. Authenticated users can export
and permanently delete their data. The product will not scrape LinkedIn, automate LinkedIn
actions, or send messages.

Permitted-source records will retain their source URL and retrieval metadata.
Optional analytics will be aggregate, privacy-conscious product events rather
than advertising or invasive tracking.

Contact imports are limited to user-uploaded CSV files. The application does
not fetch profile URLs, crawl websites, scrape LinkedIn, or use unofficial
LinkedIn APIs. CSV files are bounded in size and row count, validated row by
row, and formula-like spreadsheet values are rejected so imported text is not
treated as an instruction.

Outreach is human-controlled. Draft suggestions use only stored profile and
contact fields, show the facts used for personalization, and remain editable.
The application does not send messages, connect to LinkedIn messaging, click
send controls, or claim that a message was sent automatically. A user must
explicitly confirm manual-send, reply, archive, and delete actions. Draft
status records describe user-reported activity only.

Authentication uses Argon2id password hashes and opaque server-managed
sessions. Session tokens are stored only as SHA-256 hashes in the database and
the raw token is held in an HttpOnly SameSite=Lax cookie. Password hashes,
session hashes, and tokens are excluded from exports. Account deletion requires
password confirmation and cascades through owned records and sessions.

Password-reset email is future work because no email provider is configured.
Authentication currently has no shared distributed rate limiter, so production
deployments must add rate limiting and use HTTPS with
`SESSION_COOKIE_SECURE=true`.
