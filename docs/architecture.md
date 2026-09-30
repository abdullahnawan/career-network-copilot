# Architecture decisions

## Boundaries

The Next.js frontend is a browser client. FastAPI is the single application
boundary for authentication, authorization, validation, integrations, scoring,
message grounding, and analytics. SQLAlchemy provides typed persistence access
and Alembic will manage schema changes.

## Data flow

1. A user submits profile or contact data through the frontend.
2. FastAPI validates and authorizes the request.
3. PostgreSQL stores user-owned records and contact provenance.
4. The matching service calculates deterministic factor scores and explanations.
5. CSV imports validate bounded user-uploaded files without fetching URLs.
6. The frontend presents recommendations and requires user review before copying
   any draft.

External sources will be explicitly attributed, cached where appropriate, and
never crawled. Optional semantic similarity is additive and cannot make a
recommendation unexplained.

## Phase 4 contact and matching decisions

Contacts are intentionally separate from student profiles and record whether
they were entered manually or imported from CSV, along with a user-provided
source name. `profile_url` is reference data only. The backend never requests
that URL.

The current matcher uses normalized word overlap and fixed weights: role 30%,
industry 20%, location 15%, school 15%, and skills 20%. Each component is
either 0 or 100, making the total and its reasons directly auditable. This is
not an endorsement or an AI-generated ranking.

## Phase 5 outreach decisions

Outreach drafts are stored separately from contacts and profiles with foreign
keys to both records. Purpose, channel, tone, and lifecycle status use bounded
enum-like values. Status changes are validated by the backend; a draft cannot
skip directly to replied, an archived draft cannot be reopened, and replied
cannot move backward to sent_manually.

Suggestions are deterministic templates built only from stored student and
contact fields plus existing match reasons when available. Each suggestion
returns the facts used, an optional email subject, character count, and the
300-character connection-note limit. Suggestions are not saved until the user
explicitly saves them. The system never sends messages or connects to
LinkedIn, email, or another messaging provider.

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Unsupported claims in drafts | Store evidence and validate generated text against it. |
| Privacy leakage | Private-by-default data, resource authorization, export/delete controls. |
| Provider/API outages | Timeouts, rate-limit handling, caching, and deterministic local behavior. |
| Biased recommendations | Exclude sensitive characteristics and expose weighted factors. |
| Accidental automation | Keep external profile actions user-initiated and out of scope. |
