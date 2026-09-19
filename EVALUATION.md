# RepairGraph 2.0 Evaluation

## Evaluation goals

RepairGraph is evaluated as a software-maintenance system, not merely as an LLM prompt.

### Repair metrics

- reproduction success rate
- repair success rate
- regression-free repair rate
- mean repair attempts
- first-attempt success rate
- reflection recovery rate

### Repository intelligence

- relevant-file hit rate
- Recall@K / MRR can be added for larger localization datasets

### Safety

- false-repair rate on healthy repositories
- secret/path/workflow block rate
- unsafe-action block rate
- security false-positive rate

### Reliability and economics

- agent-error rate
- provider retry rate
- structured-output retry rate
- LLM calls per case
- input/output tokens
- P50 end-to-end latency
- P95 end-to-end latency
- per-stage latency

## Included deterministic suite

`python -m evals.run_evals --provider mock`

The suite currently contains:

1. booking deadline regression, expected repair
2. Nigerian phone normalization regression, expected repair
3. healthy repository diagnostic request, expected no repair

The mock provider exists to validate graph mechanics deterministically. Its scores must not be presented as production-model intelligence.

## Real-provider benchmark

Run:

```powershell
python -m evals.run_evals --provider cloudflare
```

Save the JSON output and use those values for model-performance claims. Compare providers only on the same case set and the same code revision.
