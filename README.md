# Singlebase Python SDK

Singlebase's Python SDK

## Usage 

### Install 

```
pip install singlebase
```

### Create Client

```py

from singlebase import Client as create_client

API_URL = "https://cloud.singlebaseapis.com/api/[[ACCESS-PATH-KEY]]"
API_KEY = "[[YOUR-SECURE-API-KEY]]"

# create client
sb_client = create_client(
    api_url=API_URL, 
    api_key=API_KEY
)

```

### Methods

#### Sync 

- `client.request(payload:dict)`
- `client.db(action:str, collection:str, payload:dict={})`
- `client.auth(action:str, payload:dict={})`
- `client.storage(action:str, payload:dict={})`
- `client.genai(action:str, payload:dict={})`
- `client.vectordb(action:str, payload:dict={})`


#### Async 

- `client.request_async(payload:dict)`
- `client.db_async(action:str, collection:str, payload:dict={})`
- `client.auth_async(action:str, payload:dict={})`
- `client.storage_async(action:str, payload:dict={})`
- `client.genai_async(action:str, payload:dict={})`
- `client.vectordb_async(action:str, payload:dict={})`



### Examples

```py

### === Datastore

# db.fetch (fetch all)
res = sbc_client.db("fetch", "articles") 

# res:Result|ResultOK|ResultError
if res.ok:
  for entry:dict in res.data: # res.data:[dict, ...]
    _key = entry.get("_key")
    title = entry.get("title")
    print(f" Article _key: {_key} - Title: {title}")

# db.fetch by _key 
res = sbc_client.db("fetch", "articles", {"_key": 1234}) 

# db.fetch by criteria. returns 5 entries
res = sbc_client.db("fetch", "articles", {
  "filter": {
    "author": "author-name",
  },
  "limit": 5
}) 


# db.insert
res = sb_client.db('insert', 'articles', {"title": "Hello", "content": "..."})

# res:Result|ResultOK|ResultError
if res.ok:
  print("Document created. _key: %s" % res.data[0].get("_key"))

# db.update
sb_client.db("update", 'articles', {"_key": "124", "summary": "something"})

# db.upsert
sb_client.db("upsert", 'articles', {
    "filter": { 
      "slug": "my-unique-slug"
    },
    "update": {
      "count:$inc": True
    },
    "insert": {
      "slug": "my-unique-slug",
      "title": "Hello",
      "content": "World"
    }
  })

# db.count
sb_client.db("count", 'articles')

# db.delete
sb_client.db("delete", 'articles', {"_key": "124"})

# db.archive
sb_client.db("archive", 'articles', {"_key": "124"})

# db.restore
sb_client.db("restore", 'articles', {"_key": "124"})

# ------------

### === Auth

# auth.signin
sb_client.auth('signin', {"email": "", "password": ""})
# all other methods follow the same pattern

# ------------

### === Storage

# storage.get
sbc_client.storage('get', {"_key": 1234})

# storage.delete
sbc_client.storage('delete', {"_key": 1234})

sbc_client.storage('convert_to_md', {"_key": 1234})

# ------------

### === GenAI

# genai.summarize
sbc_client.genai('summarize', {"input": "long-text..."})

# genai.gentext 
sbc_client.genai('gentext', {"input": "the prompt"})

# genai.qna - Knowledge Base/Q&A
sbc_client.genai('qna', {
  "collection": "articles",
  "_key": "datakey",
  "input": "the question",
})


--- 

