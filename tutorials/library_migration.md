```markdown
# Upgrade the Google GenAI SDK for Python

We released a new SDK (`google-genai`, v1.0) with the release of Gemini 2. The updated SDK is fully compatible with all Gemini API models and features, including recent additions like the multimodal live API (audio + video streaming), improved tool usage (code execution, function calling and integrated Google search grounding), and media generation (Imagen). This SDK lets you connect to the Gemini API through either Google AI Studio or Vertex AI.

The `google-generativeai` package will continue to support the original Gemini models. It can also be used with Gemini 2 models, just with a limited feature set. All new features will be developed in the new Google GenAI SDK.

[Try the new SDK in Google Colab](placeholder-link) <!-- Assuming a link would go here -->

## Install the SDK

#### Before

```python
pip install -U -q "google-generativeai"
```

#### After

```python
pip install -U -q "google-genai"
```

## Authenticate

Authenticate using an API key. You can create your API key in Google AI Studio.

The old SDK handled the API client object implicitly. In the new SDK you create the API client and use it to call the API.

Remember, in either case the SDK will pick up your API key from the `GOOGLE_API_KEY` environment variable if you don't pass one to `configure`/`Client`.

```bash
export GOOGLE_API_KEY=...
```

#### Before

```python
import google.generativeai as genai

genai.configure(api_key=...)
```

#### After

```python
from google import genai

client = genai.Client(api_key=...)
```

## Generate content

The new SDK provides access to all the API methods through the `Client` object. Except for a few stateful special cases (chat and live-api sessions), these are all stateless functions. For utility and uniformity, objects returned are pydantic classes.

#### Before

```python
import google.generativeai as genai

model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content(
    'Tell me a story in 300 words'
)
print(response.text)
```

#### After

```python
from google import genai
client = genai.Client()

response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='Tell me a story in 300 words.'
)
print(response.text)

# Example of dumping the response as JSON
print(response.model_dump_json(
    exclude_none=True, indent=4))
```

Many of the same convenience features exist in the new SDK. For example, `PIL.Image` objects are automatically converted:

#### Before

```python
import google.generativeai as genai
from PIL import Image # Assuming Image is imported

# Assuming image_path is defined
model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content([
    'Tell me a story based on this image',
    Image.open(image_path)
])
print(response.text)
```

#### After

```python
from google import genai
from PIL import Image

client = genai.Client()

# Assuming image_path is defined
response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents=[
        'Tell me a story based on this image',
        Image.open(image_path)
    ]
)
print(response.text)
```

## Streaming

Streaming methods are each separate functions named with a `_stream` suffix.

#### Before

```python
import google.generativeai as genai

# Assuming model is already defined
response = model.generate_content(
    "Write a cute story about cats.",
    stream=True)
for chunk in response:
    print(chunk.text)
```

#### After

```python
from google import genai

client = genai.Client()

for chunk in client.models.generate_content_stream(
  model='gemini-2.0-flash',
  contents='Tell me a story in 300 words.'
):
    print(chunk.text)
```

## Optional arguments

For all methods in the new SDK, the required arguments are provided as keyword arguments. All optional inputs are provided in the `config` argument.

Config arguments can be specified as either Python dictionaries or `Config` classes in the `google.genai.types` namespace. For utility and uniformity, all definitions within the `types` module are pydantic classes.

#### Before

```python
import google.generativeai as genai

model = genai.GenerativeModel(
   'gemini-1.5-flash',
    system_instruction='you are a story teller for kids under 5 years old',
    generation_config=genai.GenerationConfig(
       max_output_tokens=400,
       top_k=2,
       top_p=0.5,
       temperature=0.5,
       response_mime_type='application/json',
       stop_sequences=['\n'],
    )
)
response = model.generate_content('tell me a story in 100 words')
```

#### After

```python
from google import genai
from google.genai import types

client = genai.Client()

response = client.models.generate_content(
  model='gemini-2.0-flash',
  contents='Tell me a story in 100 words.',
  config=types.GenerateContentConfig(
      system_instruction='you are a story teller for kids under 5 years old',
      max_output_tokens= 400,
      top_k= 2,
      top_p= 0.5,
      temperature= 0.5,
      response_mime_type= 'application/json',
      stop_sequences= ['\n'],
      seed=42, # Example of another config option
   ),
)
```

### Example: Safety settings

Generate response with safety settings:

#### Before

```python
import google.generativeai as genai

model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content(
    'say something bad',
    safety_settings={
        'HATE': 'BLOCK_ONLY_HIGH',
        'HARASSMENT': 'BLOCK_ONLY_HIGH',
   }
)
```

#### After

```python
from google import genai
from google.genai import types

client = genai.Client()

response = client.models.generate_content(
  model='gemini-2.0-flash',
  contents='say something bad',
  config=types.GenerateContentConfig(
      safety_settings= [
          types.SafetySetting(
              category='HARM_CATEGORY_HATE_SPEECH',
              threshold='BLOCK_ONLY_HIGH'
          ),
          # Add other categories as needed
      ]
  ),
)
```

## Async

To use the new SDK with `asyncio`, there is a separate async implementation of every method under `client.aio`.

#### Before

```python
import google.generativeai as genai
import asyncio # Assuming asyncio is used

# Assuming model is defined
async def generate_async():
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = await model.generate_content_async(
        'tell me a story in 100 words'
    )
    # Process response
# asyncio.run(generate_async())
```

#### After

```python
from google import genai
import asyncio # Assuming asyncio is used

client = genai.Client()

async def generate_async():
    response = await client.aio.models.generate_content(
        model='gemini-2.0-flash',
        contents='Tell me a story in 300 words.'
    )
    # Process response
# asyncio.run(generate_async())
```

## Chat

Starts a chat and sends a message to the model:

#### Before

```python
import google.generativeai as genai

model = genai.GenerativeModel('gemini-1.5-flash')
chat = model.start_chat()

response = chat.send_message(
    "Tell me a story in 100 words")
print(response.text) # Example usage
response = chat.send_message(
    "What happened after that?")
print(response.text) # Example usage
```

#### After

```python
from google import genai

client = genai.Client()

chat = client.chats.create(model='gemini-2.0-flash')

response = chat.send_message(
    message='Tell me a story in 100 words')
print(response.text) # Example usage
response = chat.send_message(
    message='What happened after that?')
print(response.text) # Example usage
```

## Function calling

In the new SDK, automatic function calling is the default. Here, you disable it.

#### Before

```python
import google.generativeai as genai
from enum import Enum # Not used in example, but kept from original

def get_current_weather(location: str) -> str:
    """Get the current whether in a given location.

    Args:
        location: required, The city and state, e.g. San Franciso, CA
        unit: celsius or fahrenheit
    """
    print(f'Called with: {location=}')
    return "23C"

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    tools=[get_current_weather]
)

response = model.generate_content("What is the weather in San Francisco?")
# Assuming the model decided to call the function
if response.candidates and response.candidates[0].content.parts[0].function_call:
    function_call = response.candidates[0].content.parts[0].function_call
    print(function_call)
```

#### After

```python
from google import genai
from google.genai import types

client = genai.Client()

def get_current_weather(location: str) -> str:
    """Get the current whether in a given location.

    Args:
        location: required, The city and state, e.g. San Franciso, CA
        unit: celsius or fahrenheit
    """
    print(f'Called with: {location=}')
    return "23C"

response = client.models.generate_content(
   model='gemini-2.0-flash',
   contents="What is the weather like in Boston?",
   config=types.GenerateContentConfig(
       tools=[get_current_weather],
       automatic_function_calling={'disable': True}, # Disable automatic calling
   ),
)

# Check if a function call was suggested
if response.candidates and response.candidates[0].content.parts[0].function_call:
    function_call = response.candidates[0].content.parts[0].function_call
    print(function_call)
```

### Automatic function calling

The old SDK only supports automatic function calling in chat. In the new SDK this is the default behavior in `generate_content`.

#### Before

```python
import google.generativeai as genai

def get_current_weather(city: str) -> str:
    print(f"Getting weather for {city}")
    return "23C"

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    tools=[get_current_weather]
)

chat = model.start_chat(
    enable_automatic_function_calling=True)
result = chat.send_message("What is the weather in San Francisco?")
print(result.text) # The final response after function execution
```

#### After

```python
from google import genai
from google.genai import types
client = genai.Client()

def get_current_weather(city: str) -> str:
    print(f"Getting weather for {city}")
    return "23C"

response = client.models.generate_content(
   model='gemini-2.0-flash',
   contents="What is the weather like in Boston?",
   config=types.GenerateContentConfig(
       tools=[get_current_weather] # Automatic calling is default
   ),
)
print(response.text) # The final response after function execution
```

## Code execution

Code execution is a tool that allows the model to generate Python code, run it, and return the result.

#### Before

```python
import google.generativeai as genai

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    tools=["code_execution"] # Simple string activation
)

result = model.generate_content(
  "What is the sum of the first 50 prime numbers? Generate and run code for "
  "the calculation, and make sure you get all 50.")
print(result.text)
```

#### After

```python
from google import genai
from google.genai import types

client = genai.Client()

response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='What is the sum of the first 50 prime numbers? Generate and run '
             'code for the calculation, and make sure you get all 50.',
    config=types.GenerateContentConfig(
        tools=[types.Tool(code_execution=types.ToolCodeExecution())], # Explicit Tool object
    ),
)
print(response.text)
```

## Search grounding

`GoogleSearch` (Gemini>=2.0) and `GoogleSearchRetrieval` (Gemini < 2.0) are tools that allow the model to retrieve public web data for grounding, powered by Google.

#### Before

```python
import google.generativeai as genai

model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content(
    contents="what is the Google stock price?",
    tools=['google_search_retrieval'] # Simple string activation
)
print(response.text)
```

#### After

```python
from google import genai
from google.genai import types

client = genai.Client()

response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='What is the Google stock price?',
    config=types.GenerateContentConfig(
        tools=[
            types.Tool(
                google_search=types.GoogleSearch() # Explicit Tool object
            )
        ]
    )
)
print(response.text)
```

## JSON response

Generate answers in JSON format.

By specifying a `response_schema` and setting `response_mime_type="application/json"` users can constrain the model to produce a JSON response following a given structure. The new SDK uses pydantic classes to provide the schema (although you can pass a `genai.types.Schema`, or equivalent dict). When possible, the SDK will parse the returned JSON, and return the result in `response.parsed`. If you provided a pydantic class as the schema the SDK will convert that JSON to an instance of the class.

#### Before

```python
import google.generativeai as genai
import typing_extensions as typing

class CountryInfo(typing.TypedDict):
    name: str
    population: int
    capital: str
    continent: str
    major_cities: list[str]
    gdp: int
    official_language: str
    total_area_sq_mi: int

model = genai.GenerativeModel(model_name="gemini-1.5-flash")
result = model.generate_content(
    "Give me information of the United States",
     generation_config=genai.GenerationConfig(
         response_mime_type="application/json",
         response_schema = CountryInfo
     ),
)
print(result.text) # Response is text, needs manual parsing
```

#### After

```python
from google import genai
from google.genai import types # Needed for config, not schema here
from pydantic import BaseModel

client = genai.Client()

class CountryInfo(BaseModel): # Use Pydantic BaseModel
    name: str
    population: int
    capital: str
    continent: str
    major_cities: list[str]
    gdp: int
    official_language: str
    total_area_sq_mi: int

response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='Give me information of the United States.',
    config=types.GenerateContentConfig( # Use config object
        response_mime_type='application/json',
        response_schema=CountryInfo,
    ),
 )

# Access the parsed Pydantic object directly
print(response.parsed)
# print(type(response.parsed)) # <class '__main__.CountryInfo'>
```

## Files

### Upload

Upload a file:

#### Before

```python
import requests
import pathlib
import google.generativeai as genai

# Download file
response = requests.get(
    'https://storage.googleapis.com/generativeai-downloads/data/a11.txt')
pathlib.Path('a11.txt').write_text(response.text)

# Upload file using top-level function
my_file = genai.upload_file(path='a11.txt')

model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content([
    'Can you summarize this file:',
    my_file # Pass the file object
])
print(response.text)
```

#### After

```python
import requests
import pathlib
from google import genai

client = genai.Client()

# Download file
response = requests.get(
    'https://storage.googleapis.com/generativeai-downloads/data/a11.txt')
pathlib.Path('a11.txt').write_text(response.text)

# Upload file using client method
my_file = client.files.upload(file='a11.txt')

response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents=[
        'Can you summarize this file:',
        my_file # Pass the file object
    ]
)
print(response.text)
```

### List and get

List uploaded files and get an uploaded file with a file name:

#### Before

```python
import google.generativeai as genai

# List using top-level function
for file in genai.list_files():
  print(file.name)

# Get using top-level function (assuming file.name is valid)
file_to_get = genai.get_file(name=file.name)
print(f"Got file: {file_to_get.name}")
```

#### After

```python
from google import genai
client = genai.Client()

# List using client method
for file in client.files.list():
    print(file.name)

# Get using client method (assuming file.name is valid)
file_to_get = client.files.get(name=file.name)
print(f"Got file: {file_to_get.name}")
```

### Delete

Delete a file:

#### Before

```python
import pathlib
import google.generativeai as genai

# Create a dummy file for deletion
dummy = "This is dummy content."
pathlib.Path('dummy.txt').write_text(dummy)
dummy_file = genai.upload_file(path='dummy.txt')
print(f"Uploaded: {dummy_file.name}")

# Delete using top-level function
genai.delete_file(name=dummy_file.name)
print(f"Deleted: {dummy_file.name}")
```

#### After

```python
import pathlib
from google import genai

client = genai.Client()

# Create a dummy file for deletion
dummy = "This is dummy content."
pathlib.Path('dummy.txt').write_text(dummy)
dummy_file = client.files.upload(file='dummy.txt')
print(f"Uploaded: {dummy_file.name}")

# Delete using client method
response = client.files.delete(name=dummy_file.name)
print(f"Deleted: {dummy_file.name}")
# response is typically empty on success
```

## Context caching

Context caching allows the user to pass the content to the model once, cache the input tokens, and then refer to the cached tokens in subsequent calls to lower the cost.

#### Before

```python
import requests
import pathlib
import google.generativeai as genai
from google.generativeai import caching

# Download file
response = requests.get(
    'https://storage.googleapis.com/generativeai-downloads/data/a11.txt')
pathlib.Path('a11.txt').write_text(response.text)

# Upload file
document = genai.upload_file(path="a11.txt")

# Create cache using caching module
apollo_cache = caching.CachedContent.create(
    model="models/gemini-1.5-flash-001", # Note: Model name format might differ slightly
    system_instruction="You are an expert at analyzing transcripts.",
    contents=[document],
    display_name="apollo_cache_example" # Example display name
)
print(f"Created cache: {apollo_cache.name}")

# Generate response using model from cache
apollo_model = genai.GenerativeModel.from_cached_content(
    cached_content=apollo_cache
)
response = apollo_model.generate_content("Find a lighthearted moment from this transcript")
print(response.text)
```

#### After

```python
import requests
import pathlib
from google import genai
from google.genai import types

client = genai.Client()

# Check which models support caching.
print("Models supporting caching:")
for m in client.models.list():
  if "createCachedContent" in m.supported_generation_methods: # Check method support
      print(m.name)

# Download file
response = requests.get(
    'https://storage.googleapis.com/generativeai-downloads/data/a11.txt')
pathlib.Path('a11.txt').write_text(response.text)

# Upload file
document = client.files.upload(file='a11.txt')

# Create cache using client method
model_name='gemini-1.5-flash-001' # Use the specific model name
apollo_cache = client.caches.create(
      model=model_name,
      config=types.CreateCachedContentConfig( # Use config object
          contents=[document],
          system_instruction='You are an expert at analyzing transcripts.',
          display_name="apollo_cache_example" # Example display name
      ),
  )
print(f"Created cache: {apollo_cache.name}")

# Generate response referencing cache name in config
response = client.models.generate_content(
    model=model_name,
    contents='Find a lighthearted moment from this transcript',
    config=types.GenerateContentConfig(
        cached_content=apollo_cache.name,
    )
)
print(response.text)
```

## Count tokens

Count the number of tokens in a request.

#### Before

```python
import google.generativeai as genai

model = genai.GenerativeModel('gemini-1.5-flash')
response = model.count_tokens(
    'The quick brown fox jumps over the lazy dog.')
print(response) # e.g., total_tokens: 10
```

#### After

```python
from google import genai

client = genai.Client()

response = client.models.count_tokens(
    model='gemini-2.0-flash', # Or appropriate model
    contents='The quick brown fox jumps over the lazy dog.',
)
print(response) # e.g., total_tokens: 10
```

## Generate images

Generate images:

#### Before

```python
# Requires separate installation:
# pip install google-generativeai[imagen] # Or similar based on actual package structure
import google.generativeai as genai
import pathlib # For saving

# Assuming Imagen client setup if needed, or direct model access
imagen = genai.ImageGenerationModel("imagen-3.0-generate-001") # Hypothetical old SDK access
gen_images = imagen.generate_images(
    prompt="Robot holding a red skateboard",
    number_of_images=1,
    safety_filter_level="block_low_and_above",
    person_generation="allow_adult",
    aspect_ratio="3:4",
)

# Process results (structure might differ)
# for n, image_data in enumerate(gen_images.images): # Hypothetical structure
#     pathlib.Path(f'{n}_old.png').write_bytes(image_data.bytes)
```

#### After

```python
from google import genai
from google.genai import types # For config
import pathlib # For saving

client = genai.Client()

gen_images = client.models.generate_images(
    model='imagen-3.0-generate-001',
    prompt='Robot holding a red skateboard',
    config=types.GenerateImagesConfig( # Use config object
        number_of_images= 1,
        safety_filter_level= "BLOCK_LOW_AND_ABOVE",
        person_generation= "ALLOW_ADULT",
        aspect_ratio= "ASPECT_RATIO_3_4", # Use enum-like string
    )
)

# Process results using the new structure
for n, image in enumerate(gen_images.generated_images):
    # Assuming image.image contains the bytes directly or via an attribute
    # Adjust based on the actual structure of `image` object
    if hasattr(image, 'image_bytes'):
         pathlib.Path(f'{n}_new.png').write_bytes(image.image_bytes)
    elif hasattr(image, 'image') and hasattr(image.image, 'image_bytes'):
         pathlib.Path(f'{n}_new.png').write_bytes(image.image.image_bytes)
    else:
         print(f"Could not find image bytes for image {n}")

```

## Embed content

Generate content embeddings.

#### Before

```python
import google.generativeai as genai

response = genai.embed_content(
   model='models/text-embedding-004',
   content='Hello world'
)
print(response['embedding']) # Access embedding list
```

#### After

```python
from google import genai

client = genai.Client()

response = client.models.embed_content(
   model='text-embedding-004', # Simpler model name often works
   contents='Hello world',
)
print(response.embedding) # Access embedding list via attribute
```

## Tune a Model

Create and use a tuned model.

The new SDK simplifies tuning with `client.tunings.tune`, which launches the tuning job and polls until the job is complete.

#### Before

```python
import google.generativeai as genai
import random
import time

# Create tuning data (example format)
train_data = {}
for i in range(1, 6):
   key = f'input {i}'
   value = f'output {i}'
   train_data[key] = value # Dict format might vary

# Create tuning job using top-level function
name = f'generate-num-{random.randint(0,10000)}'
operation = genai.create_tuned_model(
    source_model='models/gemini-1.5-flash-001', # Base model for tuning
    training_data=train_data,
    id = name, # Tuned model ID
    epoch_count = 5,
    batch_size=4,
    learning_rate=0.001,
)
print(f"Started tuning job: {operation.operation.name}")

# Wait for tuning complete (manual polling might be needed)
while not operation.done():
    print("Waiting for tuning...")
    time.sleep(60)
    operation.refresh() # Refresh operation status

tuning_result = operation.result() # Get the tuned model info
tuned_model_name = tuning_result.name # Extract the tuned model name
print(f"Tuning complete. Tuned model: {tuned_model_name}")


# Generate content with the tuned model
model = genai.GenerativeModel(model_name=tuned_model_name) # Use full name
response = model.generate_content('input 55') # Example input
print(response.text)
```

#### After

```python
from google import genai
from google.genai import types
import random

client = genai.Client()

# Check which models are available for tuning.
print("Models available for tuning:")
for m in client.models.list():
  if "createTunedModel" in m.supported_generation_methods: # Check method support
      print(m.name)

# Create tuning dataset using types module
training_dataset=types.TuningDataset(
        examples=[
            types.TuningExample(
                text_input=f'input {i}',
                output=f'output {i}',
            )
            for i in range(5)
        ],
    )

# Start tuning job using client method (polls automatically)
tuning_job = client.tunings.tune(
    base_model='models/gemini-1.5-flash-001', # Base model for tuning
    training_dataset=training_dataset,
    config=types.CreateTuningJobConfig( # Use config object
        epoch_count= 5,
        batch_size=4,
        learning_rate=0.001,
        tuned_model_display_name=f"test-tuned-model-{random.randint(0,10000)}" # Optional display name
    )
)
# The 'tune' method blocks until completion and returns the completed job object
print(f"Tuning complete. Tuned model: {tuning_job.tuned_model.model}")

# Generate content with the tuned model
response = client.models.generate_content(
    model=tuning_job.tuned_model.model, # Use the model name from the job result
    contents='input 55', # Example input
)
print(response.text)
```
