# Case studies: agent wins vs direct (top 5)

## WIN: D9_0110 (domain=D9, gt=1)

- **Direct**: score=0.010 rationale='The query image displays a bottle of cherry juice with a matching label and liquid color, consistent with the reference state shown in the first image. All components are present and correctly arrange'
- **Agent**: score=1.000 rationale='The query image has a cherry label and red liquid, whereas all reference images have banana labels and white liquid. This mismatch in label identity and liquid color constitutes a logical anomaly.'
  turns=1 tools=[] confidence=100
  advantage_score: +0.990

## WIN: D9_0113 (domain=D9, gt=1)

- **Direct**: score=0.010 rationale='The query image shows a bottle of cherry juice with a matching label and liquid color, consistent with the reference image. All components are present and correctly arranged.'
- **Agent**: score=1.000 rationale='The query image has a cherry label and red liquid, whereas all reference images have banana labels and light-colored liquid. This is a clear logical anomaly (wrong label and liquid color pairing).'
  turns=1 tools=[] confidence=100
  advantage_score: +0.990

## WIN: D5c_0119 (domain=D5c, gt=1)

- **Direct**: score=0.020 rationale='The query image displays a liver cross-section with uniform parenchymal texture and density consistent with the reference images. There are no visible focal lesions, hypodense or hyperdense areas, or '
- **Agent**: score=0.990 rationale='The query image displays prominent bright, branching structures (likely vessels or lesions) that are absent in the uniform reference liver slices. The expert model confirms this with a very high anoma'
  turns=2 tools=['tool_expert_score'] confidence=98
  advantage_score: +0.970

## WIN: D9_0115 (domain=D9, gt=1)

- **Direct**: score=0.020 rationale='The image shows a juice bottle with a yellow liquid and a peach icon on the label. This represents a valid variation of the product (different flavor) compared to the reference cherry juice, with no s'
- **Agent**: score=0.980 rationale='The query bottle has a cherry label and dark red liquid, whereas all reference bottles have banana/peach labels with light-colored liquid. This mismatch in label icon and liquid color constitutes a cl'
  turns=1 tools=[] confidence=95
  advantage_score: +0.960

## WIN: D5c_0101 (domain=D5c, gt=1)

- **Direct**: score=0.020 rationale='The query image displays a liver cross-section with uniform parenchymal texture and density consistent with the provided normal reference images. There are no visible focal hypodense or hyperdense les'
- **Agent**: score=0.970 rationale='The query image contains distinct hypodense lesions within the liver parenchyma, which are not present in the normal reference images. The expert model confirms this with a high anomaly score (97.17) '
  turns=2 tools=['tool_expert_score'] confidence=98
  advantage_score: +0.950


# Case studies: agent losses (top 5)

## LOSS: D8_0143 (domain=D8, gt=1)

- **Direct**: score=0.950 rationale='A red bag and a white bag are lying on the grass in the foreground, which are out-of-place objects not present in the normal reference state.'
- **Agent**: score=0.500 rationale='json parse failed'
  turns=5 tools=['tool_reference_profiler', 'tool_expert_score', 'tool_expert_score', 'tool_zoom_bbox'] confidence=0
  advantage_score: -0.450

## LOSS: D6_0126 (domain=D6, gt=1)

- **Direct**: score=0.980 rationale='The query image shows a significant expansion of the residential housing development in the bottom-right quadrant compared to the reference image. Specifically, a new row of houses and associated road'
- **Agent**: score=0.500 rationale='json parse failed'
  turns=5 tools=['tool_image_diff', 'tool_side_by_side', 'tool_reference_profiler', 'tool_patch_grid'] confidence=0
  advantage_score: -0.480

## LOSS: D5_0059 (domain=D5, gt=0)

- **Direct**: score=0.050 rationale='The lesion exhibits a symmetric, oval shape with a relatively uniform light brown color and a regular pigment network. The borders are well-defined and smooth, lacking the irregularity, asymmetry, or '
- **Agent**: score=0.550 rationale='The query lesion shows some irregularity in borders and color variation, but the expert anomaly score was only moderate (0.53). The visual features are ambiguous - not clearly malignant but not perfec'
  turns=4 tools=['tool_expert_score', 'tool_hotspot_cropper', 'tool_side_by_side'] confidence=65
  advantage_score: -0.500

## LOSS: D10_0050 (domain=D10, gt=0)

- **Direct**: score=0.020 rationale='The query image shows a rectangular chewing gum piece with a consistent surface texture and shape that matches the reference images. There are no visible defects such as cracks, chips, or foreign incl'
- **Agent**: score=0.550 rationale='The query shows moderate anomaly signals: subspacead score of 0.486, hotspot indicating irregular edge, and 7.64% pixel difference from reference. These suggest a possible defect (edge irregularity or'
  turns=5 tools=['tool_expert_score', 'tool_hotspot_cropper', 'tool_side_by_side', 'tool_image_diff'] confidence=75
  advantage_score: -0.530

## LOSS: D2_0004 (domain=D2, gt=0)

- **Direct**: score=0.020 rationale='The query image shows the front face of the product, which is consistent with the packaging seen in the reference images (which show the back and side). The packaging is intact, the label is clear, an'
- **Agent**: score=0.550 rationale='The query image shows a green snack package with potential crumpling/deformation at the bottom corner, detected as a moderate anomaly by subspacead. While not a severe defect, the deformation suggests'
  turns=5 tools=['tool_reference_profiler', 'tool_expert_score', 'tool_hotspot_cropper', 'tool_side_by_side'] confidence=70
  advantage_score: -0.530

