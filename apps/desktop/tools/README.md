# Desktop tooling

Scripts that produce the model files bundled in
[`childshield/models/`](../childshield/models). They are **not** part of
the runtime — you only need to run them if you want to regenerate the
ONNX files from their public sources.

## `convert_age_model.py`

Re-exports the age estimator (`age_vit.onnx`).

```bash
python -m venv .venv-convert
source .venv-convert/bin/activate
pip install 'optimum[onnxruntime]' onnxconverter-common
python tools/convert_age_model.py
```

This writes a new `childshield/models/age_vit.onnx` (~85 MB).

## Face detector

`det_10g.onnx` comes from [InsightFace](https://github.com/deepinsight/insightface)'s
`buffalo_l` pack. Reproducible by running:

```python
from insightface.app import FaceAnalysis
FaceAnalysis(allowed_modules=["detection"]).prepare(ctx_id=-1)
# Model is downloaded to ~/.insightface/models/buffalo_l/det_10g.onnx
```

then copying that file into `childshield/models/`.
