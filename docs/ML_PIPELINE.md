# ML Pipeline

1. Open **Collect data** in the web app.
2. Choose a supported label and pseudonymous signer ID.
3. Collect multiple takes with explicit consent. Only landmark sequences are saved.
4. Use multiple signers and varied lighting/backgrounds.
5. Run `python -m ml.training.train_template`.
6. The trainer performs signer-disjoint evaluation when at least three signers are available. With fewer signers, the evaluation report explicitly records the limitation.
7. Artifacts are written to `ml/artifacts/demo-v1/`: `model.npz`, `manifest.json`, `evaluation.json`, `MODEL_CARD.md`.
8. Reload the backend model using `POST /api/model/reload` or restart the API.

The baseline is temporal: sequences are resampled to 48 frames and first-order velocity is appended. One class template is learned from training takes and compared against the live rolling sequence. This is deliberately small and CPU-friendly. It can later be replaced by a GRU/Transformer without changing the WebSocket/UI contract.

Never report metrics outside the vocabulary, signers, split and conditions documented in `evaluation.json`.
