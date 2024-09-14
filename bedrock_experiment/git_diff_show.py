import pandas as pd
import csv
import sys
import os
import difflib
import subprocess
import difflib
from PIL import Image, ImageDraw, ImageFont

def generate_diff_image(file1_path, file2_path, output_image_path):
    with open(file1_path) as f1, open(file2_path) as f2:
        file1_lines = f1.readlines()
        file2_lines = f2.readlines()

    # Create a side-by-side diff
    d = difflib.Differ()
    diff = list(d.compare(file1_lines, file2_lines))

    # Create an image with the diff
    font = ImageFont.load_default()
    image = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(image)

    y = 10
    for line in diff:
        draw.text((10, y), line, fill='black', font=font)
        y += 15

    image = image.crop((0, 0, 800, y + 15))  # Crop the image to fit the text
    image.save(output_image_path)

if __name__ == "__main__":
    file_path = sys.argv[1] #Results/Combined_result_of_fm_and_tests.csv
    #objective = sys.argv[2] #CC (Code Coverage) or Refine_AF (Assertion Failure)
    file_name = file_path.split('/')[-1]
    df = pd.read_csv(file_path)

    outputDir = "Results"
    if not os.path.exists(outputDir):
        os.makedirs(outputDir, exist_ok=True)

    for index, row in df.iterrows():    
        proj_name = row['proj_name'] 
        #test_file_path = row['test_filename']
        unit_test_name = row['test_method']
        #fm_file_path = row['fm_filename']
        fm_name = row['fm_method']
        repaired_test = row['repaired_test']
        diff_test = row['diff_test']
        changed_fm_code = row['changed_fm']
        diff_fm = row['diff_fm']
        error_type = row['test_pass/fail']
        #if error_type == "test_pass":
        if pd.isna(error_type):
            with open("x.txt", "w") as x_file:
                x_file.write(changed_fm_code)

            with open("y.txt", "w") as y_file:
                y_file.write(diff_fm)

            subprocess.run(["vim", "-d", "x.txt", "y.txt"])

            # Save the repaired test and diff test to temporary files
            with open("x.txt", "w") as x_file:
                x_file.write(repaired_test)

            with open("y.txt", "w") as y_file:
                y_file.write(diff_test)

            subprocess.run(["vim", "-d", "x.txt", "y.txt"])
            user_input = input("Do you want to exit? If yes, type 0:")
            if user_input == "0":
                print("Exiting the script...")
                sys.exit()  # Exit the script

        #exit()
