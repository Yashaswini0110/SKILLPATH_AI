# LLM integration

`verbalize.py` joins stored explanation facts. `retrieve.py` scores
employee and catalog passages. `assistant.py` answers only from those
passages. `client.py` calls NVIDIA NIM (`openai/gpt-oss-20b`) only when
`LLM_ENABLED` and an API key are set; otherwise `complete()` is a no-op.

The LLM is never the recommendation engine. Do not send email, resume
text, or other extra PII to an external API. GitHub evidence is a later
phase.
