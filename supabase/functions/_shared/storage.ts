import { createClient, type SupabaseClient } from "@supabase/supabase-js";

const BUCKET = "bake-handoffs";
const DOWNLOAD_SECONDS = 60;
const MAXIMUM_RETENTION_MILLISECONDS = 6 * 60 * 60 * 1_000;
const OBJECT_NAME_PATTERN = /^[0-9a-f-]{36}-[0-9a-f]{64}\.zip$/;

let client: SupabaseClient | null = null;

function storageClient(): SupabaseClient {
  if (client !== null) return client;
  const url = Deno.env.get("SUPABASE_URL") ?? "";
  const secret = Deno.env.get("DDB_READER_STORAGE_SECRET_KEY") ?? "";
  if (!/^https?:\/\//.test(url) || !secret.startsWith("sb_secret_")) {
    throw new Error("storage_unconfigured");
  }
  client = createClient(url, secret, {
    auth: {
      autoRefreshToken: false,
      persistSession: false,
      detectSessionInUrl: false,
    },
  });
  return client;
}

export async function createHandoffUpload(
  objectPath: string,
): Promise<Record<string, unknown>> {
  const { data, error } = await storageClient().storage.from(BUCKET)
    .createSignedUploadUrl(objectPath, { upsert: false });
  if (error || data === null) throw new Error("handoff_upload_unavailable");
  return {
    status: "ready",
    objectPath,
    signedUrl: data.signedUrl,
    expiresInSeconds: 7_200,
    immutable: true,
    requiredCacheControl: "0",
  };
}

export async function createHandoffDownload(
  objectPath: string,
): Promise<Record<string, unknown>> {
  const { data, error } = await storageClient().storage.from(BUCKET)
    .createSignedUrl(objectPath, DOWNLOAD_SECONDS, { download: true });
  if (error || data === null) throw new Error("handoff_download_unavailable");
  return {
    status: "ready",
    objectPath,
    signedUrl: data.signedUrl,
    expiresInSeconds: DOWNLOAD_SECONDS,
  };
}

export async function deleteHandoff(
  objectPath: string,
): Promise<Record<string, unknown>> {
  const { error } = await storageClient().storage.from(BUCKET).remove([
    objectPath,
  ]);
  if (error) throw new Error("handoff_delete_unavailable");
  return { status: "deleted", objectPath };
}

export async function cleanupExpiredHandoffs(
  referenceTime = Date.now(),
): Promise<Record<string, unknown>> {
  let offset = 0;
  let deleted = 0;
  while (true) {
    const { data, error } = await storageClient().storage.from(BUCKET).list(
      "",
      {
        limit: 100,
        offset,
        sortBy: { column: "created_at", order: "asc" },
      },
    );
    if (error || data === null) throw new Error("handoff_cleanup_unavailable");
    if (data.length === 0) break;

    const expired = data.filter((object) => {
      if (!OBJECT_NAME_PATTERN.test(object.name) || !object.created_at) {
        return false;
      }
      const createdAt = Date.parse(object.created_at);
      return Number.isFinite(createdAt) &&
        createdAt <= referenceTime - MAXIMUM_RETENTION_MILLISECONDS;
    }).map((object) => object.name);
    if (expired.length > 0) {
      const { error: removeError } = await storageClient().storage.from(BUCKET)
        .remove(expired);
      if (removeError) throw new Error("handoff_cleanup_unavailable");
      deleted += expired.length;
      continue;
    }

    if (data.length < 100) break;
    offset += data.length;
  }
  return { status: "complete", deleted };
}
