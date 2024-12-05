import base64
import os
import re
from pathlib import Path

def image_to_base64(image_path: str) -> str:
    """Convert image to base64 string."""
    with open(image_path, "rb") as image_file:
        # Get file extension to determine image type
        image_type = Path(image_path).suffix.lower()[1:]  # Remove the dot
        if image_type in ["jpg", "jpeg"]:
            image_type = "jpeg"
        
        # Create the complete base64 string with data URI scheme
        base64_data = base64.b64encode(image_file.read()).decode("utf-8")
        return f"data:image/{image_type};base64,{base64_data}"

def extract_question_number(filename: str) -> int:
    """Extract question number from filename (e.g., 'q1.png' -> 1)."""
    match = re.search(r'q(\d+)', filename.lower())
    if not match:
        raise ValueError(f"Invalid filename format: {filename}")
    return int(match.group(1))

def get_correct_answer(sql_content: str, question_number: int) -> str:
    """Extract correct answer for a given question number from SQL content."""
    question_start = sql_content.find(f'Pytanie {question_number}')
    if question_start == -1:
        raise ValueError(f"Question {question_number} not found in SQL content")
    
    # Find the part after ', false, ' for this question
    after_false = sql_content[question_start:].split(', false, ')[1]
    # Get the first part before the next comma (the answer)
    correct_answer = after_false.split(',')[0].strip("'")
    return correct_answer

def update_sql_with_images(sql_path: str, images_dir: str, output_sql_path: str) -> None:
    """Update SQL file with base64 encoded images."""
    # Read all images and convert to base64
    images_dict = {}
    for image_file in os.listdir(images_dir):
        if image_file.lower().endswith(('.png', '.jpg', '.jpeg')):
            question_number = extract_question_number(image_file)
            image_path = os.path.join(images_dir, image_file)
            base64_image = image_to_base64(image_path)
            images_dict[question_number] = base64_image

    # Read SQL file
    with open(sql_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # Replace null values with base64 images
    for question_number, base64_image in images_dict.items():
        # Pattern to match the line for specific question number
        pattern = f"\\('Pytanie {question_number}', 'ABCDEF', null, 10, \\d+, false, '[a-f]', null\\)"
        
        # Get the correct answer for this question
        correct_answer = get_correct_answer(sql_content, question_number)
        
        # Create the replacement string
        replacement = (
            f"('Pytanie {question_number}', 'ABCDEF', null, 10, "
            f"{question_number}, false, '{correct_answer}', '{base64_image}')"
        )
        
        # Replace in SQL content
        sql_content = re.sub(pattern, replacement, sql_content)

    # Write updated SQL
    with open(output_sql_path, 'w', encoding='utf-8') as f:
        f.write(sql_content)

def main():
    # Define paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    sql_path = project_root / 'supabase' / 'seed_test_iq.sql'
    images_dir = project_root / 'iq_images'
    output_sql_path = project_root / 'supabase' / 'seed_test_iq_with_images.sql'

    # Create images directory if it doesn't exist
    if not images_dir.exists():
        images_dir.mkdir(parents=True)
        print(f"Created directory for images at: {images_dir}")
        print("Please add your images to this directory in format 'qN.png' (e.g., q1.png, q2.png, etc.)")
        return

    # Check if directory is empty
    if not any(images_dir.iterdir()):
        print(f"The directory {images_dir} is empty.")
        print("Please add your images in format 'qN.png' (e.g., q1.png, q2.png, etc.)")
        return

    # Update SQL with images
    update_sql_with_images(
        sql_path=str(sql_path),
        images_dir=str(images_dir),
        output_sql_path=str(output_sql_path)
    )
    print(f"Successfully updated SQL file with images. Output saved to: {output_sql_path}")

if __name__ == "__main__":
    main()