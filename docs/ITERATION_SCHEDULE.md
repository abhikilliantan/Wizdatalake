# OpenHands local-dev schedule (GitHub push optional)

**Mode:** `LOCAL_DEV=1` — implement on disk; **no push / no PR required**.

| Iter | Issue | Title |
|------|-------|-------|
| I1 | #14 | D10 Flat file ingestion |
| I2 | #16 | D11 Redpanda topics + producer |
| I3 | #17 | D12 Streaming consumer flush |
| I4 | #18 | D13 Stream load ≥1000 |
| I5 | #19 | D14 DB extract Postgres |
| I6 | #21 | D15 MySQL + CDC spike |
| I7 | #23 | Hardening start |
| I8 | #27 | UAT pack |

Done signal: `.openhands/iterations/IN.done`

```bash
./scripts/start-openhands.sh
LOCAL_DEV=1 ./scripts/openhands-watchdog.sh run
```

Canvas: http://localhost:8010/canvas
