# Research Basis and Verified Constraints

This file records sources that materially influence the design. Re-check them as the project evolves.

## 1. Hacktopia 2026
Current Unstop listing describes:
- Round 1 as an online PPT submission,
- evaluation focus on creativity, originality and feasibility,
- top 15 advancing,
- a 24-hour offline grand finale,
- a working prototype of the submitted idea,
- shortlisting also referencing quality and potential impact.

Source:
https://unstop.com/hackathons/hacktopia-2026-pimpri-chinchwad-college-of-engineering-pccoe-pune-1749928/amp

Engineering consequence:
- prioritize a visibly differentiated but demonstrably working vertical slice;
- keep architecture ambitious, but the judge path must be reliable within hackathon constraints.

## 2. ISLRTC official dictionary
ISLRTC is a Government of India institution under the Department of Empowerment of Persons with Disabilities.

Official FAQ states the Indian Sign Language Dictionary contains 10,000 terms and explains that some concepts do not map one-to-one to English words. It also states the dictionary may be used for research, teaching and ISL-related technology provided the data are not resold/used for profiteering and ISLRTC is properly acknowledged.

Sources:
https://islrtc.nic.in/
https://islrtc.nic.in/faq/

Engineering consequence:
- treat ISL as a language, not a word-by-word encoding of English;
- prefer phrase-level approved outputs;
- maintain attribution and license/provenance notes;
- re-check permissions before any commercial productization.

## 3. ISLTranslate
Paper: “ISLTranslate: Dataset for Translating Indian Sign Language” (Joshi, Agrawal, Modi, 2023).

The paper introduces a continuous ISL translation dataset with approximately 31k ISL-English sentence/phrase pairs and benchmarks transformer-based translation.

Source:
https://arxiv.org/abs/2307.05440

Engineering consequence:
- continuous ISL translation is a legitimate research direction;
- full sentence translation is much larger than a small hackathon gesture classifier, so scope claims carefully.

## 4. Speech-to-sign research
“Towards Automatic Speech to Sign Language Generation” explores continuous sign pose generation from speech and an Indian sign language dataset with speech annotations, transcripts and sign videos.

Source:
https://arxiv.org/abs/2106.12790

Engineering consequence:
- speech/text → sign is feasible as a research direction;
- for a 24-hour prototype, curated real sign clips are safer and more linguistically honest than pretending a newly generated avatar is fluent ISL.

## 5. MediaPipe multimodal features
Current MediaPipe Tasks documentation exposes Holistic results including:
- face landmarks,
- pose landmarks,
- world pose landmarks,
- left/right hand landmarks,
- optional face blendshapes.

Face Landmarker documentation exposes 52 blendshape coefficients and live-stream modes.

Sources:
https://ai.google.dev/edge/api/mediapipe/python/mp/tasks/vision/HolisticLandmarkerResult
https://ai.google.dev/edge/api/mediapipe/python/mp/tasks/vision/FaceLandmarkerOptions

Engineering consequence:
- hands + body + non-manual facial features can be extracted using a practical real-time stack rather than full RGB video models.

## 6. 2026 landmark-based ISL recognition evidence
CVPR 2026 workshop paper “Isolated Sign Language Recognition via MediaPipe Landmarks: A Case Study On Indian Sign Language” reports strong performance on one INCLUDE split but far lower performance on CISLR, while using a parameter-efficient landmark-based model.

Source:
https://openaccess.thecvf.com/content/CVPR2026W/MSLR/html/Varanasi_Isolated_Sign_Language_Recognition_via_MediaPipe_Landmarks_A_Case_Study_CVPRW_2026_paper.html

Engineering consequence:
- landmark-based models are viable and efficient;
- cross-dataset/generalization can be hard;
- use signer-independent evaluation and confidence rejection;
- never advertise a single high accuracy number as universal real-world performance.

## 7. 2026 ISL deployment/ethics review
A CVPR 2026 workshop paper on inclusive sign-language recognition in India highlights dataset gaps, privacy/participant disclosure, diversity, licensing and deployment-readiness concerns around ISL datasets including INCLUDE.

Source:
https://openaccess.thecvf.com/content/CVPR2026W/MSLR/papers/Wadhera_Towards_Inclusive_Sign_Language_Recognition_Dataset_Gaps_Ethical_Challenges_and_CVPRW_2026_paper.pdf

Engineering consequence:
- keep consent/provenance metadata;
- do not assume research dataset access equals commercial deployment rights;
- default to not storing raw video.

## 8. ONNX Runtime Web
Official ONNX Runtime documentation states browser inference can improve privacy/offline operation and supports WebAssembly and WebGPU execution paths depending on browser/platform.

Sources:
https://onnxruntime.ai/docs/tutorials/web/
https://onnxruntime.ai/docs/tutorials/web/ep-webgpu.html

Engineering consequence:
- on-device recognition is a strong post-baseline optimization;
- keep WASM/CPU fallback because WebGPU availability varies;
- do not make WebGPU the only supported path.

---

# Research rules for future updates
When adding a paper/dataset/tool:
1. record title and canonical source,
2. record publication/year,
3. record what it actually proves,
4. record license/access limitations,
5. state the exact engineering decision it changes,
6. never copy benchmark numbers into marketing without reproducing/evaluating the conditions.
