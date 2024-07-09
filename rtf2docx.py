import os
import subprocess

def convert_rtf_to_docx(rtf_path, docx_path):
    try:
        # Specify the full path to LibreOffice executable
        libreoffice_path = 'C:/Program Files/LibreOffice/program/soffice.exe'
        
        # Use LibreOffice in headless mode to convert RTF to DOCX
        subprocess.run([libreoffice_path, '--headless', '--convert-to', 'docx', rtf_path, '--outdir', os.path.dirname(docx_path)], check=True)
        
        # Default LibreOffice output file name
        default_docx_path = os.path.splitext(rtf_path)[0] + '.docx'
        
        # If the conversion was successful, rename the file to the desired output name
        if os.path.exists(default_docx_path):
            os.rename(default_docx_path, docx_path)
        else:
            print(f"Error: Expected output file {default_docx_path} does not exist.")
    
    except subprocess.CalledProcessError as e:
        print(f"Error during conversion: {e}")

def convert_directory(directory_path):
    for filename in os.listdir(directory_path):
        if filename.endswith(".rtf"):
            file_path = os.path.join(directory_path, filename)
            docx_path = os.path.splitext(file_path)[0] + '.docx'
            convert_rtf_to_docx(file_path, docx_path)

# Usage
if __name__ == "__main__":
    convert_directory('C:/Scripts/arrendy-rag/arrendy-rag/TestDocs')
