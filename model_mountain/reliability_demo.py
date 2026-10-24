"""Runnable secure RAG fixture to accompany Model Mountain's existing threat demonstrations."""
from .evaluation import run_fixture
import json

if __name__=='__main__':
    result=run_fixture()
    print(json.dumps(result,indent=2))
