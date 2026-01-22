import os
import glob
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.widgets import RectangleSelector
import numpy as np

class ImageCropper:
    def __init__(self, image_folder, output_folder=None):
        self.image_folder = image_folder
        self.output_folder = output_folder or os.path.join(image_folder, 'cropped')
        self.crop_coords = None
        self.selector = None
        self.ax = None
        self.fig = None
        
        # Create output folder if it doesn't exist
        os.makedirs(self.output_folder, exist_ok=True)
        
        # Get all image files
        self.image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff', '*.gif']
        self.image_files = []
        for ext in self.image_extensions:
            self.image_files.extend(glob.glob(os.path.join(image_folder, ext)))
            self.image_files.extend(glob.glob(os.path.join(image_folder, ext.upper())))
        
        if not self.image_files:
            raise ValueError(f"No image files found in {image_folder}")
        
        print(f"Found {len(self.image_files)} images to process")
    
    def onselect(self, eclick, erelease):
        """Callback function for rectangle selection"""
        x1, y1 = int(eclick.xdata), int(eclick.ydata)
        x2, y2 = int(erelease.xdata), int(erelease.ydata)
        
        # Ensure coordinates are in correct order
        self.crop_coords = (
            min(x1, x2),  # left
            min(y1, y2),  # top
            max(x1, x2),  # right
            max(y1, y2)   # bottom
        )
        
        print(f"Selected crop area: {self.crop_coords}")
        print("Close the window or press Enter to proceed with cropping all images")
    
    def select_crop_area(self):
        """Display the first image and let user select crop area"""
        # Load the first image
        first_image_path = self.image_files[0]
        image = Image.open(first_image_path)
        
        print(f"Select crop area on: {os.path.basename(first_image_path)}")
        print("Instructions:")
        print("1. Click and drag to select the area you want to crop")
        print("2. Close the window when you're satisfied with the selection")
        
        # Create figure and axis
        self.fig, self.ax = plt.subplots(figsize=(12, 8))
        self.ax.imshow(np.array(image))
        self.ax.set_title(f"Select Crop Area - {os.path.basename(first_image_path)}")
        
        # Create rectangle selector
        self.selector = RectangleSelector(
            self.ax, 
            self.onselect,
            useblit=True,
            button=[1],  # Only left mouse button
            minspanx=5, 
            minspany=5,
            spancoords='pixels',
            interactive=True
        )
        
        plt.tight_layout()
        plt.show()
        
        if self.crop_coords is None:
            raise ValueError("No crop area was selected!")
        
        return self.crop_coords
    
    def crop_all_images(self):
        """Apply the selected crop to all images"""
        if self.crop_coords is None:
            raise ValueError("No crop coordinates available. Run select_crop_area() first.")
        
        left, top, right, bottom = self.crop_coords
        successful_crops = 0
        
        print(f"\nApplying crop ({left}, {top}, {right}, {bottom}) to all images...")
        
        for i, image_path in enumerate(self.image_files):
            try:
                # Open image
                image = Image.open(image_path)
                
                # Check if crop coordinates are within image bounds
                img_width, img_height = image.size
                if (left >= 0 and top >= 0 and 
                    right <= img_width and bottom <= img_height and
                    left < right and top < bottom):
                    
                    # Crop the image
                    cropped_image = image.crop((left, top, right, bottom))
                    
                    # Generate output filename
                    filename = os.path.basename(image_path)
                    name, ext = os.path.splitext(filename)
                    output_path = os.path.join(self.output_folder, f"{name}_cropped{ext}")
                    
                    # Save cropped image
                    cropped_image.save(output_path, quality=95)
                    successful_crops += 1
                    
                    print(f"✓ Processed ({i+1}/{len(self.image_files)}): {filename}")
                    
                else:
                    print(f"✗ Skipped {os.path.basename(image_path)}: crop area outside image bounds")
                    
            except Exception as e:
                print(f"✗ Error processing {os.path.basename(image_path)}: {str(e)}")
        
        print(f"\nCompleted! Successfully cropped {successful_crops}/{len(self.image_files)} images")
        print(f"Cropped images saved to: {self.output_folder}")

def main():
    """Main function to run the image cropper"""
    # Configuration
    image_folder = input("Enter the path to your image folder: ").strip().strip('"')
    
    if not os.path.exists(image_folder):
        print(f"Error: Folder '{image_folder}' does not exist!")
        return
    
    # Optional: specify output folder
    output_choice = input("Enter output folder path (or press Enter to use 'cropped' subfolder): ").strip().strip('"')
    output_folder = output_choice if output_choice else None
    
    try:
        # Create cropper instance
        cropper = ImageCropper(image_folder, output_folder)
        
        # Let user select crop area
        crop_coords = cropper.select_crop_area()
        
        # Apply crop to all images
        cropper.crop_all_images()
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()