# Migration path: `GeminiAIStudioAdapter` → `VertexAIAdapter`

**Status:** design note (Phase 3 of the roadmap). Not implemented — the MVP runs on the AI Studio
free tier to stay at zero cost.

## Why it's cheap to do

The domain depends only on the `LLMProvider` port (`app/domain/ports.py`):

```python
class LLMProvider(Protocol):
    async def analyze(self, lead: Lead) -> LeadAnalysis: ...
```

Nothing in `app/domain/**` or `app/application/**` imports the Gemini SDK — the
`test_architecture.py` guard enforces that. So swapping providers is: add one adapter module,
change one line in the composition root.

## What changes

`google-genai` is the **same SDK** for AI Studio and Vertex AI. The only differences:

| | AI Studio (now) | Vertex AI (target) |
| --- | --- | --- |
| Client | `genai.Client(api_key=...)` | `genai.Client(vertexai=True, project=..., location=...)` |
| Auth | API key | Application Default Credentials (workload identity / service account) |
| Billing | free, prompts may be used for training | billed, prompts never used for training |
| Models | Flash-class only | Flash **and** Pro |

Because the client construction is the only thing that differs, `GeminiAIStudioAdapter` already
does 95% of the work. Options:

1. **Rename + reparametrise** `GeminiAIStudioAdapter` → `GeminiAdapter`, and give
   `gemini_generate` / `from_client` both client shapes. The prompt, JSON parsing, error
   translation and `aiolimiter` throttle are unchanged.
2. Keep a thin `VertexAIAdapter` subclass whose only override is `from_settings`.

## Composition-root change

`app/infra/container.py::Container.from_settings`:

```python
# before
genai_client = genai.Client(api_key=settings.gemini_api_key)

# after
genai_client = genai.Client(
    vertexai=True,
    project=settings.gcp_project,
    location=settings.gcp_location,
)
```

Add `gcp_project` / `gcp_location` to `Settings`, drop `gemini_api_key`. The rate limiter can be
relaxed or removed once off the free-tier 15 req/min budget.

## Deployment change

- Run on **Cloud Run** instead of Render (the `Dockerfile` already works there — see
  `render.yaml` for the equivalent env vars).
- Grant the Cloud Run service account `roles/aiplatform.user`.
- Remove the synthetic-data-only constraint from the README: Vertex does not train on prompts.
