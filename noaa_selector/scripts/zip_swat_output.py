import os
import zipfile

def zip_swat_folder(out_folder, zip_name="swat_output.zip"):
    zip_path = os.path.join(out_folder, zip_name)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(out_folder):
            for file in files:
                if file.endswith((".pcp", ".tmp", ".sta", ".cio")):
                    full_path = os.path.join(root, file)
                    arcname = os.path.relpath(full_path, out_folder)
                    z.write(full_path, arcname)

    return zip_path
