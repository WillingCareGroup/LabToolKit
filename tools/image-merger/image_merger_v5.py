import os
import argparse
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from concurrent.futures import ThreadPoolExecutor
from alive_progress import alive_bar
from queue import Queue

def create_image_grid(input_dir, output_dir, grid_size=(12, 8), font_size_factor=0.15, custom_names=None):
    # Read input images from directory
    images = []
    filenames = []
    for filename in os.listdir(input_dir):
        if filename.endswith('.jpg') or filename.endswith('.png') or filename.endswith('.tif'):
            try:
                image = Image.open(os.path.join(input_dir, filename))
                images.append(image)
                filenames.append(filename)
            except Exception as e:
                print(f"Failed to load image '{filename}': {str(e)}")

    # Resize all images to the same size
    size = images[0].size
    for i in range(len(images)):
        images[i] = images[i].resize(size)

    # Create a new image for the grid
    grid_width = size[0] * grid_size[0]
    grid_height = size[1] * grid_size[1]

    grid_image = Image.new('RGB', (grid_width, grid_height))

    # Create a font and drawing context for the custom names
    font_size = int(size[1] * font_size_factor)
    font = ImageFont.truetype('arial.ttf', font_size)
    draw = ImageDraw.Draw(grid_image)

    # Paste the images into the grid and overlay custom names
    for i in range(grid_size[1]):
        for j in range(grid_size[0]):
            index = i * grid_size[0] + j
            if index < len(images):
                image = images[index]
                if custom_names is not None:
                    name = custom_names.iat[i, j] if not pd.isna(custom_names.iat[i, j]) else filenames[index]
                else:
                    name = filenames[index]
                grid_image.paste(image, (j * size[0], i * size[1]))
                draw.text((j * size[0], i * size[1]), name, font=font, fill=(255, 255, 255))

    # Save the grid image to the output directory
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, os.path.basename(input_dir) + '_grid.jpg')
    grid_image.save(output_file)


def check_excel_data(df):
    valid = True
    for index, row in df.iterrows():
        input_dir = row['input_dir']
        grid_size = tuple(map(int, row['grid_size'].split('x')))
        layout_file = row['layout_file']
        custom_names = pd.read_excel(layout_file, header=None)

        if custom_names.shape[0] != grid_size[1] or custom_names.shape[1] != grid_size[0]:
            print(f"Warning: The dimension displayed in layout file for {input_dir} (column: {custom_names.shape[1]} x Row: {custom_names.shape[0]}) does not match match input value (Column: {grid_size[0]} x Row: {grid_size[1]}).")
            valid = False
    return valid

def process_image(task, queue):
    index, row = task
    input_dir = row['input_dir']
    output_dir = row['output_dir']
    grid_size = tuple(map(int, row['grid_size'].split('x')))
    font_size_factor = row['font_size_factor']
    layout_file = row['layout_file']

    custom_names = pd.read_excel(layout_file, header=None)

    create_image_grid(input_dir, output_dir, grid_size=grid_size, font_size_factor=font_size_factor, custom_names=custom_names)

    queue.put(1)
    return f"{index + 1}/{total_rows}  {os.path.basename(input_dir)} finished."

def read_excel_file_and_process_images_multithreaded(user_provided_path):
    global total_rows
    excel_file = os.path.join(user_provided_path, "BE.xlsx")
    df = pd.read_excel(excel_file)
    total_rows = len(df)

    if not check_excel_data(df):
        print("Please fix the issues in the Excel file before proceeding.")
        return

    tasks = [(index, row) for index, row in df.iterrows()]

    with ThreadPoolExecutor() as executor:
        progress_queue = Queue()

        def wrapped_process_image(task):
            result = process_image(task, progress_queue)
            return result

        with alive_bar(total_rows, title='Overall Progress') as outer_bar:
            futures = [executor.submit(wrapped_process_image, task) for task in tasks]

            completed_tasks = 0
            while completed_tasks < total_rows:
                outer_bar()
                progress_queue.get()
                completed_tasks += 1

    for result in futures:
        print(result.result())


if __name__ == '__main__':
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Create a grid of images from an Excel file')
    parser.add_argument('user_provided_path', type=str,
                        help='The path where the "BE.xlsx" file is located')
    args = parser.parse_args()

    # Process images using the Excel file
    read_excel_file_and_process_images_multithreaded(args.user_provided_path)
