# Deterministic explainability (Phase 18)

Recommendations keep an auditable fact list built from **stored** scores
and evidence. The LLM is not the ranking engine.

```text
Recommended because:
1. Addresses Deep Learning gap.
2. Gap priority = Critical.
3. Semantic similarity = 0.89.
4. Prerequisites are satisfied.
5. Difficulty matches learner level.
6. Learner prefers video.
```

`recommendation/explain.py` emits those facts. `llm/verbalize.py` joins
them into a paragraph. An optional LLM flag may only rephrase the same
sentences; it cannot add skills or scores. The RAG assistant lives in
`llm/assistant.py`.

Each recommendation, practice pair, mentor match, and path step stores
`explanation = { facts, verbalization }` plus rank, components, matched
skills, and gap priority.

The UI **Why?** button shows the numbered facts. The Phase 19 assistant can quote those stored facts when asked why a course was recommended.
