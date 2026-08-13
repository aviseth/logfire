---
title: Understand Logfire rate limits
description: Plan query and API workloads around Logfire's request rates, usage quotas, and per-request limits.
---

# Understand Logfire rate limits

Keep scheduled queries, exports, and API integrations reliable by staying within the limits for your plan.

A rate limit caps how quickly requests can arrive. A quota caps total usage over a longer period. The limits below
apply to hosted Logfire and are shared across an organization, not assigned separately to each project or token.

## Compare limits by plan

The regional Query API limits apply to both `/v1/query` and `/v2/query`, regardless of whether you request JSON,
comma-separated values (CSV), or Apache Arrow output. The public management API limits apply across the routes
under `/api/v1`.

| Plan | Query API rate | Query API quota per billing cycle | Public management API rate |
| --- | --- | --- | --- |
| Personal | 5 per minute and 100 per hour | 72,000 queries | 50 per minute and 1,000 per hour |
| Team | No plan-specific rate | No plan-specific quota | 50 per minute and 1,000 per hour |
| Growth | No plan-specific rate | No plan-specific quota | 50 per minute and 1,000 per hour |
| Enterprise | Set by your contract and deployment | Set by your contract and deployment | Set by your contract and deployment |

"No plan-specific rate" does not remove normal service-capacity and abuse protections. Enterprise limits can be
tailored instead of having one public value. Contact [sales](mailto:sales@pydantic.dev) before committing an
Enterprise integration to a particular request rate.

Each request must pass both the per-minute and per-hour checks. Logfire smooths these limits over time: unused
capacity permits a burst up to the limit, then capacity returns gradually. There is no wall-clock minute or hour
reset to wait for. All read tokens and projects in an organization share its Query API allowance. All API keys,
other credentials, and routes under `/api/v1` share its public management API allowance.

The billing-cycle query quota also covers the organization as a whole. It resets when that organization's billing
cycle changes, not necessarily on the first day of a calendar month. Queries from the Logfire web interface do not
consume this Query API quota.

## Keep each request within its limit

These limits apply to one request on every hosted plan:

| Request | Default | Maximum | What to do at the maximum |
| --- | --- | --- | --- |
| Query API result | 100 rows | 10,000 rows | Export in several disjoint time ranges or other stable key ranges. |
| OpenTelemetry Protocol (OTLP) HTTP telemetry body | Not applicable | 100 MB | Send smaller batches. |

The Query API returns at most 10,000 rows even when the Structured Query Language (SQL) query or `limit` parameter
asks for more. A response with exactly 10,000 rows can therefore be incomplete. For exports, divide the data into
non-overlapping ranges and use a stable ordering with a unique tie-breaker so boundary rows are neither skipped nor
repeated. The [Query API guide](../how-to-guides/query-api.md) shows the available formats and parameters.

The telemetry body limit applies separately to each OTLP/HTTP request sent to `/v1/traces`, `/v1/logs`, or
`/v1/metrics`. The Logfire SDK batches telemetry below this size in normal use.

The legacy `https://logfire-api.pydantic.dev/v1/query` compatibility endpoint has an additional limit when it
buffers a JSON response: 100 MB on Personal and 500 MB on Team. Growth and Enterprise have no plan-specific
response-byte cap on this endpoint. The cap does not apply to its streaming CSV or Apache Arrow responses, or to
the regional `/v2/query` endpoint used by current clients. Prefer the regional `/v2/query` endpoint for new
integrations.

## Respond when Logfire limits a request

The response identifies which kind of limit you reached:

| Response | Meaning | Safe response |
| --- | --- | --- |
| `429 Too Many Requests` with `Retry-After` | A per-minute or per-hour rate was reached. | Wait for the number of seconds in `Retry-After`, then retry. |
| `429 Too Many Requests` without `Retry-After` and `Query quota exceeded for this organization` | The billing-cycle Query API quota was reached. | Wait for the next billing cycle or change plans. Repeated retries cannot succeed. |
| `413 Payload Too Large` from an OTLP/HTTP endpoint | One telemetry request exceeded 100 MB. | Reduce the exporter batch size before retrying. |
| `402 Payment Required` from an OTLP endpoint | Telemetry intake paused because the organization reached its usage allowance or spending-cap policy. | Change the plan or spending cap before sending more data. Do not retry the same batch unchanged. |

For a throughput limit, the Query API response says `Rate limit exceeded (minute)` or
`Rate limit exceeded (hour)`. The public management API returns a JSON `detail` that identifies the minute or hour
limit. In both cases, `Retry-After` is an integer number of seconds.

The Python query client raises `UnexpectedResponseError` for a `429` response and does not retry automatically.
Catch that error and use exponential backoff. If you make direct HTTP requests, use the more precise `Retry-After`
value from the response. Add random variation to concurrent workers' retry delays so they do not all retry at once.

OTLP clients treat `402` and `413` as non-retryable. They drop the rejected batch, and Logfire does not retain it.
Resolve the quota or batch-size problem before sending more telemetry.

Telemetry intake has a separate usage allowance rather than a requests-per-minute limit. Personal includes 10
million logs, spans, and metrics per billing cycle. Team and Growth include the same allowance, then bill additional
usage. A Personal organization eventually pauses intake after exceeding its allowance. A paid organization can set
a spending cap; Logfire can temporarily retain data beyond that cap while hiding it from queries, then pause intake
if usage continues. See [Cost & Usage](../logfire-costs.md) to inspect usage and understand billing.

## Reduce limit pressure

- Query only the time range you need, and aggregate in SQL instead of downloading raw rows to aggregate locally.
- Cache results that several workers or users request repeatedly.
- Limit concurrency and combine related reads into one query where practical.
- Space scheduled exports throughout the hour instead of starting every job at the same minute.
- Open **Organization settings → Plan & Usage** to confirm the organization's current plan and usage.
- Contact [support](mailto:support@pydantic.dev) if the response does not match the documented limit for your plan.
