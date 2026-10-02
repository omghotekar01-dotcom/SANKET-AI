# Judge Q&A — engineering answers

**Is this just gesture recognition?**  
No. The runtime feature schema combines both hands, selected upper-body pose, selected face/non-manual landmarks and motion over a temporal window. The finite demo vocabulary is intentionally scoped.

**What if it is uncertain?**  
Tracking quality, motion, calibrated probability, top-1/top-2 margin and temporal stability gate every accepted token. Weak evidence requests a repeat.

**How many signs / what accuracy?**  
Read the loaded artifact's `manifest.json` and `evaluation.json`. Do not quote a number if the model is not loaded/evaluated.

**Does it save my face/video?**  
Normal interpretation does not write raw frames. Dataset collection stores landmarks only and requires explicit consent.

**Can it work offline?**  
Once dependencies, the MediaPipe package, trained model and verified local clips are installed, core interpretation is local. Browser speech-recognition availability varies; typed input is always available.

**Can it call emergency services?**  
No. Emergency mode communicates urgent needs; it does not guarantee dispatch.
