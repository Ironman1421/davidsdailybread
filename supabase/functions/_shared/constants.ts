export const ALLOWED_BROWSER_ORIGINS = [
  "https://davidsdailybread.com",
  "https://www.davidsdailybread.com",
] as const;

export const CONSENT_VERSION = "reader-publication-v1";
export const MAX_SUBMISSION_BODY_CHARACTERS = 2_000;
export const MAX_BYLINE_CHARACTERS = 60;
export const MAX_BROWSER_REQUEST_BYTES = 12_288;
export const MAX_BROKER_REQUEST_BYTES = 8_192;
export const TURNSTILE_EXPECTED_ACTION = "reader-submit";
export const SUBMISSION_KINDS = [
  "ask_baker",
  "king_letter",
  "crumb_pin",
] as const;

export type SubmissionKind = (typeof SUBMISSION_KINDS)[number];
