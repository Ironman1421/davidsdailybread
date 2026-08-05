-- Cloudflare D1 schema for the first-1,000 diagnostic canary.
-- Apply only after separate provisioning and canary-execution authorization.

CREATE TABLE audience_visitors (
    definition_version INTEGER NOT NULL CHECK (definition_version = 1),
    month TEXT NOT NULL CHECK (
        length(month) = 7
        AND month GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]'
        AND CAST(substr(month, 6, 2) AS INTEGER) BETWEEN 1 AND 12
        AND date(month || '-01') = month || '-01'
    ),
    token_digest TEXT NOT NULL CHECK (
        length(token_digest) = 64
        AND token_digest NOT GLOB '*[^0-9a-f]*'
    ),
    first_seen_date TEXT NOT NULL CHECK (
        length(first_seen_date) = 10
        AND substr(first_seen_date, 1, 7) = month
        AND date(first_seen_date) = first_seen_date
    ),
    returned_date TEXT CHECK (
        returned_date IS NULL
        OR (
            length(returned_date) = 10
            AND substr(returned_date, 1, 7) = month
            AND date(returned_date) = returned_date
            AND returned_date > first_seen_date
        )
    ),
    qualified_date TEXT CHECK (
        qualified_date IS NULL
        OR (
            returned_date IS NOT NULL
            AND length(qualified_date) = 10
            AND substr(qualified_date, 1, 7) = month
            AND date(qualified_date) = qualified_date
            AND qualified_date > returned_date
        )
    ),
    expires_on TEXT NOT NULL CHECK (
        expires_on = date(first_seen_date, '+35 days')
    ),
    PRIMARY KEY (definition_version, month, token_digest)
) STRICT, WITHOUT ROWID;

CREATE INDEX audience_visitors_expiry
    ON audience_visitors (expires_on);

CREATE TABLE audience_monthly_aggregates (
    definition_version INTEGER NOT NULL CHECK (definition_version = 1),
    month TEXT NOT NULL CHECK (
        length(month) = 7
        AND month GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]'
        AND CAST(substr(month, 6, 2) AS INTEGER) BETWEEN 1 AND 12
        AND date(month || '-01') = month || '-01'
    ),
    first_seen_visitors INTEGER NOT NULL DEFAULT 0 CHECK (first_seen_visitors >= 0),
    returning_visitors INTEGER NOT NULL DEFAULT 0 CHECK (
        returning_visitors >= 0
        AND returning_visitors <= first_seen_visitors
    ),
    qualified_engaged_returning_readers INTEGER NOT NULL DEFAULT 0 CHECK (
        qualified_engaged_returning_readers >= 0
        AND qualified_engaged_returning_readers <= returning_visitors
    ),
    PRIMARY KEY (definition_version, month)
) STRICT, WITHOUT ROWID;

CREATE TRIGGER audience_visitor_identity_immutable
BEFORE UPDATE ON audience_visitors
WHEN OLD.definition_version != NEW.definition_version
  OR OLD.month != NEW.month
  OR OLD.token_digest != NEW.token_digest
  OR OLD.first_seen_date != NEW.first_seen_date
  OR OLD.expires_on != NEW.expires_on
BEGIN
    SELECT RAISE(ABORT, 'audience visitor identity is immutable');
END;

CREATE TRIGGER audience_first_seen_aggregate
AFTER INSERT ON audience_visitors
BEGIN
    INSERT INTO audience_monthly_aggregates (
        definition_version,
        month,
        first_seen_visitors,
        returning_visitors,
        qualified_engaged_returning_readers
    ) VALUES (NEW.definition_version, NEW.month, 1, 0, 0)
    ON CONFLICT (definition_version, month) DO UPDATE SET
        first_seen_visitors = first_seen_visitors + 1;
END;

CREATE TRIGGER audience_returning_aggregate
AFTER UPDATE OF returned_date ON audience_visitors
WHEN OLD.returned_date IS NULL AND NEW.returned_date IS NOT NULL
BEGIN
    UPDATE audience_monthly_aggregates
       SET returning_visitors = returning_visitors + 1
     WHERE definition_version = NEW.definition_version
       AND month = NEW.month;
END;

CREATE TRIGGER audience_qualified_aggregate
AFTER UPDATE OF qualified_date ON audience_visitors
WHEN OLD.qualified_date IS NULL AND NEW.qualified_date IS NOT NULL
BEGIN
    UPDATE audience_monthly_aggregates
       SET qualified_engaged_returning_readers =
           qualified_engaged_returning_readers + 1
     WHERE definition_version = NEW.definition_version
       AND month = NEW.month;
END;
