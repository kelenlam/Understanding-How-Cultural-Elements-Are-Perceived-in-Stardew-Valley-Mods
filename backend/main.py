# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict
import time
from .nlp.synonym_gen import SynonymGenerator
from .nlp.summarizer import TextSummarizer
from .crawler.spider import WebCrawler
from .database.mongodb import MongoDB
from .database.redis_cache import RedisCache
from .nlp.noise_filter import NoiseFilter
from .config import Config
import logging
import json

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ChatMessage(BaseModel):
    message: str
    user_id: str

app = FastAPI()

# Set up CORS and static file serving
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
synonym_gen = SynonymGenerator()
summarizer = TextSummarizer()
web_crawler = WebCrawler()
mongo_db = MongoDB()
redis_cache = RedisCache()
noise_filter= NoiseFilter()

# Store conversation state
conversation_state = {}

async def export_mongo_to_redis(mongo_db, redis_cache):
    # Fetch all documents from MongoDB and cache them in Redis
    collection = mongo_db.db.analysis_results
    cursor = collection.find()  # Fetch all documents, no query filter
    
    async for document in cursor:
        try:
            # Prepare key (using original_message) and value (serialized document)
            cache_key = document['original_message']
            document['_id'] = str(document['_id'])  # Convert ObjectId to string
            document['timestamp'] = document['timestamp'].isoformat()  # Convert datetime to string
            stored_dict = json.loads(json.dumps(document))
            formatted_response = generate_response(stored_dict)
            # Cache in Redis
            await redis_cache.set(cache_key, formatted_response)
            logger.info(f"Cached {cache_key} in Redis")
        except Exception as e:
            logger.error(f"Failed to cache {cache_key} in Redis: {e}")
    logger.info("MongoDB data export to Redis completed")

@app.on_event("startup")
async def startup_event():
    # Connect to MongoDB and Redis, and export MongoDB data to Redis
    try:
        await mongo_db.connect()
        await redis_cache.connect()
        await export_mongo_to_redis(mongo_db,redis_cache)
        print("Connected to MongoDB and Redis")
        print("This is latest version of the backend")
    except Exception as e:
        logger.error(f"Error during startup: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    # Close connections to MongoDB and Redis
    await mongo_db.close()
    await redis_cache.close()

@app.get("/")
async def read_root(): # Serve the frontend HTML file
    return FileResponse("frontend/templates/index.html")

@app.post("/api/chat") # Endpoint for chat messages
async def chat_endpoint(message: ChatMessage):

    try:
        logger.info(f"Received message: {message.message}")
        user_id = message.user_id
        

        cache_key = message.message
        cached_response = None
        try:
            if cache_key!="yes" and cache_key!="no": # don't cache yes or no
                # Check if the response is already cached in Redis
                cached_response = await redis_cache.get(cache_key)                    
                if cached_response:
                    try:
                        logger.info(f"Cache hit for key: {cache_key}")
                        # Decode bytes to string if necessary, then deserialize JSON
                        if isinstance(cached_response, bytes):
                            cached_response = cached_response.decode('utf-8')
                        conversation_state[user_id] = {
                            "stage": "initial",
                            "original_message": "",
                            "synonyms": [],
                            "crawl_results": []
                        }
                        return {"response": cached_response}
                    except Exception as e:
                            logger.error(f"Redis error: {e}")

        except Exception as e:
            logger.error(f"Redis get error: {e}, proceeding without cache")

        # Check if the user_id exists in conversation_state
        if user_id not in conversation_state:
            conversation_state[user_id] = {
            "stage": "initial",
            "original_message": "",
            "synonyms": [],
            "crawl_results": []
                }
        state = conversation_state[user_id]

        # Process based on current stage
        if state["stage"] == "initial": # Ask whether to generate synonyms
            print("initial") 
            state["original_message"] = (message.message).lower()
            state["stage"] = "awaiting_synonym_confirm"
            return {"response": "Would you like me to generate synonyms or related words for your query? Please respond with 'yes' or 'no' to continue."}

        elif state["stage"] == "awaiting_synonym_confirm": # Ask whether to crawl websites for synonyms
            print("synonym")
            if message.message.lower() == "yes":
                print("yes")
                logger.info("Generating synonyms...")
                state["synonyms"] = await synonym_gen.generate(state["original_message"])
                logger.debug(f"Generated synonyms: {state['synonyms']}")
                state["stage"] = "awaiting_crawl_confirm"
                return {"response": f"Generated synonyms: {state['synonyms']}. Would you like me to crawl websites for these terms? Please respond with 'yes' or 'no' to continue."}
            elif message.message.lower() == "no":  
                print("no")
                logger.info("Skipping synonyms, proceeding to crawl original keyword...")
                state["synonyms"] = []  
                state["stage"] = "awaiting_crawl_confirm"
                return {"response": f"No synonyms generated. Would you like me to crawl websites for '{state['original_message']}'? Please respond with 'yes' or 'no' to continue."}
            else:
                return {"response": "Please respond with 'yes' or 'no' to proceed."}

        elif state["stage"] == "awaiting_crawl_confirm": # Ask whether to crawl websites for the original message and synonyms
            print("crawl")
            if message.message.lower() == "yes":
                start_time = time.time()
                logger.info("Crawling websites for each synonym...")
                max_cm = 50
                crawled_mods=set()
                #crawl 10*4=40 mods for original message
                results = await web_crawler.crawl(state["original_message"], 10, max_cm, crawled_mods)
                state["crawl_results"].extend(results)
                crawled_mods.update(result["Mod title"] for result in results)

                # Crawl for synonyms
                if len(state["synonyms"])>1 and len(state["synonyms"])<=4:
                    max_mod=5 #5*4*3=60 mods for synonyms
                else:
                    max_mod=3 #3*4*10=120 mods for relatd words
                
                for synonym in state["synonyms"]:
                    results = await web_crawler.crawl(synonym, max_mod, max_cm, crawled_mods)
                    state["crawl_results"].extend(results)
                    crawled_mods.update(result["Mod title"] for result in results)
                logger.debug("Finished crawling websites.")

                # Filter out noise comments
                logger.info("Filtering out noise comment...")
                state["crawl_results"] = noise_filter.split_noise_comments(state["crawl_results"],state["original_message"])

                # Generate summary and analyze sentiment
                logger.info("Generating summary and analyzing sentiment...")
                summary = await summarizer.summarize(state["crawl_results"], state["original_message"])
                logger.debug("Summary generated.")

                end_time = time.time()
                total_time = end_time - start_time

                # Store results in MongoDB with exception handling
                logger.info("Storing results in MongoDB...")
                analysis_result = {
                    "original_message": state["original_message"],
                    "crawled_no": len(state["crawl_results"]),
                    "synonyms": state["synonyms"],
                    "summary": summary,
                    "crawling_time": total_time
                }
                try:
                    await mongo_db.store_analysis(analysis_result)
                except Exception as e:
                    logger.error(f"MongoDB storage error: {e}")

                # Generate natural language response
                logger.info("Generating natural language response...")
                response = generate_response(analysis_result)
                logger.debug(f"Generated response: {response}")

                # Cache the response in Redis with exception handling
                logger.info("Caching the response...")
                try:
                    await redis_cache.set(state["original_message"], response)
                except Exception as e:
                    logger.error(f"Redis set error: {e}, response generated but not cached")


                # Clear the conversation state
                conversation_state[user_id] = {
                    "stage": "initial",
                    "original_message": "",
                    "synonyms": [],
                    "crawl_results": []
                }
                return {"response": response}
            
            elif message.message.lower() == "no": # User declined crawling
                logger.info("User declined crawling, returning to initial stage...")
                state["stage"] = "initial"
                state["synonyms"] = []
                state["crawl_results"] = []
                return {"response": "Okay, I won’t crawl websites. Please provide a new keyword to start over."}
            else:
                return {"response": "Please respond with 'yes' or 'no' to proceed."}

    except Exception as e:
        logger.error(f"Error in chat_endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

def generate_response(analysis_result: Dict) -> str: 
    # Extract the summary dict
    summary_data = analysis_result.get('summary', {})
    
    # Format each summary item on a new line
    summary_lines = []
    for key, value in summary_data.items():
        if isinstance(value, list):  # Handle lists of any length
            if value:  # Check if list is non-empty
                formatted_value = "\n" + "\n".join(f"  - {item}" for item in value)
            else:
                formatted_value = "  - (No items)"  # Handle empty lists
        else:
            formatted_value = value
        summary_lines.append(f"{key.replace('_', ' ').title()}: {formatted_value}")

    # Join summary lines with double newlines for separation
    summary_text = "\n\n".join(summary_lines)

    # Construct the full response
    response = (
        f"Based on my analysis of {(analysis_result['crawled_no'])} sources on {(analysis_result['original_message'])}, "
        f"here's what I found:\n\n"
        f"Synonyms and related words: {', '.join(analysis_result['synonyms'])}\n\n"
        f"\n{summary_text}\n"
        f"\n Please input another cultural elements to explore.\n"
    )
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=Config.API_HOST, port=Config.API_PORT)
