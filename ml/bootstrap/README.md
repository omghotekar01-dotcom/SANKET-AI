# Bootstrap 50-word recognizer

SANKET AI can use an external pretrained model as a **bootstrap fallback** before a team-specific model has been trained.

Source project:
- Kartik Singh, `Real-time-Indic-Sign-language-to-speech-translator`
- Upstream repository: `Kartik200428/Real-time-Indic-Sign-language-to-speech-translator`
- Pinned upstream commit: `99ed8ffc47ccf3106d498e704f5c1b7e547758d7`
- License: MIT

The model is **not claimed as a SANKET-trained model**. Its original project states that it was trained on the upstream team's personally recorded ISL sequences. SANKET displays it as a bootstrap model and allows a locally trained SANKET model to replace it automatically.

The downloaded binary is intentionally not committed to this repository. `scripts/install_bootstrap.py` retrieves the exact pinned binary and verifies the upstream Git blob hash.

Feature contract:
- 30 temporal frames
- 33 pose landmarks × 4 values
- 40 selected face landmarks × 3 values, nose-relative
- 21 left-hand landmarks × 3 values, wrist-relative
- 21 right-hand landmarks × 3 values, wrist-relative
- total: 378 values/frame

See `THIRD_PARTY_NOTICES.md` for attribution and license information.
