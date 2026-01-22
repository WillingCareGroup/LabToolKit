# Streamlit Demo UI

A small Streamlit web UI that demonstrates the MultiCropper workflow with a
simple upload + crop + download flow.

## Run

```bash
pip install streamlit pillow
streamlit run tools/web-ui/streamlit_app.py
```

## Notes

- This demo uses manual crop coordinates to keep dependencies light.
- It processes uploads in memory and returns a zip of cropped images.
