# Diagnosis: tool_domain_knowledge

Total calls: 4

## Failure mode (manual analysis — fill in)

_TBD: wrong trigger / unclear output / VLM misreads / mixed_

## Wins (agent better than Direct)

- `D8_0094` [D8] label=1 agent=0.95 direct=0.95 Δerr=+0.000
  > The query image shows a person sitting on the grass with a red bag, which is confirmed as anomalous behavior per domain definition. Normal behavior requires pedestrians to be walking at normal pace, and sitting is a static posture that viol

- `D2_0002` [D2] label=0 agent=0.15 direct=0.02 Δerr=+0.130
  > The query image shows a different text variant (English warning vs Chinese/8mg) which is an intentional design difference for regional markets, not a physical defect. The weak subspacead signal (rank 0.146) and domain knowledge confirm this

- `D8_0052` [D8] label=0 agent=0.75 direct=0.02 Δerr=+0.730
  > The query image shows a person standing still near a pillar while others walk by, which domain knowledge identifies as anomalous loitering behavior. This deviation from normal pedestrian flow makes the scene anomalous.

- `D5_0003` [D5] label=0 agent=0.92 direct=0.05 Δerr=+0.870
  > Although the statistical anomaly score was low, the domain-specific analysis confirmed the presence of key malignant features (asymmetry, irregular borders, color variegation) that are absent in the benign reference images. These features s

## Losses (agent worse than Direct)

- `D8_0094` [D8] label=1 agent=0.95 direct=0.95 Δerr=+0.000
  > The query image shows a person sitting on the grass with a red bag, which is confirmed as anomalous behavior per domain definition. Normal behavior requires pedestrians to be walking at normal pace, and sitting is a static posture that viol

- `D2_0002` [D2] label=0 agent=0.15 direct=0.02 Δerr=+0.130
  > The query image shows a different text variant (English warning vs Chinese/8mg) which is an intentional design difference for regional markets, not a physical defect. The weak subspacead signal (rank 0.146) and domain knowledge confirm this

- `D8_0052` [D8] label=0 agent=0.75 direct=0.02 Δerr=+0.730
  > The query image shows a person standing still near a pillar while others walk by, which domain knowledge identifies as anomalous loitering behavior. This deviation from normal pedestrian flow makes the scene anomalous.

- `D5_0003` [D5] label=0 agent=0.92 direct=0.05 Δerr=+0.870
  > Although the statistical anomaly score was low, the domain-specific analysis confirmed the presence of key malignant features (asymmetry, irregular borders, color variegation) that are absent in the benign reference images. These features s
