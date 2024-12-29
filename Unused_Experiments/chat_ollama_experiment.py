from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage


llm = ChatOllama(
    model="llama3.1",
    temperature=0,
    # other params...
)



messages = [
    (
        "system",
        "You are a helpful assistant that translates English to Spanish. Translate the user sentence.",
    ),
    ("human", "I love programming."),
]
ai_msg = llm.invoke(messages)

ai_msg


print(ai_msg.content)

