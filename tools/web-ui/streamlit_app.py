import io
import zipfile
from dataclasses import dataclass
from typing import List, Optional, Tuple

import streamlit as st
from PIL import Image
from streamlit.elements import image as st_image
from streamlit.elements.lib import image_utils, layout_utils
from streamlit_drawable_canvas import st_canvas


@dataclass
class CropBox:
    left: int
    top: int
    right: int
    bottom: int

    def as_tuple(self) -> Tuple[int, int, int, int]:
        return (self.left, self.top, self.right, self.bottom)


def load_images(files) -> List[Tuple[str, Image.Image]]:
    images = []
    for file in files:
        try:
            image = Image.open(file).convert("RGB")
            images.append((file.name, image))
        except Exception:
            st.warning(f"Could not open {file.name}")
    return images


def ensure_streamlit_image_to_url() -> None:
    if hasattr(st_image, "image_to_url"):
        return

    def image_to_url(image, width, clamp, channels, output_format, image_id) -> str:
        layout_config = layout_utils.LayoutConfig(width=width)
        return image_utils.image_to_url(
            image, layout_config, clamp, channels, output_format, image_id
        )

    st_image.image_to_url = image_to_url


def crop_image(image: Image.Image, crop_box: CropBox) -> Image.Image:
    return image.crop(crop_box.as_tuple())


def build_zip(images: List[Tuple[str, Image.Image]], crop_box: CropBox) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename, image in images:
            cropped = crop_image(image, crop_box)
            base, ext = filename.rsplit(".", 1)
            output_name = f"{base}_cropped.{ext}"
            image_bytes = io.BytesIO()
            save_format = image.format if image.format else ext.upper()
            if save_format in {"TIF", "TIFF"}:
                save_format = "TIFF"
            elif save_format not in {"PNG", "JPEG", "JPG", "BMP", "GIF"}:
                save_format = "PNG"
                output_name = f"{base}_cropped.png"
            cropped.save(image_bytes, format=save_format)
            zf.writestr(output_name, image_bytes.getvalue())
    return buffer.getvalue()


def clamp_crop_box(box: CropBox, width: int, height: int) -> CropBox:
    left = max(0, min(box.left, width - 1))
    top = max(0, min(box.top, height - 1))
    right = max(left + 1, min(box.right, width))
    bottom = max(top + 1, min(box.bottom, height))
    return CropBox(left=left, top=top, right=right, bottom=bottom)


def crop_box_from_canvas(canvas_json, width: int, height: int) -> Optional[CropBox]:
    if not canvas_json:
        return None
    objects = canvas_json.get("objects", [])
    if not objects:
        return None
    rect = objects[-1]
    if rect.get("type") != "rect":
        return None
    left = int(rect.get("left", 0))
    top = int(rect.get("top", 0))
    rect_width = int(rect.get("width", 0) * rect.get("scaleX", 1))
    rect_height = int(rect.get("height", 0) * rect.get("scaleY", 1))
    return clamp_crop_box(
        CropBox(left=left, top=top, right=left + rect_width, bottom=top + rect_height),
        width,
        height,
    )


def resize_for_canvas(image: Image.Image, max_size: int = 900) -> Image.Image:
    display = image.copy()
    display.thumbnail((max_size, max_size), Image.LANCZOS)
    return display


def main() -> None:
    st.set_page_config(page_title="Lab Toolkit UI", layout="wide")
    st.title("Lab Toolkit: MultiCropper (Demo)")
    st.write(
        "Upload images, choose a crop box, preview the result, and download all crops as a zip."
    )

    files = st.file_uploader(
        "Upload images",
        type=["png", "jpg", "jpeg", "tif", "tiff", "bmp"],
        accept_multiple_files=True,
    )

    if not files:
        st.info("Upload at least one image to begin.")
        return

    images = load_images(files)
    if not images:
        st.warning("No valid images were loaded.")
        return

    first_name, first_image = images[0]
    width, height = first_image.size
    display_image = resize_for_canvas(first_image)
    display_width, display_height = display_image.size
    scale_x = width / display_width
    scale_y = height / display_height

    ensure_streamlit_image_to_url()
    st.subheader("Crop selection")
    st.write("Draw a rectangle on the image to set the crop area.")
    canvas = st_canvas(
        fill_color="rgba(255, 106, 61, 0.15)",
        stroke_width=2,
        stroke_color="#ff6a3d",
        background_image=display_image,
        update_streamlit=True,
        height=display_height,
        width=display_width,
        drawing_mode="rect",
        key="crop_canvas",
    )

    crop_box = crop_box_from_canvas(canvas.json_data, display_width, display_height)
    if crop_box is None:
        crop_box = CropBox(left=0, top=0, right=display_width, bottom=display_height)

    crop_box = CropBox(
        left=int(crop_box.left * scale_x),
        top=int(crop_box.top * scale_y),
        right=int(crop_box.right * scale_x),
        bottom=int(crop_box.bottom * scale_y),
    )
    crop_box = clamp_crop_box(crop_box, width, height)

    st.subheader("Preview")
    preview = crop_image(first_image, crop_box)
    st.image(preview, caption=f"Preview: {first_name}", use_column_width=True)

    st.subheader("Download")
    zip_bytes = build_zip(images, crop_box)
    st.download_button(
        label="Download cropped images",
        data=zip_bytes,
        file_name="cropped_images.zip",
        mime="application/zip",
    )


if __name__ == "__main__":
    main()
