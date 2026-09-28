# Evaluation results

Synthetic labeled evaluation. Results do not represent real-world employee behavior.

All input sets are labeled `synthetic: true`.

## Recommendation methods @5

| Method | P@5 | R@5 | NDCG@5 | MAP@5 | Coverage | Diversity |
| --- | --- | --- | --- | --- | --- | --- |
| POPULARITY | 0.933 | 1.000 | 0.985 | 0.963 | 0.500 | 0.761 |
| CONTENT | 0.867 | 0.933 | 0.925 | 0.868 | 0.500 | 0.774 |
| SEMANTIC | 0.933 | 1.000 | 1.000 | 1.000 | 0.500 | 0.761 |
| KG | 0.867 | 0.933 | 0.872 | 0.810 | 0.538 | 0.758 |
| HYBRID | 0.867 | 0.933 | 0.946 | 0.903 | 0.500 | 0.761 |

## Hybrid ablation (NDCG@5 delta vs full)

| Variant | NDCG@5 | delta |
| --- | --- | --- |
| full | 0.946 | 0.000 |
| minus_semantic | 0.929 | -0.017 |
| minus_gap | 0.943 | -0.002 |
| minus_prerequisite | 0.942 | -0.004 |
| minus_difficulty | 0.985 | +0.040 |
| minus_preference | 0.951 | +0.006 |
| minus_collaborative | 0.946 | +0.000 |
| minus_kg | 0.946 | +0.000 |

## Extraction

Precision 1.000, recall 1.000, F1 1.000 on 2 synthetic resumes.

## Skill-gap ranking

NDCG@10 0.978 on 2 synthetic personas.

## Learning path

Prerequisite violations 0.000, coverage 1.000, hours 107.5, efficiency 0.094.

