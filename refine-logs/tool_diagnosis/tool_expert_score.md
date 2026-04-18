# Diagnosis: tool_expert_score

Total calls: 1078

## Failure mode (manual analysis — fill in)

_TBD: wrong trigger / unclear output / VLM misreads / mixed_

## Wins (agent better than Direct)

- `D5c_0119` [D5c] label=1 agent=0.99 direct=0.02 Δerr=-0.970
  > The query image displays prominent bright, branching structures (likely vessels or lesions) that are absent in the uniform reference liver slices. The expert model confirms this with a very high anomaly score (98.8) and rank (0.90), strongl

- `D7_0178` [D7] label=1 agent=0.97 direct=0.02 Δerr=-0.950
  > The query image features a horse-drawn carriage on a road, which is an unexpected and out-of-place object in a typical modern traffic scene, confirmed by a strong anomaly signal from the expert model.

- `D5c_0101` [D5c] label=1 agent=0.97 direct=0.02 Δerr=-0.950
  > The query image contains distinct hypodense lesions within the liver parenchyma, which are not present in the normal reference images. The expert model confirms this with a high anomaly score (97.17) and rank (0.90), indicating a clear devi

- `D5c_0176` [D5c] label=1 agent=0.97 direct=0.02 Δerr=-0.950
  > The query image displays a small, isolated bright region, which is structurally and texturally inconsistent with the larger, complex liver parenchyma seen in the normal reference images. The expert anomaly score (0.97) strongly supports thi

- `D5c_0144` [D5c] label=1 agent=0.97 direct=0.02 Δerr=-0.950
  > The subspacead expert score indicates a strong anomaly signal (normalized_rank=0.9676), confirming the presence of a significant deviation from normal liver parenchyma, consistent with a focal lesion.

- `D5c_0124` [D5c] label=1 agent=0.96 direct=0.02 Δerr=-0.940
  > The query image contains a distinct hypodense lesion within the liver parenchyma, which is a clear deviation from the uniform texture of the normal reference images. The expert model strongly corroborates this finding with a high anomaly sc

- `D5c_0164` [D5c] label=1 agent=0.96 direct=0.02 Δerr=-0.940
  > The query image contains a clear hypodense lesion, confirmed by a high subspacead anomaly score (0.96) and visual inspection of the hotspot, indicating liver pathology.

- `D5c_0104` [D5c] label=1 agent=0.96 direct=0.02 Δerr=-0.940
  > The subspacead expert score indicates a strong anomaly signal (normalized rank 0.956 > 0.80), confirming the presence of a focal lesion (the dark circular region) in the liver parenchyma, which is inconsistent with the normal reference imag

- `D8_0096` [D8] label=1 agent=0.95 direct=0.02 Δerr=-0.930
  > The query image shows a person running (indicated by motion blur) in a pedestrian walkway where normal behavior is walking. This is a clear violation of the 'normal' behavior defined for this domain, making it a strong anomaly.

- `D5c_0122` [D5c] label=1 agent=0.95 direct=0.02 Δerr=-0.930
  > The subspacead expert detected a strong anomaly signal (rank 0.91, score 101.8), confirming the presence of a significant structural deviation (likely a lesion or artifact) in the liver compared to the normal reference images.

## Losses (agent worse than Direct)

- `D5c_0027` [D5c] label=0 agent=0.95 direct=0.02 Δerr=+0.930
  > The expert model detected a strong anomaly signal (rank 0.946), and visual inspection confirms the query contains two distinct regions while normal references show a single contiguous region, indicating a structural anomaly.

- `D5c_0076` [D5c] label=0 agent=0.95 direct=0.02 Δerr=+0.930
  > The query image is almost completely black, containing only a tiny speck, whereas all reference images show a complete liver cross-section. This indicates the liver is missing or the image is corrupted, which is a definitive anomaly.

- `D5d_0015` [D5d] label=0 agent=0.95 direct=0.02 Δerr=+0.930
  > The query image contains a large, dark, non-mucosal object or lesion that is completely absent in all normal reference images, which show healthy pink tissue. This represents a clear and significant pathological or foreign body anomaly.

- `D5d_0079` [D5d] label=0 agent=0.95 direct=0.02 Δerr=+0.930
  > The query image displays a distinct, raised polypoid lesion, which is a clear pathological anomaly compared to the smooth, normal mucosa described in the reference images. The expert model's low score is incorrect in this context.

- `D5d_0049` [D5d] label=0 agent=0.95 direct=0.02 Δerr=+0.930
  > Despite the low expert score, visual inspection clearly shows a raised, nodular polypoid lesion in the center of the query image, which is a pathological finding. The reference images show normal, flat mucosa. This structural abnormality co

- `D5c_0028` [D5c] label=0 agent=0.96 direct=0.02 Δerr=+0.940
  > The query image contains a distinct focal hyperdense lesion, which is a clear deviation from the uniform liver parenchyma seen in the normal references. This is confirmed by the subspacead expert score (rank 0.96), indicating a strong anoma

- `D5c_0046` [D5c] label=0 agent=0.98 direct=0.02 Δerr=+0.960
  > The subspacead expert score indicates a very strong anomaly signal (normalized rank 0.98), confirming that the query image contains a significant deviation from the normal liver parenchyma seen in the reference images, consistent with a foc

- `D5c_0074` [D5c] label=0 agent=0.98 direct=0.02 Δerr=+0.960
  > The query image displays a small, thin, elongated structure, which is structurally inconsistent with the large, substantial liver cross-sections seen in all four reference images. The expert model confirms this with a strong anomaly signal 

- `D5c_0084` [D5c] label=0 agent=0.99 direct=0.02 Δerr=+0.970
  > The query image displays distinct hypodense lesions (dark holes) within the liver tissue, which is a clear deviation from the uniform parenchyma seen in the normal reference images. The expert model confirms this with a very high anomaly sc

- `D5c_0064` [D5c] label=0 agent=0.99 direct=0.02 Δerr=+0.970
  > The query image contains distinct hypodense lesions within the liver parenchyma, which are not present in the normal reference images. The expert model confirms this with a very high anomaly score (rank 0.989), indicating a clear deviation 
