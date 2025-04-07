import re
import json
import os
from typing import List, Dict, Tuple
import ast
from datetime import datetime
import spacy
from spacy.lang.en import English


class NoiseFilter():
    name="noise_filter"
    def __init__(self, *args, **kwargs):
        # Initialize the noise filter with a list of keywords to identify noise in comments
        self.noise_keywords = [
            "SMAPI", "SVE", "install", "installed", "re-installing", "log", "warning", "warnings",
            "patch", "Content Patcher", "tile", "tiles", "compatibility", "compatible", "update", "recipe",
            "recipes", "shop", "stall", "closed", "open", "error", "errors", "version", "fix", "fixed", "fixes",
            "map", "spawn", "spawner", "balance", "support", "translation", "translated", "JSON", "crash", "location", 
            "supporter", "requirements", "feature", "work", "working", "use", "using", "author", "creator",
            "upload", "uploading", "uploaded", "download", "downloaded", "downloading", "console", "screenshot", "share", "URL", "link",
            "note", "changelogs", "description", "design", "default",
            "issue", "problem", "inconvenience", "persist", "persists", "resolve", "resolved", "hotfix", "check", "tested", "try", "tried",
            "account", "code", "publish", "purchase", "repurchase", "recode", "load", "reporting", "report", "reported", "object", "data"
        ]
        # Load the language model
        nlp_defaults = English.Defaults
        # These are words that we want to keep in the text, even if they are stop words
        discard_stop_words = ["well","cannot", "nor", "less", "not", "n't", "very", "neither","n‘t", "no", "n’t", "is", "do", "can"]
        # Remove these words from SpaCy's stop word list
        for word in discard_stop_words:
            nlp_defaults.stop_words.discard(word)
        # load the English language model after modifying the stop words
        self.nlp = spacy.load("en_core_web_sm")
        

    def split_noise_comments(self, text_input, keyword) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
        # Convert string input to list of dictionaries if necessary
        if isinstance(text_input, str):
            try:
                text_dicts = json.loads(text_input)
            except json.JSONDecodeError:
                text_dicts = ast.literal_eval(text_input)
        else:
            text_dicts = text_input

        # Compile regex for sentence boundaries (ending with ., ?, !, or newline)
        sentence_pattern = re.compile(r'(.*?)(?:[\.\?!]|\n|$)', re.DOTALL)

        # Compile regex for noise keywords (case-insensitive, word boundaries)
        noise_pattern = re.compile(r'\b(?:' + '|'.join(map(re.escape, self.noise_keywords)) + r')\b', re.IGNORECASE)

        clean_results = []
        noise_results = []

        # Iterate through each entry in the list of dictionaries
        for entry in text_dicts:
            if not entry:
                continue
            comments = entry.get('Comments', '') # Default to empty string if not provided
            mod_title = entry.get('Mod title', 'Unknown Mod')  # Default to 'Unknown Mod' if not provided

            if not comments:
                noise_results.append({'Mod title': mod_title, 'Comments': ''})
                continue

            # Split text into sentences
            sentences = [match.group(0).strip() for match in sentence_pattern.finditer(comments) if match.group(0).strip()]
            
            # Separate clean and noise sentences
            clean_sentences = []
            noise_sentences = []

            for sentence in sentences:
                doc = self.nlp(sentence)
                # Remove stop words
                filtered_tokens = [token.text for token in doc if not token.is_stop]
                filtered_text = ' '.join(filtered_tokens)
                # Check for noise patterns
                if noise_pattern.search(filtered_text):
                    noise_sentences.append(filtered_text) 
                else:
                    clean_sentences.append(filtered_text)

            # Create dictionary entries
            clean_comments = ' '.join(clean_sentences)
            noise_comments = ' '.join(noise_sentences)

            clean_results.append({'Mod title': mod_title, 'Comments': clean_comments})
            noise_results.append({'Mod title': mod_title, 'Comments': noise_comments})

        # Create crawled_data folder if it doesn't exist
        folder_path = "crawled_data"
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        # Generate timestamp for unique filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Write clean comments to file
        clean_file_path = os.path.join(folder_path, f"{keyword}_clean_comments_{timestamp}.txt")
        with open(clean_file_path, 'w', encoding='utf-8') as clean_file:
            clean_file.write("Comments Without Noise:\n")
            for entry in clean_results:
                clean_file.write(f"Mod: {entry['Mod title']}\n")
                clean_file.write(f"Comments: {entry['Comments']}\n\n")

        # Write noise comments to file
        noise_file_path = os.path.join(folder_path, f"{keyword}_noise_comments_{timestamp}.txt")
        with open(noise_file_path, 'w', encoding='utf-8') as noise_file:
            noise_file.write("Comments With Noise:\n")
            for entry in noise_results:
                noise_file.write(f"Mod: {entry['Mod title']}\n")
                noise_file.write(f"Comments: {entry['Comments']}\n\n")

        return clean_results


