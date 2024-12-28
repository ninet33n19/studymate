import requests

# Define the Flask endpoint URL
url = "http://127.0.0.1:5000/upload"  # Replace with your actual Flask endpoint

# File path and user ID to send
file_path = r"D:\djsanghvi\notes\semester_5\is\Genetic Algorithm.pdf"  # Replace with the actual file path
user_id = "user_7"  # Replace with the actual user ID

# Open the file in binary mode
with open(file_path, "rb") as file:
    # Define the payload with user_id and file
    files = {
        "file": (file_path.split("/")[-1], file, "application/octet-stream"),
    }
    data = {
        "user_id": user_id
    }

    # Send POST request to the endpoint
    try:
        response = requests.post(url, data=data, files=files)

        # Check the response status code
        if response.status_code == 200:
            print("File uploaded and processed successfully!")
            print("Response:", response.json())
        else:
            print("Failed to upload file. Status Code:", response.status_code)
            print("Error Response:", response.json())

    except requests.exceptions.RequestException as e:
        print("An error occurred:", e)
