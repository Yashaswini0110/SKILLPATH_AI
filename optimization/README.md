# Learning-path optimization

Phase 13 emits a topological candidate sequence.
Phase 14 selects a feasible subset with OR-Tools CP-SAT and compares
greedy and topological baselines.

Constraints: prerequisites, weekly hours, deadline, unique resources.

```text
GET /api/v1/learning-paths?method=ORTOOLS
```

The Path page groups those steps as Learn first / Core / Later. This
package only chooses which skills fit the hour budget.
