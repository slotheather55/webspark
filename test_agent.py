#!/usr/bin/env python3
"""
test_agent.py

Run a browser-use AI agent for a given task prompt, record all actions, and save history to a JSON file.
"""

import os
import sys
import asyncio
from dotenv import load_dotenv
import base64
import time
from pathlib import Path

# Ensure browser-use library is on the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'browser-use'))

from langchain_openai import ChatOpenAI
from browser_use import Agent

async def main(task_prompt: str = None):
    load_dotenv()
    if task_prompt is None:
        # Hardcoded default task: navigate and add to cart
        task_prompt = "Click on https://www.penguinrandomhouse.com/books/536247/devotions-a-read-with-jenna-pick-by-mary-oliver/ and then add to cart."
    llm = ChatOpenAI(model="gpt-4o")
    agent = Agent(task=task_prompt, llm=llm)
    history = await agent.run(max_steps=50)

    # save screenshots externally
    screenshot_dir = Path(__file__).parent / 'browser-use' / 'dom_state_data'
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    for idx, h in enumerate(history.history):
        b64 = h.state.screenshot
        if b64:
            file_name = f"dom_state_{int(time.time())}_{idx}.png"
            file_path = screenshot_dir / file_name
            with open(file_path, 'wb') as f:
                f.write(base64.b64decode(b64))
            # update JSON reference
            h.state.screenshot = str(file_path)

    history.save_to_file("out.json")
    print("Done. History saved to out.json; screenshots in dom_state_data")

if __name__ == '__main__':
    import sys
    # Allow passing task prompt via CLI argument
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else None))
