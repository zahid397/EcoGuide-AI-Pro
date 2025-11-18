import os

# Folders that MUST be Python packages (contain __init__.py)
packages = [
    "backend",
    "ui",
    "ui/tabs",
    "utils"
]

# Folders for data/storage
data_dirs = [
    "data",
    "data/profiles",
    "prompts",
    "logs"
]

print("🔄 Fixing project structure...")

# 1. Create package folders and __init__.py
for folder in packages:
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"✅ Created folder: {folder}")
    
    init_file = os.path.join(folder, "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, "w") as f:
            f.write("# Init file for package")
        print(f"✅ Created missing file: {init_file}")

# 2. Create data folders
for folder in data_dirs:
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"✅ Created data folder: {folder}")

print("\n🎉 Project Structure Fixed! Now follow Step 3.")
