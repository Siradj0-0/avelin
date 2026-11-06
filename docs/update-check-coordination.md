# Update-check coordination specification

**Status: proposal, not implemented.** The checker remains advisory: it does not download or install releases. This specification addresses [issue #88](https://github.com/Siradj0-0/avelin/issues/88) without deciding the shell-extraction boundary. Existing behavior and comparison limits are in [update-security.md](update-security.md).

## Goals and boundaries

The startup check and user-initiated check share one controller per application process. Keep the GTK main thread responsive, avoid parallel requests and duplicate notifications, and never label a failed or stale check as current. There is no cross-process lock or promise to eliminate requests from other Avelin processes. Do not change installation behavior, introduce credentials, or silently install software.

## Request lifecycle

- States are **idle**, **checking**, and **cooldown**; an outcome records its own status and observation time. Only the main thread mutates UI/controller state. A worker performs the blocking metadata request, then schedules one completion on the main thread.
- In idle, startup or an explicit check starts one worker. While checking, subsequent requests coalesce into that in-flight operation: they do not start another worker, queue a retry, or open another dialog. Indicate that a check is already underway and retain accessible feedback.
- Attach a monotonically increasing request generation to each started check. A completion may update state only if its generation is still active and the controller/window is alive. Ignore duplicate, obsolete and late callbacks; closing the window must not lead to UI access after destruction.
- A successful new-release result may show at most one dialog for that request. Failure, unknown, no-release and current results do not show a new-release dialog. Show the actual advisory message and the time it was checked; a positive result means only a newer comparable tag was observed, not that an artifact is trusted or the newest release was found.
- Bound response size and network operations as today. An individual socket timeout is not a strict wall-clock deadline. If a total deadline is introduced, use cancellable I/O or another design that actually prevents overlapping abandoned requests; never start a replacement merely because the UI timed out while an old worker is still running.

## Rate limits and offline failures

Classify 429 and documented GitHub rate-limit responses separately from generic 403, offline, timeout and malformed-response errors. On a recognized rate limit, enter cooldown. Parse a valid `Retry-After` duration or HTTP-date, and/or a valid `X-RateLimit-Reset` epoch when `X-RateLimit-Remaining` is zero; when both valid constraints apply, honor the later time. Use a monotonic deadline for the running process and UTC wall time only to convert an absolute date or display it. Handle invalid, missing, negative, overflow and past values safely. When no usable header is supplied for a secondary limit, wait at least one minute before a retry. Follow GitHub's [rate-limit guidance](https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api#handle-rate-limit-errors-appropriately).

- Manual clicks during cooldown do not bypass the deadline; show an accessible rate-limit explanation and next eligible time when known. Do not repeatedly display modal dialogs.
- Default to **no automatic retries**. If a future design adds them, use bounded exponential backoff and a maximum attempt count; never retry earlier than the server's deadline. Do not cap a server-provided wait downward. If an unreasonable value cannot be represented, fail closed and require an explicit later check rather than retry early.
- Offline, DNS, TLS, timeout and other errors produce an unavailable/error state, not `current`; no background retry storm. User-initiated retry is allowed after any active rate-limit cooldown. Never expose raw network exception text that may include sensitive details.
- Cache is optional and outside the initial implementation. If introduced, preserve the original observation timestamp, clearly mark it stale, handle 304 only when a usable matching cache exists, and never replace an error with an unqualified current status. Do not assume an unauthenticated conditional request is exempt from the primary limit.
- Cooldown persistence across restart requires a separate reviewed storage design, including malformed data, wall-clock changes and privacy. Without it, document that cooldown applies only for the current process; do not claim restart persistence.

## Verification before implementation ships

Use fake transports, fake clock and deterministic main-loop scheduling; never depend on live GitHub. Assert: repeated startup/manual triggers produce one request and one dialog; stale or post-close callbacks do nothing; success, incomplete results, offline, timeout, TLS failure and malformed metadata remain distinct; 403/429 headers and secondary limits follow the stated deadlines; malformed and extreme header values do not cause early retry; cooldown clicks do not open dialogs or spawn workers; and no worker completion mutates GTK off the main thread. Test clock jumps, duplicate callbacks, explicit retry after expiry and window teardown. If caching or persistence is later added, test missing/corrupt cache, 304, stale labels and restart/clock changes.

Run the full suite, compile check and GTK integration tests under a real headless display; inspect a screenshot before claiming visual validation. Agent 6 owns shell coordination and Agent 10 owns QA; request their review before implementation. Failure, timeout or cancellation must never trigger an install.
