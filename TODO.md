# TODO List

## Completed Tasks ✅

- [x] Implement async system-wide vector index rebuild for all users without admin restrictions
- [x] Add concurrency control (limit 3 concurrent users) to prevent resource overload
- [x] Implement disk persistence for rebuild task states to survive backend restarts
- [x] Fix import error (NameError: os not defined) in main.py
- [x] Validate retrieval functionality works after rebuild (queries return sources)
- [x] Test end-to-end flow: login → rebuild_all → query → verify sources returned
- [x] Implement time-based tagging for documents (days since 2026-01-01)
- [x] Add time range filtering support in query API
- [x] Update frontend with time range selector UI
- [x] Integrate time filtering with PPRFANNS range search algorithm
- [x] Test time tag calculation and component initialization
- [x] Modify frontend UI: show time range inputs directly in hybrid search mode instead of scalar filter button
- [x] Refine UI: pure vector search shows no extra buttons, hybrid search shows time range inputs directly

## Optional Future Enhancements

- [ ] Add task cancellation endpoint for running rebuild tasks
- [ ] Add progress metrics/monitoring for rebuild operations
- [ ] Optimize rebuild performance if needed (currently limited to 3 concurrent users)
- [ ] Add rebuild status endpoint for individual users to check progress
- [ ] Add validation for time range inputs in frontend
- [ ] Add preset time ranges (last 7 days, last 30 days, etc.)