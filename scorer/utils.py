import openai
import editdistance
import json
import os

# Load API key from file
def load_api_key(key_file_path="mykey"):
    try:
        with open(key_file_path, 'r') as file:
            api_key = file.read().strip()
        return api_key
    except Exception as e:
        print(f"Error loading API key: {e}")
        return None

# Set the API key for OpenAI
api_key = load_api_key()
if api_key:
    openai.api_key = api_key
else:
    print("Warning: No API key found. API calls will fail.")

def compose_alignment_prompt(label_text, predicted_text):
    # Use double curly braces to escape them in f-strings
    prompt = f"""
    Below are two pieces of text, the first is a manual transcript of a conversation (label text), the second is an automatic transcription of the same conversation (predicted text).
    Your job is to align the sentences in the two texts.
    The label is the ground truth so align the predicted text to the label text.
    The output should be valid json with the following format:

    ```json
    [
        {{
            "label_sentence_index": 0,
            "label_sentence": "sentence from the manual transcript",
            "predicted_sentence": "sentence from the automatic transcription"
        }}
    ]
    ```
    Label Text
    The label text is:
    {label_text}

    Predicted text
    The predicted text is:
    {predicted_text}

    Respond only in json.
    """

    return prompt


def generate_aligned_sentences(label_text, predicted_text):
    # Check if API key is set
    if not openai.api_key:
        raise ValueError("OpenAI API key is not set. Please check the 'mykey' file.")
        
    prompt = compose_alignment_prompt(label_text, predicted_text)
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    
    # Return the content from the response
    return response.choices[0].message.content


def score_response_json(response_json):
    # Parse the response json
    try:
        response_data = json.loads(response_json)
    except json.JSONDecodeError as e:
        print(f"Error parsing response json: {e}")
        return None

    results = []
    for item in response_data:
        label_sentence = item["label_sentence"]
        predicted_sentence = item["predicted_sentence"]
        index = item["label_sentence_index"]

        # Calculate edit distance
        edit_distance = editdistance.eval(label_sentence, predicted_sentence)

        results.append({
            "index": index,
            "label_sentence": label_sentence,
            "predicted_sentence": predicted_sentence,
            "edit_distance": edit_distance
        })

    return results

def summarize_results(results):
    if not results:
        return {"error": "No results to summarize"}
        
    return {
        "total_edit_distance": sum(item["edit_distance"] for item in results),
        "average_edit_distance": sum(item["edit_distance"] for item in results) / len(results),
        "maximum_edit_distance": max(item["edit_distance"] for item in results)
    }

def visualize_results(results):
    try:
        import matplotlib.pyplot as plt
        import numpy as np

        # Extract edit distances from results
        edit_distances = [item["edit_distance"] for item in results]

        # Plot histogram of edit distances
        plt.figure(figsize=(10, 6))
        plt.hist(edit_distances, bins=min(30, len(edit_distances)), edgecolor='black')
        plt.title('Histogram of Edit Distances')
        plt.xlabel('Edit Distance')
        plt.ylabel('Frequency')
        plt.grid(True, alpha=0.3)
        plt.show()
        
        # Plot edit distances by sentence index
        indices = [item["index"] for item in results]
        plt.figure(figsize=(12, 6))
        plt.bar(range(len(indices)), edit_distances)
        plt.xticks(range(len(indices)), indices, rotation=90)
        plt.title('Edit Distance by Sentence Index')
        plt.xlabel('Sentence Index')
        plt.ylabel('Edit Distance')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()
        
    except ImportError:
        print("Matplotlib is required for visualization. Install it with 'pip install matplotlib'")
    
