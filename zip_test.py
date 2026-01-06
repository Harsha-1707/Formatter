import shutil
import os

OUTPUT_FOLDER = "./output_tex"
# Find the directory
dirs = [d for d in os.listdir(OUTPUT_FOLDER) if os.path.isdir(os.path.join(OUTPUT_FOLDER, d))]

if dirs:
    project_dir = os.path.join(OUTPUT_FOLDER, dirs[0])
    print(f"Zipping {project_dir}...")
    shutil.make_archive(project_dir, 'zip', project_dir)
    print(f"Created {project_dir}.zip")
else:
    print("No project directory found to zip.")
