import os
import argparse
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def convert_16bit_to_8bit(image):
    return image.point(lambda i: i * (1 / 256)).convert('RGB')


def load_image(filepath):
    try:
        image = Image.open(filepath)
        if image.mode == 'I;16':
            image = convert_16bit_to_8bit(image)
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        return image
    except Exception as e:
        logging.error(f"Failed to load image '{filepath}': {str(e)}")
        return None


def resize_images(images, size):
    return [img.resize(size, Image.LANCZOS) for img in images]


def draw_text(draw, text, position, font):
    draw.text(position, text, font=font, fill=(0, 0, 0))


def create_image_grid(input_dir, output_dir, grid_size=(12, 8), font_size_factor=0.15, custom_names=None):
    images = []
    filenames = []

    # Load and filter images
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.tif', '.tiff')):
            image = load_image(os.path.join(input_dir, filename))
            if image:
                images.append(image)
                filenames.append(filename)

    if not images:
        logging.warning("No valid images found in the input directory.")
        return

    size = images[0].size
    images = resize_images(images, size)

    grid_width = size[0] * grid_size[0]
    grid_height = size[1] * grid_size[1]
    grid_image = Image.new('RGB', (grid_width, grid_height), (255, 255, 255))

    font_size = int(size[1] * font_size_factor)
    try:
        font = ImageFont.truetype('arial.ttf', font_size)
    except IOError:
        font = ImageFont.load_default()

    draw = ImageDraw.Draw(grid_image)

    # Arrange images in grid
    for i in range(grid_size[1]):
        for j in range(grid_size[0]):
            index = i * grid_size[0] + j
            if index < len(images):
                x, y = j * size[0], i * size[1]
                grid_image.paste(images[index], (x, y))
                name = custom_names.iat[i, j] if custom_names is not None and not pd.isna(custom_names.iat[i, j]) else \
                filenames[index]
                draw_text(draw, name, (x, y), font)

    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, os.path.basename(input_dir) + '_grid.png')
    grid_image.save(output_file)
    logging.info(f"Grid image saved to {output_file}")


def check_excel_data(df):
    valid = True
    for _, row in df.iterrows():
        input_dir = row['input_dir']
        grid_size = tuple(map(int, row['grid_size'].split('x')))
        layout_file = row['layout_file']
        custom_names = pd.read_excel(layout_file, header=None)
        if custom_names.shape[0] != grid_size[1] or custom_names.shape[1] != grid_size[0]:
            logging.warning(
                f"Warning: Layout file dimensions for {input_dir} ({custom_names.shape[1]}x{custom_names.shape[0]}) do not match input value ({grid_size[0]}x{grid_size[1]}).")
            valid = False
    return valid


def process_image(task):
    index, row = task
    input_dir = row['input_dir']
    output_dir = row['output_dir']
    grid_size = tuple(map(int, row['grid_size'].split('x')))
    font_size_factor = row['font_size_factor']
    layout_file = row['layout_file']
    custom_names = pd.read_excel(layout_file, header=None)

    create_image_grid(input_dir, output_dir, grid_size=grid_size, font_size_factor=font_size_factor,
                      custom_names=custom_names)
    return f"{index + 1}/{total_rows} {os.path.basename(input_dir)} finished."


def read_excel_file_and_process_images_multithreaded(user_provided_path):
    global total_rows
    excel_file = os.path.join(user_provided_path, "BE.xlsx")
    df = pd.read_excel(excel_file)
    total_rows = len(df)
    if not check_excel_data(df):
        logging.error("Please fix the issues in the Excel file before proceeding.")
        return

    tasks = [(index, row) for index, row in df.iterrows()]
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(process_image, task): task for task in tasks}
        for future in tqdm(as_completed(futures), total=total_rows, desc="Processing"):
            logging.info(future.result())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create a grid of images from an Excel file')
    parser.add_argument('user_provided_path', type=str, help='The path where the "BE.xlsx" file is located')
    args = parser.parse_args()
    read_excel_file_and_process_images_multithreaded(args.user_provided_path)
