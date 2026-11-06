# Stopped Set B token-budget review

The user stopped the partial Set B run before any scores or per-clip results were displayed. This document contains API usage only.

Source: logs/llm_calls.csv, successful HTTP 200 chat-completion rows, sampled immediately after stopping. Model: openai/gpt-oss-120b. Failed HTTP attempts and /models calls are excluded from per-success token averages.

| Scope | Successful calls | Tokens | Average tokens/call | Projection for 212 calls |
|---|---:|---:|---:|---:|
| Stopped Set B run (last 69 logged calls at stop) | 69 | 103,515 | 1,500.22 | 318,046 |
| All successful calls logged at stop | 124 | 164,309 | 1,325.07 | 280,915 |

The Set B-specific projection exceeds the published 200,000 tokens/day default by about 118,046 tokens (59.0%). To fit 212 calls within that nominal budget, the average would need to be at most 943.4 tokens/call before other organization traffic. These are total-token projections, not exact remaining daily quota: the HTTP headers did not expose TPD, and Groq documents that cached tokens do not count toward limits. Logged calls may span quota windows.

References: https://console.groq.com/docs/rate-limits and https://console.groq.com/docs/api-reference (GPT-OSS reasoning_effort low/medium/high; medium is the default when omitted).

LLM_REASONING_EFFORT is now set to low in the local .env and in .env.example. It is passed only for gpt-oss models and participates in extraction cache identity. The stopped Set B checkpoint and old LLM caches remain preserved; Prisma caches remain untouched. No Set B restart or deletion has been performed. The next step is held at the requested Set C comparison stop point.
