import os
import json
import time
import urllib3
from typing import ClassVar, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage
from langchain_core.tools import BaseTool
from langgraph.graph.state import CompiledStateGraph

class CoreAPIWrapper(BaseModel):
    """Simple wrapper around the CORE API."""
    base_url: ClassVar[str] = "https://api.core.ac.uk/v3"
    top_k_results: int = Field(description="Top k results obtained by running a query on Core", default=1)

    def _get_search_response(self, query: str) -> dict:
        api_key = os.environ.get("CORE_API_KEY", "")
        if not api_key:
            raise ValueError("CORE_API_KEY is not set. Please set it in your environment or .env file.")
        
        http = urllib3.PoolManager()
        max_retries = 5    
        for attempt in range(max_retries):
            response = http.request(
                'GET',
                f"{self.base_url}/search/outputs", 
                headers={"Authorization": f"Bearer {api_key}"}, 
                fields={"q": query, "limit": self.top_k_results}
            )
            if 200 <= response.status < 300:
                return json.loads(response.data.decode('utf-8'))
            elif attempt < max_retries - 1:
                time.sleep(2 ** (attempt + 2))
            else:
                raise Exception(f"Got non 2xx response from CORE API: {response.status} {response.data.decode('utf-8')}")

    def search(self, query: str) -> str:
        response = self._get_search_response(query)
        results = response.get("results", [])
        if not results:
            return "No relevant results were found"

        # Format the results in a string
        docs = []
        for result in results:
            published_date_str = result.get('publishedDate') or result.get('yearPublished', '')
            authors_str = ' and '.join([item['name'] for item in result.get('authors', [])])
            docs.append((
                f"* ID: {result.get('id', '')},\n"
                f"* Title: {result.get('title', '')},\n"
                f"* Published Date: {published_date_str},\n"
                f"* Authors: {authors_str},\n"
                f"* Abstract: {result.get('abstract', '')},\n"
                f"* Paper URLs: {result.get('sourceFulltextUrls') or result.get('downloadUrl', '')}"
            ))
        return "\n-----\n".join(docs)

def format_tools_description(tools: list[BaseTool]) -> str:
    return "\n\n".join([f"- {tool.name}: {tool.description}\n Input arguments: {tool.args}" for tool in tools])

async def print_stream(app: CompiledStateGraph, input_query: str) -> Optional[BaseMessage]:
    print("\n" + "="*50)
    print("## New research running")
    print(f"### Input:\n\n{input_query}\n")
    print("### Stream:\n")

    # Stream the results 
    all_messages = []
    async for chunk in app.astream({"messages": [input_query]}, stream_mode="updates"):
        for updates in chunk.values():
            if messages := updates.get("messages"):
                all_messages.extend(messages)
                for message in messages:
                    message.pretty_print()
                    print("\n")
 
    # Return the last message if any
    if not all_messages:
        return None
    return all_messages[-1]
