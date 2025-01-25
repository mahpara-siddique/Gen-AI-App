from fastapi import FastAPI, UploadFile, File, HTTPException, Form
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from groq import Groq
import os

# Initialize FastAPI app
app = FastAPI()

# Initialize Groq client
GROQ_API_KEY = "your_groq_api_key"  # Replace with your actual API key
client = Groq(api_key=GROQ_API_KEY)

# Temporary storage for datasets
uploaded_datasets = {}

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to the Gen-AI Water Resource Management App!"}

# Endpoint to upload dataset
@app.post("/upload-dataset/")
async def upload_dataset(file: UploadFile = File(...)):
    try:
        # Save the uploaded file temporarily
        file_path = f"temp_{file.filename}"
        with open(file_path, "wb") as f:
            f.write(await file.read())

        # Load dataset
        dataset = pd.read_excel(file_path)
        os.remove(file_path)  # Clean up the temporary file

        # Add serial numbers if missing
        if "Serial Number" not in dataset.columns:
            dataset["Serial Number"] = range(1, len(dataset) + 1)

        # Store dataset in memory
        uploaded_datasets[file.filename] = dataset

        return {"message": "Dataset uploaded successfully!", "columns": list(dataset.columns), "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

# Endpoint to analyze data
@app.post("/analyze/")
async def analyze_data(filename: str = Form(...), serial_number: int = Form(...)):
    try:
        # Retrieve the uploaded dataset
        if filename not in uploaded_datasets:
            raise HTTPException(status_code=400, detail="Dataset not found. Please upload it first.")

        dataset = uploaded_datasets[filename]

        # Ensure serial number exists
        if serial_number not in dataset["Serial Number"].values:
            raise HTTPException(status_code=400, detail="Invalid serial number. Please check the dataset.")

        # Example Groq API query
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f"Optimize water distribution network for Serial Number {serial_number} to minimize consumption fluctuations."
                }
            ],
            model="llama3-8b-8192",
        )
        return {"analysis": chat_completion.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying Groq API: {str(e)}")

