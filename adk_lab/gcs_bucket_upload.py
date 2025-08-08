import os
import zipfile
from google.cloud import storage


def upload_zip_contents_to_gcs(zip_file_paths, bucket_name):
    """
    Extracts source code files from local ZIP archives in memory and uploads
    them directly to a specified Google Cloud Storage bucket with a .txt extension.

    This script avoids saving extracted files to the local disk.

    Args:
        zip_file_paths (list): A list of strings, where each string is the
                             path to a local ZIP file.
        bucket_name (str): The name of the target GCS bucket
                           (e.g., "my-source-code-bucket").
    """
    # Define the file extensions to look for
    SOURCE_EXTENSIONS = {".cpp", ".h", ".py", ".java"}

    try:
        # Initialize the GCS client.
        # Assumes you have authenticated via `gcloud auth application-default login`
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        print(f"✅ Successfully connected to GCS bucket '{bucket_name}'.")

    except Exception as e:
        print(f"❌ Failed to connect to GCS. Please ensure you are authenticated.")
        print(f"Error: {e}")
        return

    # Process each ZIP file provided in the list
    for zip_path in zip_file_paths:
        if not os.path.exists(zip_path):
            print(f"⚠️  Warning: File not found at '{zip_path}'. Skipping.")
            continue

        print(f"\nProcessing '{zip_path}'...")
        zip_file_name = os.path.basename(zip_path).replace('.zip', '')

        try:
            # Open the zip file in read mode
            with zipfile.ZipFile(zip_path, 'r') as zf:
                # Iterate over each file in the zip archive
                for file_info in zf.infolist():
                    # Skip directories
                    if file_info.is_dir():
                        continue
                    
                    original_filename = file_info.filename
                    
                    # Check if the file has one of the desired source code extensions
                    if any(original_filename.lower().endswith(ext) for ext in SOURCE_EXTENSIONS):
                        # Get the base filename without its original extension
                        base_filename = os.path.splitext(original_filename)[0]

                        # Construct a new destination path for GCS with a .txt extension
                        destination_blob_name = f"{zip_file_name}/{base_filename}.txt"
                        
                        # Create a blob object for the destination in GCS
                        blob = bucket.blob(destination_blob_name)
                        
                        # Read the file's content directly from the zip into memory
                        file_content = zf.read(original_filename)
                        
                        # Upload the in-memory content to GCS
                        blob.upload_from_string(file_content)
                        
                        print(f"  -> Uploaded '{original_filename}' to '{destination_blob_name}'")

        except zipfile.BadZipFile:
            print(f"❌ Error: '{zip_path}' is not a valid ZIP file.")
        except Exception as e:
            print(f"❌ An unexpected error occurred while processing '{zip_path}': {e}")
            
    print("\n🎉 Script finished.")


# --- HOW TO USE ---
if __name__ == "__main__":
    # 1. TODO: Replace with the actual name of your GCS bucket.
    GCS_BUCKET_NAME = "adk-lab-source-code"

    # 2. TODO: Add the paths to your local ZIP files here.
    #    The script will look for these files in the same directory where you run it,
    #    or you can provide the full path to them.
    zip_files_to_upload = [
        "beg-cplusplus17-master.zip",
        "Beginning-Cpp-Programming-master.zip",
        "Java-master.zip",
        "Python-master.zip",
    ]

    # 3. Run the function
    upload_zip_contents_to_gcs(zip_files_to_upload, GCS_BUCKET_NAME)
