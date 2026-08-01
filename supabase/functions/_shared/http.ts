import {
  ALLOWED_BROWSER_ORIGINS,
  MAX_BROKER_REQUEST_BYTES,
  MAX_BROWSER_REQUEST_BYTES,
} from "./constants.ts";
import { SafeHttpError } from "./errors.ts";

const ALLOWED_ORIGIN_SET = new Set<string>(ALLOWED_BROWSER_ORIGINS);
const JSON_HEADERS = {
  "Cache-Control": "no-store",
  "Content-Type": "application/json; charset=utf-8",
  "X-Content-Type-Options": "nosniff",
};

function corsHeaders(origin: string): Record<string, string> {
  return {
    "Access-Control-Allow-Headers": "content-type",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Origin": origin,
    "Access-Control-Max-Age": "600",
    "Vary": "Origin",
  };
}

export function browserOrigin(request: Request): string {
  const origin = request.headers.get("Origin") ?? "";
  if (!ALLOWED_ORIGIN_SET.has(origin)) {
    throw new SafeHttpError(403, "origin_not_allowed");
  }
  return origin;
}

export function handleBrowserPreflight(request: Request): Response | null {
  if (request.method !== "OPTIONS") return null;

  const origin = browserOrigin(request);
  if (request.headers.get("Access-Control-Request-Method") !== "POST") {
    throw new SafeHttpError(405, "method_not_allowed");
  }

  const requestedHeaders =
    (request.headers.get("Access-Control-Request-Headers") ?? "")
      .split(",")
      .map((value) => value.trim().toLowerCase())
      .filter(Boolean);
  if (requestedHeaders.some((value) => value !== "content-type")) {
    throw new SafeHttpError(403, "headers_not_allowed");
  }

  return new Response(null, { status: 204, headers: corsHeaders(origin) });
}

export function requireBrowserPost(request: Request): string {
  const origin = browserOrigin(request);
  if (request.method !== "POST") {
    throw new SafeHttpError(405, "method_not_allowed");
  }
  return origin;
}

export function requireBrokerPost(request: Request): void {
  if (request.headers.has("Origin")) {
    throw new SafeHttpError(403, "browser_requests_forbidden");
  }
  if (request.method !== "POST") {
    throw new SafeHttpError(405, "method_not_allowed");
  }
}

export function readBrowserJson(
  request: Request,
): Promise<Record<string, unknown>> {
  return readJson(request, MAX_BROWSER_REQUEST_BYTES);
}

export function readBrokerJson(
  request: Request,
): Promise<Record<string, unknown>> {
  return readJson(request, MAX_BROKER_REQUEST_BYTES);
}

async function readJson(
  request: Request,
  maximumBytes: number,
): Promise<Record<string, unknown>> {
  if (
    (request.headers.get("Content-Type") ?? "").toLowerCase() !==
      "application/json"
  ) {
    throw new SafeHttpError(415, "content_type_required");
  }

  const declaredLength = request.headers.get("Content-Length");
  if (declaredLength !== null) {
    const parsedLength = Number(declaredLength);
    if (
      !Number.isSafeInteger(parsedLength) || parsedLength < 0 ||
      parsedLength > maximumBytes
    ) {
      throw new SafeHttpError(413, "request_too_large");
    }
  }

  const bytes = new Uint8Array(await request.arrayBuffer());
  if (bytes.byteLength === 0) throw new SafeHttpError(400, "invalid_json");
  if (bytes.byteLength > maximumBytes) {
    throw new SafeHttpError(413, "request_too_large");
  }

  let parsed: unknown;
  try {
    const text = new TextDecoder("utf-8", { fatal: true }).decode(bytes);
    parsed = JSON.parse(text);
  } catch {
    throw new SafeHttpError(400, "invalid_json");
  }

  if (!isPlainObject(parsed)) throw new SafeHttpError(400, "invalid_json");
  return parsed;
}

export function browserJson(
  origin: string,
  body: Record<string, unknown>,
  status = 200,
): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...JSON_HEADERS, ...corsHeaders(origin) },
  });
}

export function brokerJson(
  body: Record<string, unknown>,
  status = 200,
): Response {
  return new Response(JSON.stringify(body), { status, headers: JSON_HEADERS });
}

export function browserError(
  origin: string | null,
  error: SafeHttpError,
): Response {
  const headers = origin === null
    ? JSON_HEADERS
    : { ...JSON_HEADERS, ...corsHeaders(origin) };
  return new Response(JSON.stringify({ error: error.code }), {
    status: error.status,
    headers,
  });
}

export function brokerError(error: SafeHttpError): Response {
  return new Response(JSON.stringify({ error: error.code }), {
    status: error.status,
    headers: JSON_HEADERS,
  });
}

function isPlainObject(value: unknown): value is Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return false;
  }
  const prototype = Object.getPrototypeOf(value);
  return prototype === Object.prototype || prototype === null;
}
