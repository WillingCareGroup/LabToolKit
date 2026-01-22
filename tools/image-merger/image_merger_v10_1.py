import os
import argparse
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn, TextColumn, BarColumn, TaskProgressColumn
import logging
from pathlib import Path
from typing import Tuple, Optional, List
from dataclasses import dataclass

# Set up logging with rich
from rich.logging import RichHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)]
)


@dataclass
class ImageProcessingTask:
    input_dir: str
    output_dir: str
    grid_size: Tuple[int, int]
    font_size_factor: float
    custom_names: pd.DataFrame
    index: int
    total: int


class ImageProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def convert_16bit_to_8bit(image: Image.Image) -> Image.Image:
        return image.point(lambda i: i * (1 / 256)).convert('RGB')

    def load_image(self, filepath: str) -> Optional[Image.Image]:
        try:
            # Open the file and read the bytes
            with open(filepath, 'rb') as f:
                file_bytes = f.read()

            # Create image from bytes in memory
            from io import BytesIO
            with BytesIO(file_bytes) as bio:
                with Image.open(bio) as image:
                    # Force loading of image data and conversion to RGB
                    if image.mode == 'I;16':
                        converted = self.convert_16bit_to_8bit(image)
                    else:
                        converted = image.convert('RGB')

                    # Create a new copy in memory
                    return converted.copy()

        except OSError as e:
            self.logger.error(f"OS Error loading image '{filepath}': {str(e)}")
            if hasattr(e, 'errno'):
                self.logger.error(f"Error number: {e.errno}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error loading image '{filepath}': {str(e)}")
            return None

    @staticmethod
    def resize_images(images: List[Image.Image], size: Tuple[int, int]) -> List[Image.Image]:
        # Use BILINEAR resampling instead of LANCZOS for better speed
        return [img.resize(size, Image.BILINEAR) for img in images if img is not None]

    @staticmethod
    def draw_text(draw: ImageDraw.Draw, text: str, position: Tuple[int, int], font: ImageFont.FreeTypeFont):
        draw.text(position, text, font=font, fill=(0, 0, 0))

    def create_image_grid(self, task: ImageProcessingTask, progress=None) -> None:
        task_id = progress.add_task(
            f"Processing {os.path.basename(task.input_dir)}",
            total=100
        ) if progress else None

        # Update progress
        if progress:
            progress.update(task_id, advance=10, description="Loading images...")

        images = []
        filenames = []

        # Load and filter images using Path for better path handling
        input_path = Path(task.input_dir)
        for filepath in input_path.glob('*'):
            if filepath.suffix.lower() in {'.jpg', '.jpeg', '.png', '.tif', '.tiff'}:
                image = self.load_image(str(filepath))
                if image:
                    images.append(image)
                    filenames.append(filepath.name)

        if not images:
            self.logger.warning("No valid images found in the input directory.")
            if progress:
                progress.update(task_id, completed=100)
            return

        if progress:
            progress.update(task_id, advance=20, description="Resizing images...")

        # Process images
        size = images[0].size
        images = self.resize_images(images, size)

        grid_width = size[0] * task.grid_size[0]
        grid_height = size[1] * task.grid_size[1]
        grid_image = Image.new('RGB', (grid_width, grid_height), (255, 255, 255))

        if progress:
            progress.update(task_id, advance=20, description="Creating grid...")

        # Setup font
        font_size = int(size[1] * task.font_size_factor)
        try:
            font = ImageFont.truetype('arial.ttf', font_size)
        except IOError:
            try:
                # Try system font as fallback
                font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', font_size)
            except IOError:
                font = ImageFont.load_default()

        draw = ImageDraw.Draw(grid_image)

        if progress:
            progress.update(task_id, advance=20, description="Adding images and labels...")

        # Arrange images in grid
        for i in range(task.grid_size[1]):
            for j in range(task.grid_size[0]):
                index = i * task.grid_size[0] + j
                if index < len(images):
                    x, y = j * size[0], i * size[1]
                    grid_image.paste(images[index], (x, y))
                    name = (
                        task.custom_names.iat[i, j]
                        if task.custom_names is not None and not pd.isna(task.custom_names.iat[i, j])
                        else filenames[index]
                    )
                    self.draw_text(draw, str(name), (x, y), font)

        if progress:
            progress.update(task_id, advance=20, description="Saving grid...")

        # Create output directory if it doesn't exist
        output_path = Path(task.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        output_file = output_path / f"{input_path.name}_grid.png"
        # Save with optimal settings for speed and quality
        grid_image.save(output_file,
                        format='PNG',
                        optimize=False,  # Disable optimization for faster saving
                        compress_level=1)  # Use minimal compression for faster saving

        if progress:
            progress.update(task_id, advance=10, completed=True, description="Complete!")

        self.logger.info(f"Grid image saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Create a grid of images from an Excel file')
    parser.add_argument('--path', type=str, default='.',
                        help='The path where the "BE.xlsx" file is located (default: current directory)')
    args = parser.parse_args()

    base_path = Path(args.path)
    excel_file = base_path / "BE.xlsx"

    if not excel_file.exists():
        logging.error(f"Excel file not found: {excel_file}")
        return

    df = pd.read_excel(excel_file)
    processor = ImageProcessor()

    # Set up rich progress display
    with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
    ) as progress:
        overall_progress = progress.add_task("[cyan]Overall progress", total=len(df))

        with ThreadPoolExecutor() as executor:
            futures = []

            for index, row in df.iterrows():
                input_dir = row.get('input_dir', str(base_path))
                output_dir = row.get('output_dir', str(base_path / 'output'))
                grid_size = tuple(map(int, row['grid_size'].split('x')))
                font_size_factor = row.get('font_size_factor', 0.15)
                layout_file = row['layout_file']

                try:
                    custom_names = pd.read_excel(layout_file, header=None)
                    if custom_names.shape != (grid_size[1], grid_size[0]):
                        logging.warning(
                            f"Layout dimensions mismatch for {input_dir}: "
                            f"Expected {grid_size[0]}x{grid_size[1]}, got {custom_names.shape[1]}x{custom_names.shape[0]}"
                        )
                except Exception as e:
                    logging.error(f"Failed to read layout file {layout_file}: {e}")
                    continue

                task = ImageProcessingTask(
                    input_dir=input_dir,
                    output_dir=output_dir,
                    grid_size=grid_size,
                    font_size_factor=font_size_factor,
                    custom_names=custom_names,
                    index=index,
                    total=len(df)
                )

                future = executor.submit(processor.create_image_grid, task, progress)
                futures.append(future)

            # Wait for all tasks to complete
            for future in as_completed(futures):
                try:
                    future.result()
                    progress.update(overall_progress, advance=1)
                except Exception as e:
                    logging.error(f"Task failed: {e}")


if __name__ == '__main__':
    main()