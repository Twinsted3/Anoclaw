# Diagnosis: tool_segment_and_count

Total calls: 1

## Failure mode (manual analysis — fill in)

_TBD: wrong trigger / unclear output / VLM misreads / mixed_

## Wins (agent better than Direct)

- `D6_0094` [D6] label=1 agent=0.75 direct=0.98 Δerr=+0.230
  > The image_diff showed 46.37% change and segment_and_count showed 25% of cells changed with significant differences. In bi-temporal building change detection, such substantial changes indicate building-level anomalies like new construction, 

## Losses (agent worse than Direct)

- `D6_0094` [D6] label=1 agent=0.75 direct=0.98 Δerr=+0.230
  > The image_diff showed 46.37% change and segment_and_count showed 25% of cells changed with significant differences. In bi-temporal building change detection, such substantial changes indicate building-level anomalies like new construction, 
