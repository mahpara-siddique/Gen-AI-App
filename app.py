from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from groq import Groq
import os

app = FastAPI()

# Set your Groq API key here


uploaded_dataset = None  # Global variable to hold the dataset


@app.get("/", response_class=HTMLResponse)
async def main():
    html_content = """
    <h1>Gen-AI Water Resource Management</h1>
    <h3>Upload Dataset</h3>
    <form action="/upload-dataset/" method="post" enctype="multipart/form-data">
        <label for="file">Upload Excel File (xlsx):</label>
        <input type="file" id="file" name="file">
        <button type="submit">Upload</button>
    </form>
    <h3>Analyze Data</h3>
    <form action="/analyze/" method="post">
        <label for="serial_number">Serial Number:</label>
        <input type="number" id="serial_number" name="serial_number" required>
        <button type="submit">Analyze</button>
    </form>
    """
    return HTMLResponse(content=html_content)


@app.post("/upload-dataset/")
async def upload_dataset(file: UploadFile = File(...)):
    global uploaded_dataset

    try:
        # Save the file temporarily
        file_path = f"temp_{file.filename}"
        with open(file_path, "wb") as f:
            f.write(await file.read())

        # Load dataset
        uploaded_dataset = pd.read_excel(file_path)
        os.remove(file_path)

        return {"message": "Dataset uploaded successfully!", "columns": list(uploaded_dataset.columns)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error uploading dataset: {str(e)}")


@app.post("/analyze/")
async def analyze_data(serial_number: int = Form(...)):
    global uploaded_dataset

    if uploaded_dataset is None:
        raise HTTPException(status_code=400, detail="No dataset uploaded. Please upload a dataset first.")

    try:
        # Query Groq API for optimization
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f"Optimize water distribution network for Serial Number {serial_number}."
                }
            ],
            model="llama3-8b-8192",
        )

        # Extract Groq API response
        optimization_message = response.choices[0].message.content

        # Generate a graph for demonstration
        graph = nx.DiGraph()
        graph.add_edge("Source", "Node 1", weight=10)
        graph.add_edge("Node 1", "Node 2", weight=15)
        graph.add_edge("Node 2", "Sink", weight=5)

        # Save graph visualization
        plt.figure(figsize=(8, 6))
        pos = nx.spring_layout(graph)
        nx.draw(graph, pos, with_labels=True, node_color="lightblue", font_weight="bold")
        nx.draw_networkx_edge_labels(graph, pos, edge_labels=nx.get_edge_attributes(graph, "weight"))
        plt.savefig("graph.png")
        plt.close()

        # Generate HTML with results
        html_content = f"""
        <h1>Analysis Results</h1>
        <p>Optimization Message: {optimization_message}</p>
        <h3>Graph:</h3>
        <img src="/graph.png" alt="Graph">
        <a href="/">Go Back</a>
        """
        return HTMLResponse(content=html_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing data: {str(e)}")
