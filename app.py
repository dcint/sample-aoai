import json
import os
import logging
import requests
import openai
from flask import Flask, Response, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

@app.route("/", defaults={"path": "index.html"})
@app.route("/<path:path>")
def static_file(path):
    return app.send_static_file(path)

# ACS Integration Settings
AZURE_SEARCH_SERVICE = os.environ.get("AZURE_SEARCH_SERVICE")
AZURE_SEARCH_INDEX = os.environ.get("AZURE_SEARCH_INDEX")
AZURE_SEARCH_KEY = os.environ.get("AZURE_SEARCH_KEY")
AZURE_SEARCH_USE_SEMANTIC_SEARCH = os.environ.get("AZURE_SEARCH_USE_SEMANTIC_SEARCH", "false")
AZURE_SEARCH_SEMANTIC_SEARCH_CONFIG = os.environ.get("AZURE_SEARCH_SEMANTIC_SEARCH_CONFIG", "default")
AZURE_SEARCH_TOP_K = os.environ.get("AZURE_SEARCH_TOP_K", 5)
AZURE_SEARCH_ENABLE_IN_DOMAIN = os.environ.get("AZURE_SEARCH_ENABLE_IN_DOMAIN", "true")
AZURE_SEARCH_CONTENT_COLUMNS = os.environ.get("AZURE_SEARCH_CONTENT_COLUMNS")
AZURE_SEARCH_FILENAME_COLUMN = os.environ.get("AZURE_SEARCH_FILENAME_COLUMN")
AZURE_SEARCH_TITLE_COLUMN = os.environ.get("AZURE_SEARCH_TITLE_COLUMN")
AZURE_SEARCH_URL_COLUMN = os.environ.get("AZURE_SEARCH_URL_COLUMN")

# AOAI Integration Settings
AZURE_OPENAI_RESOURCE = os.environ.get("AZURE_OPENAI_RESOURCE")
AZURE_OPENAI_MODEL = os.environ.get("AZURE_OPENAI_MODEL")
AZURE_OPENAI_KEY = os.environ.get("AZURE_OPENAI_KEY")
AZURE_OPENAI_TEMPERATURE = os.environ.get("AZURE_OPENAI_TEMPERATURE", 0)
AZURE_OPENAI_TOP_P = os.environ.get("AZURE_OPENAI_TOP_P", 1.0)
AZURE_OPENAI_MAX_TOKENS = os.environ.get("AZURE_OPENAI_MAX_TOKENS", 1000)
AZURE_OPENAI_STOP_SEQUENCE = os.environ.get("AZURE_OPENAI_STOP_SEQUENCE")
AZURE_OPENAI_SYSTEM_MESSAGE = os.environ.get("AZURE_OPENAI_SYSTEM_MESSAGE", "You are an AI assistant that helps people find information.")
AZURE_OPENAI_PREVIEW_API_VERSION = os.environ.get("AZURE_OPENAI_PREVIEW_API_VERSION", "2023-06-01-preview")
AZURE_OPENAI_STREAM = os.environ.get("AZURE_OPENAI_STREAM", "true")
AZURE_OPENAI_MODEL_NAME = os.environ.get("AZURE_OPENAI_MODEL_NAME", "gpt-35-turbo") # Name of the model, e.g. 'gpt-35-turbo' or 'gpt-4'

SHOULD_STREAM = True if AZURE_OPENAI_STREAM.lower() == "true" else False

def is_chat_model():
    if 'gpt-4' in AZURE_OPENAI_MODEL_NAME.lower() or AZURE_OPENAI_MODEL_NAME.lower() in ['gpt-35-turbo-4k', 'gpt-35-turbo-16k']:
        return True
    return False

def should_use_data():
    if AZURE_SEARCH_SERVICE and AZURE_SEARCH_INDEX and AZURE_SEARCH_KEY:
        return True
    return False

def prepare_body_headers_with_data(request):
    request_messages = request.json["messages"]

    body = {
        "messages": request_messages,
        "temperature": float(AZURE_OPENAI_TEMPERATURE),
        "max_tokens": int(AZURE_OPENAI_MAX_TOKENS),
        "top_p": float(AZURE_OPENAI_TOP_P),
        "stop": AZURE_OPENAI_STOP_SEQUENCE.split("|") if AZURE_OPENAI_STOP_SEQUENCE else None,
        "stream": SHOULD_STREAM,
        "dataSources": [
            {
                "type": "AzureCognitiveSearch",
                "parameters": {
                    "endpoint": f"https://{AZURE_SEARCH_SERVICE}.search.windows.net",
                    "key": AZURE_SEARCH_KEY,
                    "indexName": AZURE_SEARCH_INDEX,
                    "fieldsMapping": {
                        "contentField": AZURE_SEARCH_CONTENT_COLUMNS.split("|") if AZURE_SEARCH_CONTENT_COLUMNS else [],
                        "titleField": AZURE_SEARCH_TITLE_COLUMN if AZURE_SEARCH_TITLE_COLUMN else None,
                        "urlField": AZURE_SEARCH_URL_COLUMN if AZURE_SEARCH_URL_COLUMN else None,
                        "filepathField": AZURE_SEARCH_FILENAME_COLUMN if AZURE_SEARCH_FILENAME_COLUMN else None
                    },
                    "inScope": True if AZURE_SEARCH_ENABLE_IN_DOMAIN.lower() == "true" else False,
                    "topNDocuments": AZURE_SEARCH_TOP_K,
                    "queryType": "semantic" if AZURE_SEARCH_USE_SEMANTIC_SEARCH.lower() == "true" else "simple",
                    "semanticConfiguration": AZURE_SEARCH_SEMANTIC_SEARCH_CONFIG if AZURE_SEARCH_USE_SEMANTIC_SEARCH.lower() == "true" and AZURE_SEARCH_SEMANTIC_SEARCH_CONFIG else "",
                    "roleInformation": AZURE_OPENAI_SYSTEM_MESSAGE
                }
            }
        ]
    }

    chatgpt_url = f"{AZURE_OPENAI_RESOURCE}deployments/{AZURE_OPENAI_MODEL}"
    if is_chat_model():
        chatgpt_url += "/chat/completions?api-version=2023-03-15-preview"
    else:
        chatgpt_url += "/completions?api-version=2023-03-15-preview"

    headers = {
        'Content-Type': 'application/json',
        'api-key': AZURE_OPENAI_KEY,
        'chatgpt_url': chatgpt_url,
        'chatgpt_key': AZURE_OPENAI_KEY,
        'Authorization': 'Bearer ' + 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6Ii1LSTNROW5OUjdiUm9meG1lWm9YcWJIWkdldyIsImtpZCI6Ii1LSTNROW5OUjdiUm9meG1lWm9YcWJIWkdldyJ9.eyJhdWQiOiJhcGk6Ly80ODA5ZDNiMy02ZmM0LTQ4NmYtYmYyMi1kZDBmZTA3YWRlYTgiLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC9iZDhjMDZhNS1hZmIwLTRjMjctOWI0NS03NzM1MzQzN2JjZGQvIiwiaWF0IjoxNjkxOTMwMjMwLCJuYmYiOjE2OTE5MzAyMzAsImV4cCI6MTY5MTkzNTYxMywiYWNyIjoiMSIsImFpbyI6IkFVUUF1LzhVQUFBQWFuTkVQRWVINUJRd0p0ZitNY0NJekZyT3picWdDV1o3TmpuZnZUQ3RpNzVLaUhuUXRxSXZjdCtDNngxRTJVUHc5eGRMcGRHR3FLNWRCVkQzNzZIaDNnPT0iLCJhbXIiOlsicHdkIl0sImFwcGlkIjoiMTUxOGVhNWYtMWJlMy00N2I1LTkzZmMtMjYzMDQ5Y2RlOTI2IiwiYXBwaWRhY3IiOiIxIiwiZW1haWwiOiJkYXZpZEBjaW50cm9uLmlvIiwiaWRwIjoiaHR0cHM6Ly9zdHMud2luZG93cy5uZXQvMzhjZjQyMzAtZWMyMS00YTUwLWEyYjUtMGUzNmY0ZTdjN2Y2LyIsImlwYWRkciI6Ijk4LjIxMi4xODEuMTc2IiwibmFtZSI6IkRhdmlkIENpbnRyb24iLCJvaWQiOiI2MTVkYzhkZi04MmVlLTRmZDUtYTQ5NS05NTdmNjA5NGQxMDciLCJyaCI6IjAuQVZrQXBRYU12YkN2SjB5YlJYYzFORGU4M2JQVENVakViMjlJdnlMZEQtQjYzcWlkQURBLiIsInJvbGVzIjpbInNwbiJdLCJzY3AiOiJvcGVuYWkuYmFja2VuZC5yZWFkIiwic3ViIjoiZVZlbWF6eE9QdXZ6ZWxrOEgyU1F4dDdEVmxZQ3AzS1ZObkNoT3RjdzNKUSIsInRpZCI6ImJkOGMwNmE1LWFmYjAtNGMyNy05YjQ1LTc3MzUzNDM3YmNkZCIsInVuaXF1ZV9uYW1lIjoiZGF2aWRAY2ludHJvbi5pbyIsInV0aSI6Im92cWVTS3hTSEU2di0yN1g1MXFTQUEiLCJ2ZXIiOiIxLjAifQ.ngcLxuHqFgVJOey8bElCFGbyB9zJvAGaH69hDZdZBrzAHPp4YRjos3M-PFaI9VHdVc-Bqlqbtx5lanG-LmfATtI8cZOTzdKf36JThai3tdZfWjBa6BI-V-XNiJeUHGpdROsupznJW_J-LBczCIqE1jeiUJohCgkgNcZpXs7oR_qldxcuqzM0QjcNzTo3vsETiX2AlllvMiElAwwbBut2jBKHmDcNUtJntWQDzg4MjDhom3bYHJ4-TqXi_vcmfut2T2dhDBEnE_lwbVkFAFKSNUPtcPO5alw3pHsVKLPVvJ5ELosqzm-bQZARx6Telpq9X8-BJ5q3DpFo544jqXRuXw',
        "x-ms-useragent": "GitHubSampleWebApp/PublicAPI/1.0.0"
    }

    return body, headers


def stream_with_data(body, headers, endpoint):
    s = requests.Session()
    response = {
        "id": "",
        "model": "",
        "created": 0,
        "object": "",
        "choices": [{
            "messages": []
        }]
    }
    try:
        with s.post(endpoint, json=body, headers=headers, stream=True) as r:
            for line in r.iter_lines(chunk_size=10):
                if line:
                    lineJson = json.loads(line.lstrip(b'data:').decode('utf-8'))
                    if 'error' in lineJson:
                        yield json.dumps(lineJson).replace("\n", "\\n") + "\n"
                    response["id"] = lineJson["id"]
                    response["model"] = lineJson["model"]
                    response["created"] = lineJson["created"]
                    response["object"] = lineJson["object"]

                    role = lineJson["choices"][0]["messages"][0]["delta"].get("role")
                    if role == "tool":
                        response["choices"][0]["messages"].append(lineJson["choices"][0]["messages"][0]["delta"])
                    elif role == "assistant": 
                        response["choices"][0]["messages"].append({
                            "role": "assistant",
                            "content": ""
                        })
                    else:
                        deltaText = lineJson["choices"][0]["messages"][0]["delta"]["content"]
                        if deltaText != "[DONE]":
                            response["choices"][0]["messages"][1]["content"] += deltaText

                    yield json.dumps(response).replace("\n", "\\n") + "\n"
    except Exception as e:
        yield json.dumps({"error": str(e)}).replace("\n", "\\n") + "\n"


def conversation_with_data(request):
    body, headers = prepare_body_headers_with_data(request)
    endpoint = f"{AZURE_OPENAI_RESOURCE}deployments/{AZURE_OPENAI_MODEL}/extensions/chat/completions?api-version={AZURE_OPENAI_PREVIEW_API_VERSION}"
    
    if not SHOULD_STREAM:
        r = requests.post(endpoint, headers=headers, json=body)
        status_code = r.status_code
        r = r.json()

        return Response(json.dumps(r).replace("\n", "\\n"), status=status_code)
    else:
        if request.method == "POST":
            return Response(stream_with_data(body, headers, endpoint), mimetype='text/event-stream')
        else:
            return Response(None, mimetype='text/event-stream')

def stream_without_data(response):
    responseText = ""
    for line in response:
        deltaText = line["choices"][0]["delta"].get('content')
        if deltaText and deltaText != "[DONE]":
            responseText += deltaText

        response_obj = {
            "id": line["id"],
            "model": line["model"],
            "created": line["created"],
            "object": line["object"],
            "choices": [{
                "messages": [{
                    "role": "assistant",
                    "content": responseText
                }]
            }]
        }
        yield json.dumps(response_obj).replace("\n", "\\n") + "\n"


def conversation_without_data(request):
    openai.api_type = "azure"
    openai.api_base = f"{AZURE_OPENAI_RESOURCE}"
    openai.api_version = "2023-03-15-preview"
    openai.api_key = AZURE_OPENAI_KEY
    openai.api_token = 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6Ii1LSTNROW5OUjdiUm9meG1lWm9YcWJIWkdldyIsImtpZCI6Ii1LSTNROW5OUjdiUm9meG1lWm9YcWJIWkdldyJ9.eyJhdWQiOiJhcGk6Ly80ODA5ZDNiMy02ZmM0LTQ4NmYtYmYyMi1kZDBmZTA3YWRlYTgiLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC9iZDhjMDZhNS1hZmIwLTRjMjctOWI0NS03NzM1MzQzN2JjZGQvIiwiaWF0IjoxNjkxOTM5NzQyLCJuYmYiOjE2OTE5Mzk3NDIsImV4cCI6MTY5MTk0NDk3NiwiYWNyIjoiMSIsImFpbyI6IkFVUUF1LzhVQUFBQU02THJ4SHhSZE9jZS9UK2IrM2kwbGU1cVBxSEg1ZzI4bHVrYlhDVmpTUXN2eDRDOWVJbTM0UWw4RUsvTVBjaE9kb3R0dDNLRGNJY3luY1ZpRGVwSzBRPT0iLCJhbXIiOlsicHdkIl0sImFwcGlkIjoiMTUxOGVhNWYtMWJlMy00N2I1LTkzZmMtMjYzMDQ5Y2RlOTI2IiwiYXBwaWRhY3IiOiIxIiwiZW1haWwiOiJkYXZpZEBjaW50cm9uLmlvIiwiaWRwIjoiaHR0cHM6Ly9zdHMud2luZG93cy5uZXQvMzhjZjQyMzAtZWMyMS00YTUwLWEyYjUtMGUzNmY0ZTdjN2Y2LyIsImlwYWRkciI6Ijk4LjIxMi4xODEuMTc2IiwibmFtZSI6IkRhdmlkIENpbnRyb24iLCJvaWQiOiI2MTVkYzhkZi04MmVlLTRmZDUtYTQ5NS05NTdmNjA5NGQxMDciLCJyaCI6IjAuQVZrQXBRYU12YkN2SjB5YlJYYzFORGU4M2JQVENVakViMjlJdnlMZEQtQjYzcWlkQURBLiIsInJvbGVzIjpbInNwbiJdLCJzY3AiOiJvcGVuYWkuYmFja2VuZC5yZWFkIiwic3ViIjoiZVZlbWF6eE9QdXZ6ZWxrOEgyU1F4dDdEVmxZQ3AzS1ZObkNoT3RjdzNKUSIsInRpZCI6ImJkOGMwNmE1LWFmYjAtNGMyNy05YjQ1LTc3MzUzNDM3YmNkZCIsInVuaXF1ZV9uYW1lIjoiZGF2aWRAY2ludHJvbi5pbyIsInV0aSI6IjBzRWVnc2lCU1VPNkhHZWRnNUtmQUEiLCJ2ZXIiOiIxLjAifQ.LBNt1M2JPj87-rOcRtN6H60kmqESFeS50-LI7nQMBqU-40GnWz_UZqT5QFzdoE-his-Z3Ue56Ipnib0FrnHyhdw1iM4qDEoqBJku3AvtkRKe5LZ9afWyZfvDB-8gwQh1eINnqbh43004y3Cl0qbkwct7nhb1dszWAPQZ5ZaLAEEmkW2G8h-h_cYHXzPYnx_Y2lW0RCK6IZgsSuHk4jfGo9QACwIbaGgGJtXsOJz_rV0lSYa063GkZ8sBx0rVyLxqYvc-8ApCleQf6JY8-1h-ImdjxTwf8yQYa5iNhxk4HU3n-TstxMbshgUUc1qrDxKjLQRTgBqUNlE0oza-_obnNQ'
    
    headers = { 
        'Authorization': request.headers.get('Authorization') ##openai.api_token
    }
    request_messages = request.json["messages"]
    messages = [
        {
            "role": "system",
            "content": AZURE_OPENAI_SYSTEM_MESSAGE
        }
    ]

    for message in request_messages:
        messages.append({
            "role": message["role"] ,
            "content": message["content"]
        })

    response = openai.ChatCompletion.create(
        engine=AZURE_OPENAI_MODEL,
        messages = messages,
        temperature=float(AZURE_OPENAI_TEMPERATURE),
        max_tokens=int(AZURE_OPENAI_MAX_TOKENS),
        top_p=float(AZURE_OPENAI_TOP_P),
        stop=AZURE_OPENAI_STOP_SEQUENCE.split("|") if AZURE_OPENAI_STOP_SEQUENCE else None,
        stream=SHOULD_STREAM,
        headers=headers
    )

    if not SHOULD_STREAM:
        response_obj = {
            "id": response,
            "model": response.model,
            "created": response.created,
            "object": response.object,
            "choices": [{
                "messages": [{
                    "role": "assistant",
                    "content": response.choices[0].message.content
                }]
            }]
        }

        return jsonify(response_obj), 200
    else:
        if request.method == "POST":
            return Response(stream_without_data(response), mimetype='text/event-stream')
        else:
            return Response(None, mimetype='text/event-stream')
        
# def refresh_tokens():
#     refresh_url = "https://cintron-openai.azurewebsites.net/.auth/refresh"
#     response = requests.post(refresh_url)
#     if response.status_code == 200:
#         print("Token refresh completed successfully.")
#     else:
#         print("Token refresh failed. See application logs for details.")

@app.route("/conversation", methods=["GET", "POST"])
def conversation():
    try:
        use_data = should_use_data()
        if use_data:
            return conversation_with_data(request)
        else:
            return conversation_without_data(request)
    except Exception as e:
        logging.exception("Exception in /conversation")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run()