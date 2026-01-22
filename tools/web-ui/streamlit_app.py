import io
import zipfile
from dataclasses import dataclass
from typing import List, Tuple

import streamlit as st
from PIL import Image


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
            image = Image.open(file)
            images.append((file.name, image))
        except Exception:
            st.warning(f"Could not open {file.name}")
    return images


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
            cropped.save(image_bytes, format=save_format)
            zf.writestr(output_name, image_bytes.getvalue())
    return buffer.getvalue()


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

    st.subheader("Crop settings")
    col_left, col_top, col_right, col_bottom = st.columns(4)
    with col_left:
        left = st.number_input("Left", min_value=0, max_value=width - 1, value=0)
    with col_top:
        top = st.number_input("Top", min_value=0, max_value=height - 1, value=0)
    with col_right:
        right = st.number_input(
            "Right", min_value=left + 1, max_value=width, value=width
        )
    with col_bottom:
        bottom = st.number_input(
            "Bottom", min_value=top + 1, max_value=height, value=height
        )

    crop_box = CropBox(left=left, top=top, right=right, bottom=bottom)

    st.subheader("Preview")
    preview = crop_image(first_image, crop_box)
    st.image(preview, caption=f"Preview: {first_name}", use_column_width=True)

    st.subheader("Download")
    if st.button("Create zip"):
        zip_bytes = build_zip(images, crop_box)
        st.download_button(
            label="Download cropped images",
            data=zip_bytes,
            file_name="cropped_images.zip",
            mime="application/zip",
        )


if __name__ == "__main__":
    main()
