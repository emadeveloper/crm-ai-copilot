import createClient from "openapi-fetch";
import type { paths } from "./api";

export type { components, operations, paths } from "./api";

export type ApiClient = ReturnType<typeof createClient<paths>>;

export function makeApiClient(baseUrl: string): ApiClient {
  return createClient<paths>({
    baseUrl,
    // Defer to the live global fetch on every call so test doubles (MSW) that patch
    // globalThis.fetch after this client is constructed still take effect.
    fetch: (request) => globalThis.fetch(request),
  });
}
