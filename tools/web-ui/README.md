# Streamlit Demo UI

A small Streamlit web UI that demonstrates the MultiCropper workflow with a
simple upload + crop + download flow.

## Run

```bash
pip install streamlit pillow streamlit-drawable-canvas
streamlit run tools/web-ui/streamlit_app.py
```

## Notes

- Draw a rectangle on the first image to set the crop area.
- It processes uploads in memory and returns a zip of cropped images.
