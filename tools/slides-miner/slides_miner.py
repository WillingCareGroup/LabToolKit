import cv2
import numpy as np
import os
from PIL import Image
import argparse
from pathlib import Path
import time
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor

class SlideExtractor:
    def __init__(self, video_path, output_dir="./screenshots", threshold=0.02, num_workers=None, reference_points=100):
        """
        Initialize the slide extractor.
        
        Args:
            video_path (str): Path to the input video file
            output_dir (str): Directory to save screenshots
            threshold (float): Threshold for detecting slide changes (0.0-1.0)
            num_workers (int): Number of worker threads (None = auto-detect)
            reference_points (int): Number of reference points to sample across frame
        """
        self.video_path = video_path
        self.output_dir = Path(output_dir)
        self.threshold = threshold
        self.num_workers = num_workers or min(mp.cpu_count(), 16)
        self.reference_points = reference_points
        self.screenshots = []
        self.sample_points = None  # Will be calculated based on frame size
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(exist_ok=True)
        
    def generate_sample_points(self, frame_height, frame_width):
        """Generate strategically distributed sample points to avoid slide grid alignment."""
        if self.sample_points is not None:
            return self.sample_points
        
        # Use fixed random seed for consistent sampling across frames
        np.random.seed(42)
        
        # Create margins to avoid UI elements and slide borders
        margin_h = int(frame_height * 0.08)
        margin_w = int(frame_width * 0.08)
        
        usable_height = frame_height - 2 * margin_h
        usable_width = frame_width - 2 * margin_w
        
        points = []
        
        # Strategy: Combine random sampling with diagonal bias to avoid slide structure
        for i in range(self.reference_points):
            if i < self.reference_points // 2:
                # First half: Pure random distribution
                y = margin_h + np.random.randint(0, usable_height)
                x = margin_w + np.random.randint(0, usable_width)
            else:
                # Second half: Diagonal and offset patterns to break slide alignment
                # Use diagonal bias with random offset
                diagonal_progress = (i - self.reference_points // 2) / (self.reference_points // 2)
                
                # Create diagonal sweep with random perpendicular offset
                base_y = margin_h + int(diagonal_progress * usable_height)
                base_x = margin_w + int(diagonal_progress * usable_width)
                
                # Add random offset perpendicular to diagonal
                offset_range = min(usable_height, usable_width) // 8
                y_offset = np.random.randint(-offset_range, offset_range)
                x_offset = np.random.randint(-offset_range, offset_range)
                
                y = np.clip(base_y + y_offset, margin_h, frame_height - margin_h)
                x = np.clip(base_x + x_offset, margin_w, frame_width - margin_w)
            
            points.append((int(y), int(x)))
        
        # Remove duplicates and ensure good distribution
        unique_points = list(set(points))
        
        # If we lost too many to duplicates, fill with more random points
        while len(unique_points) < self.reference_points:
            y = margin_h + np.random.randint(0, usable_height)
            x = margin_w + np.random.randint(0, usable_width)
            point = (int(y), int(x))
            if point not in unique_points:
                unique_points.append(point)
        
        # Keep only the requested number of points
        self.sample_points = unique_points[:self.reference_points]
        
        print(f"Generated {len(self.sample_points)} strategically distributed sample points")
        print(f"Sampling strategy: 50% random + 50% diagonal-offset to avoid slide alignment")
        return self.sample_points
    
    def extract_reference_features(self, frame):
        """Extract features from reference points across the frame."""
        h, w = frame.shape[:2]
        points = self.generate_sample_points(h, w)
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
        
        features = []
        patch_size = 8  # 8x8 patch around each point
        half_patch = patch_size // 2
        
        for y, x in points:
            # Extract small patch around each point
            y1, y2 = max(0, y - half_patch), min(h, y + half_patch)
            x1, x2 = max(0, x - half_patch), min(w, x + half_patch)
            
            patch = gray[y1:y2, x1:x2]
            
            if patch.size > 0:
                # Calculate multiple features for each patch
                mean_intensity = np.mean(patch)
                std_intensity = np.std(patch)
                
                # Simple gradient features
                if patch.shape[0] > 1 and patch.shape[1] > 1:
                    grad_x = np.mean(np.abs(np.diff(patch, axis=1)))
                    grad_y = np.mean(np.abs(np.diff(patch, axis=0)))
                else:
                    grad_x = grad_y = 0
                
                features.extend([mean_intensity, std_intensity, grad_x, grad_y])
            else:
                features.extend([0, 0, 0, 0])  # Default values for edge cases
        
        return np.array(features)
    
    def calculate_frame_difference_multipoint(self, features1, features2):
        """Calculate frame difference using multiple reference point features."""
        if len(features1) != len(features2):
            return 1.0  # Maximum difference if feature lengths don't match
        
        # Normalize features to 0-1 range for consistent comparison
        features1_norm = features1 / 255.0
        features2_norm = features2 / 255.0
        
        # Calculate mean absolute difference
        mad = np.mean(np.abs(features1_norm - features2_norm))
        
        # Calculate normalized euclidean distance
        euclidean_dist = np.linalg.norm(features1_norm - features2_norm) / np.sqrt(len(features1))
        
        # Combine both metrics
        combined_diff = 0.6 * mad + 0.4 * euclidean_dist
        
        return combined_diff
    
    def process_frame_batch(self, frame_batch_info):
        """Process a batch of frames and return detection results."""
        frames, start_frame_num = frame_batch_info
        detections = []
        
        if len(frames) < 2:
            return detections
        
        # Extract reference point features for all frames in batch
        features_list = []
        for frame in frames:
            features = self.extract_reference_features(frame)
            features_list.append(features)
        
        # Calculate differences for consecutive frames
        for i in range(1, len(features_list)):
            diff = self.calculate_frame_difference_multipoint(features_list[i-1], features_list[i])
            
            if diff > self.threshold:
                frame_num = start_frame_num + i
                detections.append((frame_num, diff, frames[i]))
        
        return detections
    
    def save_screenshot(self, frame, frame_number):
        """Save a frame as a screenshot."""
        filename = f"slide_{len(self.screenshots):04d}_frame_{frame_number}.png"
        filepath = self.output_dir / filename
        
        # Convert BGR to RGB for saving
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame_rgb)
        image.save(filepath, "PNG")
        
        self.screenshots.append(filepath)
        print(f"Saved screenshot: {filename}")
        
    def process_video(self):
        """Process the video using fast batch processing with multi-point detection."""
        print(f"Processing video: {self.video_path}")
        print(f"Settings: threshold={self.threshold}, reference_points={self.reference_points}")
        print(f"Using {self.num_workers} worker threads for parallel processing")
        
        # Open video
        cap = cv2.VideoCapture(str(self.video_path))
        
        if not cap.isOpened():
            raise ValueError(f"Error opening video file: {self.video_path}")
        
        # Get video properties
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        print(f"Video properties: {total_frames} frames, {fps:.2f} FPS")
        
        # Load all frames in batches
        batch_size = 50  # Smaller batches for better memory management
        frame_batches = []
        all_frames = []
        
        print("Loading frames into memory...")
        start_time = time.time()
        
        frame_count = 0
        current_batch = []
        
        while True:
            ret, frame = cap.read()
            if not ret:
                if current_batch:
                    frame_batches.append((current_batch.copy(), frame_count - len(current_batch)))
                break
            
            all_frames.append(frame)
            current_batch.append(frame)
            frame_count += 1
            
            if len(current_batch) >= batch_size:
                frame_batches.append((current_batch.copy(), frame_count - len(current_batch)))
                current_batch = []
            
            # Progress indicator
            if frame_count % (total_frames // 10) == 0:
                progress = (frame_count / total_frames) * 100
                print(f"Loading progress: {progress:.1f}%")
        
        cap.release()
        loading_time = time.time() - start_time
        print(f"Loaded {len(all_frames)} frames in {loading_time:.2f} seconds")
        
        # Save first frame as first slide
        self.save_screenshot(all_frames[0], 0)
        slides_detected = 1
        
        # Process batches in parallel
        print(f"Processing {len(frame_batches)} batches with multi-point detection...")
        start_time = time.time()
        
        all_detections = []
        
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            # Submit all batch jobs
            futures = [executor.submit(self.process_frame_batch, batch) for batch in frame_batches]
            
            # Collect results as they complete
            for i, future in enumerate(futures):
                batch_detections = future.result()
                all_detections.extend(batch_detections)
                
                progress = ((i + 1) / len(futures)) * 100
                print(f"Batch processing progress: {progress:.1f}%")
        
        # Sort detections by frame number
        all_detections.sort(key=lambda x: x[0])
        
        # Save detected slides
        print("Saving detected slides...")
        for frame_num, difference, frame in all_detections:
            self.save_screenshot(frame, frame_num)
            slides_detected += 1
            print(f"Slide change detected at frame {frame_num} (difference: {difference:.4f})")
        
        processing_time = time.time() - start_time
        total_time = loading_time + processing_time
        
        print(f"\nProcessing complete!")
        print(f"Total slides detected: {slides_detected}")
        print(f"Processing time: {processing_time:.2f} seconds")
        print(f"Total time: {total_time:.2f} seconds")
        print(f"Processing speed: {len(all_frames)/total_time:.1f} FPS")
        
        if slides_detected < 20:
            print(f"Consider lowering threshold for more detections")
        
        return self.screenshots
    
    def create_pdf(self, output_pdf="slides.pdf"):
        """Combine all screenshots into a PDF file in the current directory."""
        if not self.screenshots:
            print("No screenshots to combine into PDF")
            return
        
        print(f"Creating PDF with {len(self.screenshots)} slides...")
        
        # Open all images
        images = []
        for screenshot_path in self.screenshots:
            img = Image.open(screenshot_path)
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            images.append(img)
        
        # Save PDF in current directory (not in screenshots folder)
        pdf_path = Path.cwd() / output_pdf
        images[0].save(
            pdf_path,
            save_all=True,
            append_images=images[1:],
            resolution=100.0,
            quality=95
        )
        
        print(f"PDF created in current directory: {pdf_path}")
        return pdf_path
    
    def cleanup_screenshots(self):
        """Remove individual screenshot files after PDF creation."""
        for screenshot_path in self.screenshots:
            screenshot_path.unlink()
        print("Screenshot files deleted.")


def find_mp4_in_folder():
    """Find the first .mp4 file in the current directory."""
    current_dir = Path('.')
    mp4_files = list(current_dir.glob('*.mp4'))
    if mp4_files:
        return str(mp4_files[0])
    return None


def main():
    parser = argparse.ArgumentParser(description="Extract slides from screenrecording video (Multi-Point Detection)")
    parser.add_argument("video_path", nargs='?', help="Path to the input video file (auto-detects .mp4 if not provided)")
    parser.add_argument("--output-dir", default="./screenshots", 
                       help="Directory to save screenshots (default: ./screenshots)")
    parser.add_argument("--threshold", type=float, default=0.02,
                       help="Threshold for detecting slide changes (default: 0.02)")
    parser.add_argument("--reference-points", type=int, default=100,
                       help="Number of reference points to sample across frame (default: 100)")
    parser.add_argument("--pdf-name", default="slides.pdf",
                       help="Name of output PDF file (default: slides.pdf)")
    parser.add_argument("--cleanup", action="store_true",
                       help="Delete individual screenshot files after PDF creation")
    parser.add_argument("--workers", type=int, default=None,
                       help="Number of worker threads (default: auto-detect)")
    
    args = parser.parse_args()
    
    # Auto-detect video file if not provided
    video_path = args.video_path
    if not video_path:
        video_path = find_mp4_in_folder()
        if not video_path:
            print("Error: No .mp4 file found in current directory. Please specify a video file.")
            return
        print(f"Auto-detected video file: {video_path}")
    
    # Validate video file exists
    if not os.path.exists(video_path):
        print(f"Error: Video file '{video_path}' not found")
        return
    
    try:
        # Create extractor and process video
        extractor = SlideExtractor(
            video_path=video_path,
            output_dir=args.output_dir,
            threshold=args.threshold,
            num_workers=args.workers,
            reference_points=args.reference_points
        )
        
        # Extract slides using fast processing
        screenshots = extractor.process_video()
        
        if screenshots:
            # Create PDF in current directory
            extractor.create_pdf(args.pdf_name)
            
            # Cleanup if requested
            if args.cleanup:
                extractor.cleanup_screenshots()
        else:
            print("No slides were extracted from the video")
            
    except Exception as e:
        print(f"Error processing video: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()