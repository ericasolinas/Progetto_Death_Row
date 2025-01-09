import csv
import ssl
import logging
import requests
from io import BytesIO
from urllib.request import urlopen
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import easyocr
from PIL import Image
import numpy as np
import json
from openai import OpenAI
import os
import urllib3

# DISABLE SSL WARNINGS
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

api_key = os.getenv('MY_API_KEY')

SYSTEM_PROMPT = """You are a helpful assistant. When requested, you will parse text from an image and respond ONLY with a JSON object in the format:
{
  "Summary": "...",c
  "Education Level": "..."
}
No extra commentary, only the JSON object from the first '{' to the last '}'. 
"""


ocr_reader = easyocr.Reader(['en'], gpu=True)


def fix_url(url, base_url="https://www.tdcj.texas.gov"):
    """
    Creates a full valid URL from a relative path.
    """
    if "/death_row/" not in url:
        url = "/death_row/" + url.lstrip("/")
    return urljoin(base_url, url)

def ocr_inmate_info_with_easyocr(image_url):
    """
    Download the .jpg inmate info page.
    Return the raw text as a single string.
    """
    try:
        logging.debug(f"Downloading image for OCR: {image_url}")
        response = requests.get(image_url, timeout=15, verify=False)
        response.raise_for_status()

        # Convert to PIL image, then to NumPy array
        pil_image = Image.open(BytesIO(response.content)).convert("RGB")
        np_image = np.array(pil_image)

        # Perform OCR
        extracted_lines = ocr_reader.readtext(np_image, detail=0)
        ocr_text = "\n".join(extracted_lines)

        logging.debug("OCR extraction complete.")
        return ocr_text

    except Exception as e:
        logging.error(f"OCR error for {image_url}: {e}")
        return ""

def parse_with_gpt(raw_text):
    """
    Sends raw text to GPT, returns structured data (Summary, Education Level) in JSON.
    Extracts from the first '{' to the last '}' to avoid extraneous text.
    """
    if not raw_text:
        return "N/A", "N/A"

    try:
        
        user_prompt = f"""
        Extract 'Summary' and 'Education Level' from the following text exactly as it appears, 
        and respond ONLY with the JSON from the first '{{' to the last '}}':
        
        {raw_text}
        """
        
        
        client = OpenAI(api_key=api_key)
        
        completion =  client.chat.completions.create(
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

        summary = parsed.get("Summary", "N/A")
        education = parsed.get("Education Level", "N/A")

        return summary, education

    except Exception as e:
        logging.error(f"Error parsing text with GPT: {e}")
        return "N/A", "N/A"

def extract_inmate_info(url):
    """
    Extracts Summary of Incident and Education Level from the Inmate Information page.
    - If URL ends with '.jpg', we do OCR + GPT parse.
    - Otherwise, parse HTML as usual.
    """
    logging.debug(f"Extracting inmate info from {url}")

    if url.endswith(".jpg"):
        
        ocr_text = ocr_inmate_info_with_easyocr(url)

        summary_of_incident, education_level = parse_with_gpt(ocr_text)
        return summary_of_incident, education_level

    
    summary_of_incident = "N/A"
    education_level = "N/A"
    try:
        context = ssl._create_unverified_context()
        html_page = urlopen(url, context=context)
        soup = BeautifulSoup(html_page, "html.parser")

        # exact Education Level
        education_row = soup.find("td", string="Education Level (Highest Grade Completed)")
        if education_row:
            education_level = education_row.find_next_sibling("td").get_text(strip=True)

        # extract Summary of Incident
        summary_paragraph = soup.find("span", string="Summary of Incident")
        if summary_paragraph:
            summary_text = summary_paragraph.find_next("br").next_sibling
            summary_of_incident = summary_text.strip() if summary_text else "N/A"

        logging.debug(f"HTML: Summary={summary_of_incident}, Education={education_level}")

    except Exception as e:
        logging.error(f"Error extracting info from HTML {url}: {e}")

    return summary_of_incident, education_level

def extract_last_statement(url):
    """
    Extracts the Last Statement from the page.
    """
    logging.debug(f"Extracting last statement from {url}")

    last_statement = "N/A"
    try:
        context = ssl._create_unverified_context()
        inmate_html = urlopen(url, context=context)
        inmate_soup = BeautifulSoup(inmate_html, "html.parser")
        paragraphs = inmate_soup.find_all("p")

        for i, paragraph in enumerate(paragraphs):
            if "last statement" in paragraph.get_text(strip=True).lower():
                statement_text = [
                    follow_up.get_text(strip=True)
                    for follow_up in paragraphs[i + 1:]
                    if follow_up.get_text(strip=True)
                    and "offender information" not in follow_up.get_text(strip=True).lower()
                ]
                last_statement = " ".join(statement_text) if statement_text else "N/A"
                break

        logging.debug(f"Last statement: {last_statement[:60]}...")

    except Exception as e:
        logging.error(f"Error parsing the Last Statement for {url}: {e}")

    return last_statement

def process_inmate_row(row, base_url):
    """Processes a single row from the main table."""
    columns = row.find_all("td")
    last_name = columns[3].get_text(strip=True)
    first_name = columns[4].get_text(strip=True)
    age = columns[6].get_text(strip=True)
    date = columns[7].get_text(strip=True)
    ethnicity = columns[8].get_text(strip=True)
    county = columns[9].get_text(strip=True)

    
    statement_link = columns[2].find('a')
    last_statement_url = fix_url(statement_link['href'], base_url) if statement_link else None

    inmate_link = columns[1].find('a')
    inmate_info_url = fix_url(inmate_link['href'], base_url) if inmate_link else None

    
    last_statement = "N/A"
    summary_of_incident = "N/A"
    education_level = "N/A"

    if last_statement_url:
        last_statement = extract_last_statement(last_statement_url)

    if inmate_info_url:
        summary_of_incident, education_level = extract_inmate_info(inmate_info_url)

    return [
        last_name,
        first_name,
        age,
        date,
        ethnicity,
        county,
        last_statement,
        summary_of_incident,
        education_level
    ]

def main():
    base_url = "https://www.tdcj.texas.gov"
    main_url = base_url + "/death_row/dr_executed_offenders.html"

    logging.info(f"Loading main page: {main_url}")

    context = ssl._create_unverified_context()
    html_page = urlopen(main_url, context=context)
    soup_page = BeautifulSoup(html_page, "html.parser")

    table = soup_page.find("table", {"class": "tdcj_table indent"})
    if not table:
        logging.error("Unable to find the main offender table.")
        return

    rows = table.find_all("tr")[1:]  
    info_inmates = []

    logging.info("Processing rows...")
    
    for row in rows:
        row_data = process_inmate_row(row, base_url)
        info_inmates.append(row_data)

    # create CSV file
    csv_filename = "scraping_executed_inmates.csv"
    logging.info(f"Writing data to {csv_filename}")

    with open(csv_filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "Last Name",
            "First Name",
            "Age",
            "Date",
            "Ethnicity",
            "County",
            "Last Statement",
            "Summary of Incident",
            "Education Level"
        ])
        writer.writerows(info_inmates)

    logging.info(f"Data written to {csv_filename}")

if __name__ == "__main__":
    main()