import os
import subprocess
import sys
import shutil

def create_and_setup_venv():
    # Define the virtual environment directory and Python path
    venv_dir = os.path.join(os.getcwd(), "venv")
    print(venv_dir)
    python_path = r"python.exe"

    # Check if the specified Python exists
    if not os.path.exists(python_path):
        print(f"Error: Specified Python executable not found at {python_path}")
        sys.exit(1)

    # Install virtualenv globally if not already installed
    try:
        print(f"Ensuring virtualenv is installed for Python at {python_path}...")
        subprocess.check_call([python_path, "-m", "pip", "install", "virtualenv"])
    except subprocess.CalledProcessError as e:
        print(f"Failed to install virtualenv: {e}")
        sys.exit(1)

    # Check if venv already exists
    if os.path.exists(venv_dir):
        print(f"Virtual environment already exists at {venv_dir}.")
        try:
            response = input("Would you like to delete and recreate it? (y/n): ").strip().lower()
            if response == 'y':
                print(f"Deleting existing virtual environment at {venv_dir}...")
                shutil.rmtree(venv_dir)
            else:
                print("Proceeding with existing virtual environment.")
        except KeyboardInterrupt:
            print("\nSetup aborted by user.")
            sys.exit(1)
    
    # Create the virtual environment using virtualenv if it doesn't exist
    if not os.path.exists(venv_dir):
        try:
            print(f"Creating virtual environment with Python at {python_path}...")
            subprocess.check_call([python_path, "-m", "virtualenv", venv_dir, f"--python={python_path}"])
        except subprocess.CalledProcessError as e:
            print(f"Failed to create virtual environment: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Unexpected error during virtual environment creation: {e}")
            sys.exit(1)
    
    # Determine the path to the Python and pip executables in the venv
    if sys.platform == "win32":
        python_executable = os.path.join(venv_dir, "Scripts", "python.exe")
        pip_executable = os.path.join(venv_dir, "Scripts", "pip.exe")
    else:
        python_executable = os.path.join(venv_dir, "bin", "python")
        pip_executable = os.path.join(venv_dir, "bin", "pip")
    
    # Ensure the executables exist
    if not os.path.exists(python_executable):
        print(f"Error: Python executable not found at {python_executable}")
        sys.exit(1)
    
    # Upgrade pip, setuptools, and wheel
    try:
        print("Upgrading pip, setuptools, and wheel...")
        subprocess.check_call([python_executable, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"])
    except subprocess.CalledProcessError as e:
        print(f"Failed to upgrade pip, setuptools, and wheel: {e}")
        sys.exit(1)
    
    # Uninstall typing package if it exists
    try:
        print("Checking for and uninstalling 'typing' package...")
        subprocess.check_call([pip_executable, "uninstall", "typing", "-y"])
        print("'typing' package uninstalled successfully (or was not present).")
    except subprocess.CalledProcessError as e:
        # If uninstall fails because typing isn't installed, it's not an error
        if "not installed" in str(e.output):
            print("'typing' package was not installed.")
        else:
            print(f"Failed to uninstall 'typing' package: {e}")
            sys.exit(1)
    
    # Install requirements from requirements.txt
    requirements_file = "requirements.txt"
    if not os.path.exists(requirements_file):
        print(f"Error: {requirements_file} not found in the current directory.")
        sys.exit(1)
    
    try:
        print(f"Installing dependencies from {requirements_file}...")
        subprocess.check_call([pip_executable, "install", "-r", requirements_file])
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        sys.exit(1)
    
    # Set PYTHONPATH with relative paths (assuming current dir is 'building')
    current_dir = os.getcwd()  # This is the 'building' folder
    venv_site_packages = os.path.join(current_dir,"venv", "Lib", "site-packages")
    crawler_dir = os.path.join(current_dir,"backend", "crawler")
    nlp_dir = os.path.join(current_dir,"backend", "nlp")
    
    pythonpath = f"{venv_site_packages};{crawler_dir};{nlp_dir}"
    
    print("Setup complete!")

       # Print activation instructions
    print("To activate the virtual environment:")
    if sys.platform == "win32":
        print(f"  {os.path.join(venv_dir, 'Scripts', 'activate')}")
    else:
        print(f"  source {os.path.join(venv_dir, 'bin', 'activate')}")

    print("Set the following environment variable for PYTHONPATH:")
    if sys.platform == "win32":
        print(f"  set PYTHONPATH={pythonpath}")
        print("  (You can add this to your shell or environment variables permanently)")
    else:
        print(f"  export PYTHONPATH={pythonpath}")
        print("  (You can add this to your shell profile, e.g., ~/.bashrc or ~/.zshrc)")

 

if __name__ == "__main__":
    try:
        create_and_setup_venv()
    except Exception as e:
        print(f"An unexpected error occurred during setup: {e}")
        sys.exit(1)