# backend/nlp/summarizer.py
from typing import List
import http
import json

class TextSummarizer:
    def __init__(self):
        self.HOST = "api.x.ai"
        self.ENDPOINT = "/v1/chat/completions"
        self.API_KEY = "xai-UVqSx7pTIfcPWUvmeMK6srY93SQAA7ns08yJOGO9zV1klfJxpgGvEU53Nq3rxwZxVq3EinJbQbqOgRUm"  # xAI API key

    async def summarize(self, texts: List[str], input_keyword: str) -> str:

        payload = {
            "messages": [
            {
              "role": "system",
              "content":f"Input: Stardew Valley mod comments filtered for cultural keywords, excluding bugs, technical requests, mod mechanics, and stop words. Purpose: Explore cultural perceptions and attitudes toward related countries or communities. Act as a cultural study professional to extract insights from comments. Follow these 8 rules: 1. Process input sentence-by-sentence, identifying mod titles related to '{input_keyword}'. 2.Analyze comments under relevant titles, skipping bugs, technical requests, or mod mechanics.3.Summarize and analyze sentiment (0-10, 0=hate, 10=strong support) for comments providing perspective on '{input_keyword}' itself. 4. Extract up to 5 positive and 5 negative unique comments prioritizing cultural value over generic opinions,maximizing diversity across aspects and mods, appending mod name in brackets (e.g., 'Great comment (Mod1)'). 5.Translate informal and non-English text to standard English. 6.Enhance comment fluency by adding stop words and refining grammar only as needed to maintain readability, while preserving the original meaning and tone of the comment without over-elaboration. 7.Define positive comments: like or support for '{input_keyword}' or criticism of its underrepresentation. 8.Define negative comments: hate or discrimination directly targeting '{input_keyword}', not external issues or mod/game critique. Output: a raw JSON string with keys: 'summary' (string), 'highlighted_positive_comments' (list of strings), 'highlighted_negative_comments' (list of strings), 'sentiment_analysis_score' (integer), 'sentiment_analysis_summary' (string)’. Without any prefixes like ```json or code block markers."
            },
         {
                "role": "user",
                "content": f"input: {texts}"
            }
            ],
            "model": "grok-2-1212",  
            "stream": False,
            "temperature": 0
        }

        # Establish connection
        conn = http.client.HTTPSConnection(self.HOST)

        # Headers
        headers = {
            "Authorization": f"Bearer {self.API_KEY}",
            "Content-Type": "application/json"
        }

        # Send POST request
        conn.request("POST", self.ENDPOINT, body=json.dumps(payload), headers=headers)

        # Get response
        response = conn.getresponse()
        response_data = response.read().decode("utf-8")

        # Close connection
        conn.close()

        # Parse and display the assistant's reply (if successful)
        if response.status == 200:
            data = json.loads(response_data)
            output = data["choices"][0]["message"]["content"]
            # Parse the JSON string into a Python dictionary
            result = json.loads(output)
        return result

# Example usage
if __name__ == "__main__":
    import asyncio

    # Example usage of the TextSummarizer class
    summarizer = TextSummarizer()
    texts = ["This is a great mod!", "I had a terrible experience with this mod."]
    input_keyword = "mod"
    result = asyncio.run(summarizer.summarize(texts, input_keyword))
    print(result)

