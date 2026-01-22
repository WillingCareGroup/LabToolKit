import os
import argparse
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from concurrent.futures import ThreadPoolExecutor
from alive_progress import alive_bar
from queue import Queue

def convert_16bit_to_8bit(image):
    return image.point(lambda i: i * (1/256)).convert('RGB')

def create_image_grid(input_dir, output_dir, grid_size=(12, 8), font_size_factor=0.15, custom_names=None, progress_bar=None):
    images = []
    filenames = []
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.tif', '.tiff')):
            try:
                image = Image.open(os.path.join(input_dir, filename))
                if image.mode == 'I;16':
                    image = convert_16bit_to_8bit(image)
                elif image.mode != 'RGB':
                    image = image.convert('RGB')
                images.append(image)
                filenames.append(filename)
            except Exception as e:
                print(f"Failed to load image '{filename}': {str(e)}")

    if not images:
        print("No valid images found in the input directory.")
        return

    size = images[0].size
    for i in range(len(images)):
        images[i] = images[i].resize(size, Image.LANCZOS)

    grid_width = size[0] * grid_size[0]
    grid_height = size[1] * grid_size[1]
    grid_image = Image.new('RGB', (grid_width, grid_height), (255, 255, 255))

    font_size = int(size[1] * font_size_factor)
    try:
        font = ImageFont.truetype('arial.ttf', font_size)
    except IOError:
        font = ImageFont.load_default()
    draw = ImageDraw.Draw(grid_image)

    for i in range(grid_size[1]):
        for j in range(grid_size[0]):
            index = i * grid_size[0] + j
            if index < len(images):
                image = images[index]
                x = j * size[0]
                y = i * size[1]
                grid_image.paste(image, (x, y))
                name = custom_names.iat[i, j] if custom_names is not None and not pd.isna(custom_names.iat[i, j]) else filenames[index]
                draw.text((x, y), name, font=font, fill=(0, 0, 0))
                if progress_bar:
                    progress_bar()

    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, os.path.basename(input_dir) + '_grid.png')
    grid_image.save(output_file)
    print(f"Grid image saved to {output_file}")

def check_excel_data(df):
    valid = True
    for index, row in df.iterrows():
        input_dir = row['input_dir']
        grid_size = tuple(map(int, row['grid_size'].split('x')))
        layout_file = row['layout_file']
        custom_names = pd.read_excel(layout_file, header=None)
        if custom_names.shape[0] != grid_size[1] or custom_names.shape[1] != grid_size[0]:
            print(f"Warning: Layout file dimensions for {input_dir} ({custom_names.shape[1]}x{custom_names.shape[0]}) do not match input value ({grid_size[0]}x{grid_size[1]}).")
            valid = False
    return valid

def process_image(task, queue, total_images):
    index, row = task
    input_dir = row['input_dir']
    output_dir = row['output_dir']
    grid_size = tuple(map(int, row['grid_size'].split('x')))
    font_size_factor = row['font_size_factor']
    layout_file = row['layout_file']
    custom_names = pd.read_excel(layout_file, header=None)
    
    with alive_bar(total_images, title=f'Processing {os.path.basename(input_dir)}') as inner_bar:
        create_image_grid(input_dir, output_dir, grid_size=grid_size, font_size_factor=font_size_factor, custom_names=custom_names, progress_bar=inner_bar)

    queue.put(1)
    return f"{index + 1}/{total_rows} {os.path.basename(input_dir)} finished."

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
            total_images = len([f for f in os.listdir(task[1]['input_dir']) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.tif', '.tiff'))])
            result = process_image(task, progress_queue, total_images)
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
    parser = argparse.ArgumentParser(description='Create a grid of images from an Excel file')
    parser.add_argument('user_provided_path', type=str, help='The path where the "BE.xlsx" file is located')
    args = parser.parse_args()
    read_excel_file_and_process_images_multithreaded(args.user_provided_path)
