from langchain_openai import ChatOpenAI
from browser_use import Agent
import asyncio
from dotenv import load_dotenv
load_dotenv()

async def main():
    agent = Agent(
        task="https://www.penguinrandomhouse.com/books/536247/devotions-a-read-with-jenna-pick-by-mary-oliver/ Go to this URL and click on add to cart. ",
        llm=ChatOpenAI(model="gpt-4o"),
    )
    await agent.run()

asyncio.run(main()) 