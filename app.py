from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
from groq import Groq
import os

# Initialize FastAPI app
app = FastAPI()

# Initialize Groq client
GROQ_API_KEY = "your_groq_api_key"  # Replace with your actual API key
client = Groq(api_key=GROQ_API_KEY)

# Temporary storage for datasets
uploaded_datasets = {}

# Root endpoint with HTML interface
@app.get("/", response_class=HTMLResponse)
def home():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Gen-AI Water Resource Management App</title>
    </head>
    <body>
        <h1>Gen-AI Water Resource Management</h1>
        <h2>Upload Dataset</h2>
        <form action="/upload-dataset/" enctype="multipart/form-data" method="post">
            <label for="file">Upload Excel File (xlsx):</label>
            <input type="file" id="file" name="file" accept=".xlsx" required>
            <button type="submit">Upload</button>
        </form>
        <hr>
        <h2>Analyze Data</h2>
        <form action="/analyze/" method="post">
            <label for="filename">Uploaded Filename:</label>
            <input type="text" id="filename" name="filename" required>
            <br><br>
            <label for="serial_number">Serial Number:</label>
            <input type="number" id="serial_number" name="serial_number" required>
            <br><br>
            <button type="submit">Analyze</button>
        </form>
    </body>
    </html>
    """
    return html_content

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

        return HTMLResponse(f"""
        <html>
        <body>
        <h3>Dataset uploaded successfully!</h3>
        <p>Filename: {file.filename}</p>
        <p>Columns: {", ".join(dataset.columns)}</p>
        <a href="/">Go back to Home</a>
        </body>
        </html>
        """)
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
        optimization_result = chat_completion.choices[0].message.content

        # Generate a graph for demonstration (replace with real graph if needed)
        plt.figure(figsize=(6, 4))
        plt.bar(["Metric A", "Metric B", "Metric C"], [10, 20, 15], color="blue")
        plt.title(f"Analysis Results for Serial Number {serial_number}")
        plt.xlabel("Metrics")
        plt.ylabel("Values")
        plt.grid()

        # Save the graph to a BytesIO object and encode it as base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format="png")
        buffer.seek(0)
        graph_base64 = base64.b64encode(buffer.read()).decode("utf-8")
        buffer.close()

        return HTMLResponse(f"""
        <html>
        <body>
        <h3>Analysis Result</h3>
        <p><b>Optimization:</b> {optimization_result}</p>
        <h3>Graph:</h3>
        <img src="data:image/png;base64,{graph_base64}" alt="Analysis Graph">
        <br><br>
        <a href="/">Go back to Home</a>
        </body>
        </html>
        """)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying Groq API: {str(e)}")
