from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from langchain_groq import ChatGroq
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent


# ---------------- DATABASE ---------------- #
db = SQLDatabase.from_uri("sqlite:///my_tasks.db")

db.run("""
CREATE TABLE IF NOT EXISTS tasks(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT CHECK(status IN('pending','in_progress','completed')) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

system_prompt = """
You are an AI assistant that manages tasks using a SQL database.

Use tools to interact with the database when needed.
Write correct SQL queries.

The database has a table 'tasks' with:
id, title, description, status, created_at.

Limit SELECT queries to 10 rows.
"""

# ---------------- MODEL ---------------- #
llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0
)

toolkit = SQLDatabaseToolkit(db=db, llm=llm)
tools = toolkit.get_tools()


# ---------------- AGENT ---------------- #
@st.cache_resource
def get_agent():
    agent = create_agent(
        model=llm,
        tools=tools,
        checkpointer=InMemorySaver(),
        system_prompt=system_prompt
    )
    return agent

agent = get_agent()


# ---------------- UI CONFIG ---------------- #
st.set_page_config(
    page_title="Todo AI Assistant",
    page_icon="🧠",
    layout="centered"
)

st.title("🧠 Todo AI Assistant")
st.caption("Manage your tasks using natural language 🚀")


# ---------------- SESSION STATE ---------------- #
if "messages" not in st.session_state:
    st.session_state.messages = []


# ---------------- DISPLAY CHAT ---------------- #
chat_container = st.container()

with chat_container:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])


# ---------------- INPUT ---------------- #
prompt = st.chat_input("Ask me to manage your tasks...")

if prompt:
    # USER MESSAGE
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with chat_container:
        with st.chat_message("user"):
            st.markdown(prompt)

        # AI RESPONSE
        with st.chat_message("assistant"):
            with st.spinner("🤖 Thinking..."):
                response = agent.invoke(
                    {"messages": [{"role": "user", "content": prompt}]},
                    {"configurable": {"thread_id": "1"}}
                )

                result = response["messages"][-1].content

                st.markdown(result)

                # Save response
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result
                })


# ---------------- SIDEBAR ---------------- #
with st.sidebar:
    st.header("⚙️ Controls")

    if st.button("🧹 Clear Chat"):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")

    st.markdown("### 💡 Example Prompts")
    st.markdown("""
- Add task: Finish ML project  
- Show my tasks  
- Mark task 1 as completed  
- Delete task 2  
""")