from fastapi import FastAPI
from schema import SemanticRequest
from parser import parse

app = FastAPI()


@app.post("/semantic/parse")
def semantic_parse(req: SemanticRequest):
    return parse(req.query)
