# Live API Stress Results

Date: 2026-05-18
Target: `https://gauntlet-week1.onrender.com`

The deployed Sprint 1 API was exercised with 25 black-box checks plus cleanup
deletes. All first 25 checks passed.

```text
SUMMARY first_25_passed=25/25 total_failures=0 total_checks=27
```

Checks covered:

1. `GET /health`
2. `GET /docs`
3. `GET /openapi.json`
4. `GET /api/v1/tasks`
5. `GET /api/v1/tasks/stats`
6. create minimal task
7. create full task
8. get created task
9. full update task
10. patch status
11. filter by status
12. filter by priority
13. filter by assignee
14. filter by tag
15. pagination
16. sort by title
17. invalid sort fallback
18. missing title validation
19. empty title validation
20. title too long validation
21. invalid status validation
22. invalid priority validation
23. too many tags validation
24. invalid date validation
25. malformed JSON validation

Cleanup:

- deleted the two red-team tasks created by the run

Important operational observation:

- Many requests took roughly 20-24 seconds on Render Free. That is acceptable
  for Week 1 public proof but must be disclosed as free-tier cold-start and
  low-resource behavior.
