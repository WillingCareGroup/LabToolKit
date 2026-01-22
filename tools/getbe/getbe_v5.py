import argparse
import os
import pandas as pd
import math
import datetime

def get_subdirectories(root_path):
    return [os.path.join(root_path, d) for d in os.listdir(root_path) if os.path.isdir(os.path.join(root_path, d))]

def calculate_grid_size(directory):
    num_images = len([f for f in os.listdir(directory) if f.endswith('.jpg') or f.endswith('.png') or f.endswith('.tif')])
    sqrt_num_images = int(math.sqrt(num_images))
    for rows in range(sqrt_num_images, 0, -1):
        if num_images % rows == 0:
            cols = num_images // rows
            return f"{cols}x{rows}"
    return "1x1"

def count_images(directory):
    return len([f for f in os.listdir(directory) if f.endswith('.jpg') or f.endswith('.png') or f.endswith('.tif')])

def generate_excel_file(output_file, root_path, layout_file):
    folders = get_subdirectories(root_path)
    grid_sizes = [calculate_grid_size(folder) for folder in folders]
    font_size_factors = [0.1] * len(folders)
    image_counts = [count_images(folder) for folder in folders]

    data = {
        'input_dir': folders,
        'grid_size': grid_sizes,
        'font_size_factor': font_size_factors,
        'layout_file': [os.path.join(root_path, folder_name[2:6] + folder_name[7] + folder_name[9] + '.xlsx') for folder_name in os.listdir(root_path) if os.path.isdir(os.path.join(root_path, folder_name))],
        'image_count': image_counts,
        'output_dir': [root_path] * len(folders),
    }

    df = pd.DataFrame(data)
    df.to_excel(output_file, index=False)

if __name__ == '__main__':
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Generate an Excel file with input directories, grid sizes, and font size factors')
    parser.add_argument('-output_file', type=str, default=None, help='Output Excel file (optional)')
    parser.add_argument('root_path', type=str, help='Root directory containing subfolders with images')
    args = parser.parse_args()

    # Set the default output file name with the current date
    if args.output_file is None:
        current_date = datetime.datetime.now().strftime('%m%d')
        args.output_file = "BE.xlsx"

    # Generate Excel file in the root directory
    output_path = os.path.join(args.root_path, args.output_file)
    generate_excel_file(output_path, args.root_path, None)

    # Open the output file
    os.startfile(output_path)
