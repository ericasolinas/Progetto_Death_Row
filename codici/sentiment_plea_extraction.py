import csv
import ssl
import logging
import requests
from urllib.request import urlopen
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import json
from openai import OpenAI
import os

# DISABLE SSL WARNINGS
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

api_key = os.getenv('MY_API_KEY')

SYSTEM_PROMPT = """
You are a helpful assistant. Your task is to analyze the provided statement and respond ONLY with a JSON object in the following format:

{
  "Emotions": ["emotion1", "emotion2", "emotion3"],
  "Plea": "guilty/not guilty/unspecified"
}

Guidelines:
- "Emotions" should contain exactly three distinct emotions that best represent the statement's content. 
- Use emotions like: "remorse", "serenity", "anger", "fear", "hope", "sadness", "gratitude", "defiance", "love", "peace", or "forgiveness". Choose the most relevant ones.
- "Plea" should indicate whether the statement expresses guilt ("guilty"), denial of guilt ("not guilty"), or does not mention guilt ("unspecified").
- Do not add extra commentary or output anything outside the JSON object from the first '{' to the last '}'.
"""

def analyze_last_statement_with_gpt(last_statement):
    """
    Analyzes the emotions and plea status of the last statement using OpenAI GPT.
    """
    if not last_statement or last_statement == "N/A":
        return "N/A", "N/A"

    try:
        client = OpenAI(api_key=api_key)
        user_prompt = f"""
        Analyze the following statement and respond with the emotions it expresses and its plea status (guilty, not guilty, unspecified). 
        Last Statement: "{last_statement}"
        """
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            temperature=0,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]
        )

        gpt_response = completion.choices[0].message.content

        
        start_idx = gpt_response.find('{')
        end_idx = gpt_response.rfind('}')
        if start_idx == -1 or end_idx == -1:
            logging.warning("GPT response did not contain valid JSON braces.")
            return "N/A", "N/A"

        json_str = gpt_response[start_idx:end_idx+1]
        parsed = json.loads(json_str)

        emotions = ", ".join(parsed.get("Emotions", []))
        plea = parsed.get("Plea", "N/A")

        return emotions, plea

    except Exception as e:
        logging.error(f"Error analyzing last statement with GPT: {e}")
        return "N/A", "N/A"

def update_csv_with_emotions_and_pleas(input_csv, output_csv):
    """
    Reads the existing CSV, updates it with emotions and plea status using OpenAI GPT, 
    and writes the updated data to a new CSV file.
    """
    updated_data = []

    with open(input_csv, "r", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames + ["Emotions", "Plea Status"]  
        logging.info(f"Existing fields: {reader.fieldnames}")

        for row in reader:
            last_statement = row.get("Last Statement", "N/A")
            emotions, plea_status = analyze_last_statement_with_gpt(last_statement)

            row["Emotions"] = emotions
            row["Plea Status"] = plea_status

            updated_data.append(row)

    # create new CSV file
    with open(output_csv, "w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_data)

    logging.info(f"CSV file updated with emotions and plea statuses. Output saved to {output_csv}")

def main():
    input_csv = "scraping_executed_inmates.csv"
    output_csv = "executed_inmates_emotions_plea.csv" 
    update_csv_with_emotions_and_pleas(input_csv, output_csv)

if __name__ == "__main__":
    main()