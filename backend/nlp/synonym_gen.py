# backend/nlp/synonym_gen.py
from typing import List
import logging
import http.client
import json

logger = logging.getLogger(__name__)

class SynonymGenerator:
    def __init__(self):
        self.HOST = "api.x.ai"
        self.ENDPOINT = "/v1/chat/completions"
        self.API_KEY = "xai-UVqSx7pTIfcPWUvmeMK6srY93SQAA7ns08yJOGO9zV1klfJxpgGvEU53Nq3rxwZxVq3EinJbQbqOgRUm"  #xAI API key

    def _make_api_request(self, payload):
        # Make the API request to xAI
        # Handle the request and response
        try:
            conn = http.client.HTTPSConnection(self.HOST)
            headers = {
                "Authorization": f"Bearer {self.API_KEY}",
                "Content-Type": "application/json"
            }
            conn.request("POST", self.ENDPOINT, body=json.dumps(payload), headers=headers)
            response = conn.getresponse() # Get the response from the server
            response_data = response.read().decode("utf-8") # Read the response data
            conn.close()

            if response.status == 200:
                data = json.loads(response_data)
                return data["choices"][0]["message"]["content"]
            else:
                logger.error(f"API request failed with status {response.status}: {response_data}")
                return None
        except Exception as e:
            logger.error(f"Error in API request: {str(e)}")
            return None

    async def classify_term(self, text: str) -> int:
        # Classify the term into one of the specified categories
        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": "Classify the input term into one of these categories and return only the corresponding number:\n- 0 for group term (e.g., LGBT, Asian) - 1 for country-prefixed broad categories (e.g., Japanese cuisine, French architecture) - 2 for country name (e.g., Japan) - 3 for specific cultural element (e.g., sushi) - 4 if the term does not fit any specified category. Output only the number (e.g., 0)."
                },
                {"role": "user", "content": f"input: {text}"}
            ],
            "model": "grok-2-1212",
            "stream": False,
            "temperature": 0
        }

        result = self._make_api_request(payload)
        if result is not None and result.isdigit(): # Check if the result is a digit
            return int(result)
        logger.error(f"Classification failed for {text}, received: {result}")
        return None  # Default to None category on failure

    async def process_term(self, text: str, category: int) -> List[str]:
        # Process the term based on its classification number, sending only the relevant prompt.
        prompt_templates = {
            0: "Process the input term as a group term and return a comma-separated string without quotes containing 5 related words and 5 cultural elements tied to the group (e.g., input Japanese output anime, input Asian output Chinese, input LGBTQ+ output lesbian,gay), avoiding famous people. Prioritize well-known terms, exclude disrespectful terms, ensure exactly 10 terms, return only the string (e.g., output1,output2), no additional labels.",
            1: "Process the input term as a country-prefixed broad category and return a comma-separated string without quotes containing 10 specific cultural elements tied to the category, avoiding famous people (e.g., input Chinese clothing output qipao). Prioritize well-known terms, ensure exactly 10 terms, return only the string (e.g., output1,output2), no additional labels.",
            2: "Process the input term as a country name and return a comma-separated string without quotes containing 10 cultural elements: first 5 are broad categories prefixed with the country name (e.g., input Japan output Japanese cuisine), last 5 are specific elements (e.g., kimono). Prioritize well-known terms, ensure exactly 10 terms, return only the string (e.g., output1,output2), no additional labels.",
            3: "Process the input term as a specific cultural element and return a comma-separated string without quotes containing 1 broad category it belongs to and 3 synonyms or closely related terms (e.g., input sushi output Japanese cuisine,makizushi,nigiri,sashimi). Prioritize well-known terms, do not include the input term in the output, ensure exactly 4 terms, return only the string (e.g., output1,output2), no additional labels.",
        }

        # Select the appropriate prompt based on category
        system_content = prompt_templates.get(category, None)  

        if system_content is not None:
            payload = {
                "messages": [
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": f"input: {text}"}
                ],
                "model": "grok-2-1212",
                "stream": False,
                "temperature": 0
            }
            result = self._make_api_request(payload)
            if result and result != "None":
                return result.split(",")
        else:
            return []

    async def generate(self, text: str) -> List[str]:
        """Main method to classify and process the term."""
        # Step 1: Classify the term
        category = await self.classify_term(text)
        if category is not None:
        # Step 2: Process based on classification
            synonyms = await self.process_term(text, category)
            return synonyms
        else:
            return []

if __name__ == "__main__":
    import asyncio

    # Example usage
    # Define the terms to be classified and processed
    terms = {
        "country": ["Japan", "India", "China"],
        "country_board": ["Japanese cuisine", "Chinese clothing", "UK music", "India festival", "Vietnam clothing"],
        "community": ["LGBTQ+", "African American", "Japanese", "Asian", "Latino"],
        "cultural_element": ["Sushi", "Kimono", "Jollof", "Yoga", "Tacos"],
        "others":["hello world"]
    }

    generator = SynonymGenerator()
    for category, items in terms.items():
        for item in items:
            print(f"{category}: {item}")
            result = asyncio.run(generator.generate(item))
            print(result, "\n")