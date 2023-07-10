from flask import Flask, request, jsonify
from langchain.indexes import VectorstoreIndexCreator
from langchain.document_loaders import PyPDFDirectoryLoader
from langchain.callbacks import get_openai_callback
from azure.storage.blob import BlobServiceClient, BlobClient
import os

app = Flask(__name__)

class DownloadPayload:
    def __init__(self, blob_name):
        self.blob_name = blob_name

def read_text_from_file(file_path):
    try:
        with open(file_path, "r") as file:
            text = file.read()
        return text
    except Exception as e:
        print(f"Error reading file '{file_path}': {str(e)}")
        return None

def download_file_from_blob(container_name, blob_name):
    try:
        connection_string = "DefaultEndpointsProtocol=https;AccountName=azuretestshubham832458;AccountKey=2yEaP59qlgKVv6kEUCA5ARB4wdV3ZRoL2X9zjYCcIxOSYAG1CSBbBlAMPx3uBIe7ilQtSh7purEK+AStvFn8GA==;EndpointSuffix=core.windows.net"  # Replace with your Azure Blob Storage connection string
        
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        
        destination_path = f"transcripts/{blob_name}"  # Replace with the desired destination path
        
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)  # Create the destination directory if it doesn't exist
        
        with open(destination_path, "wb") as file:
            file.write(blob_client.download_blob().readall())
        
        print(f"File downloaded successfully: {destination_path}")
        return True
    except Exception as e:
        print(f"Error downloading file '{blob_name}': {str(e)}")
        return False

@app.route("/download", methods=["POST"])
def download_file():
    payload = request.json
    blob_name = payload["blob_name"]
    
    success = download_file_from_blob("transcript", blob_name)
    
    if success:
        return jsonify({"message": "File download completed successfully."})
    else:
        return jsonify({"message": "File download failed."})

os.environ["OPENAI_API_KEY"] = "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"

def search_questions(questions, context):
    pdf_directory = "./transcripts/"
    loader = PyPDFDirectoryLoader(pdf_directory)
    docs = loader.load()
    index = VectorstoreIndexCreator().from_loaders([loader])
    output_data = []
    total_cost = 0  # Initialize total cost
    with get_openai_callback() as cb:
        for i, question in enumerate(questions):
            full_question = f"{context} {question}"  # Add the context before each question
            answer = index.query_with_sources(full_question)
            output_data.append(answer)
        total_cost = cb.total_cost  # Get the total cost from the callback
    return output_data

context = read_text_from_file('context.txt')
print(context)

@app.route("/predict", methods=["POST"])
def predict():
    payload = request.json
    question = payload["question"]
    answer = search_questions([question], context)[0]  # Pass the context as an argument
    return jsonify({"answer": answer['answer'], "source": answer['sources']})

if __name__ == "__main__":
    app.run()
