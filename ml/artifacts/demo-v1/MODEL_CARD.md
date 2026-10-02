# SANKET public isolated-sign starter model

This model was trained by SANKET AI from public isolated ISL video clips.

- Aggregate: vidit031/isl-isolated-40words
- Training sources restricted to INCLUDE and CISLR rows
- Source videos are downloaded during training and are not committed
- Offline feature extractor: MediaPipe 0.10.21 Holistic
- Feature contract: SANKET native 226-D schema
- Model: temporal template baseline
- Evaluation: stratified sample holdout, not signer-disjoint

Do not claim unrestricted ISL translation or signer-independent accuracy from this artifact.

# SANKET AI model card — template-v1

Backend: temporal template baseline  
Vocabulary: friend, hello, hospital, market, school, thank_you  
Samples: 72  
Split mode: stratified_sample_split_no_signer_claim  
Acceptance threshold: 0.177  
Margin threshold: 0.004  
Test top-1: 0.500  
Selective accepted accuracy: 0.500 at coverage 1.000.

## Limitations
This is a finite-vocabulary landmark model. It is not open-vocabulary continuous ISL translation. Metrics are valid only for the data and split documented in evaluation.json.
