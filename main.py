import sys
import json
import pprint

from llama_index.llms.ollama import Ollama
from llama_index.core import Settings
from llama_index.core.tools import QueryEngineTool
from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    String,
    Integer,
    select,
    column,
)
from llama_index.core import SQLDatabase
from sqlalchemy import insert
from llama_index.core.query_engine import NLSQLTableQueryEngine
from llama_index.core import PromptTemplate


def test_ollama_llm(llm):
    # template = (
    #     "We have provided context information below. \n"
    #     "---------------------\n"
    #     "{context_str}"
    #     "\n---------------------\n"
    #     "Given this information, please answer the question: {query_str}\n"
    # )
    # qa_template = PromptTemplate(template)

    # # you can create text prompt (for completion API)
    # prompt = qa_template.format(context_str=..., query_str=...)

    # # or easily convert to message prompts (for chat API)
    # messages = qa_template.format_messages(context_str=..., query_str=...)

    resp = llm.complete("Who is Paul Graham?")
    print(f"{resp = }")

def test_dql_db_tool(llm):

    engine = create_engine("sqlite:///:memory:", future=True)
    metadata_obj = MetaData()
    # create city SQL table
    table_name = "city_stats"
    city_stats_table = Table(
        table_name,
        metadata_obj,
        Column("city_name", String(16), primary_key=True),
        Column("population", Integer),
        Column("country", String(16), nullable=False),
    )

    metadata_obj.create_all(engine)

    rows = [
        {"city_name": "Toronto", "population": 2930000, "country": "Canada"},
        {"city_name": "Tokyo", "population": 13960000, "country": "Japan"},
        {"city_name": "Berlin", "population": 3645000, "country": "Germany"},
    ]
    for row in rows:
        stmt = insert(city_stats_table).values(**row)
        with engine.begin() as connection:
            cursor = connection.execute(stmt)

    sql_database = SQLDatabase(engine, include_tables=["city_stats"])
    sql_query_engine = NLSQLTableQueryEngine(
        sql_database=sql_database, tables=["city_stats"], verbose=True, llm=llm
    )
    sql_tool = QueryEngineTool.from_defaults(
        query_engine=sql_query_engine,
        description=(
            "Useful for translating a natural language query into a SQL query over"
            " a table containing: city_stats, containing the population/country of"
            " each city"
        ),
    )

def main():
    # Settings.llm = Ollama(model="llama2", request_timeout=60.0)

    # grabbing something I have locally
    # llama3:latest
    Settings.llm = Ollama(model="llama3:latest", request_timeout=60.0)
    print(Settings.llm)
    print(Settings.llm.request_timeout)
    print(type(Settings.llm)) # <class 'llama_index.llms.ollama.base.Ollama'>
    print(Settings.llm.__dict__)
    # print(json.dumps(Settings.llm.__dict__, indent=4))
    pprint.pp(Settings.llm.__dict__)


    # separate stuff
    print(''.join(['\n---']*5))
    print()\
    
    test_ollama_llm(Settings.llm)
    # response = agent.chat("What is 20+(2*4)? Calculate step by step.")
    # TODO: wondering if this will at least work?
    from llama_index.core.agent import ReActAgent
    from llama_index.core.tools import FunctionTool
    def agent_tool_test():
        return 'test agent response'
    def multiply(a: float, b: float) -> float:
        """Multiply two numbers and returns the product"""
        return a * b

    multiply_tool = FunctionTool.from_defaults(fn=multiply)

    def add(a: float, b: float) -> float:
        """Add two numbers and returns the sum"""
        return a + b

    add_tool = FunctionTool.from_defaults(fn=add)
    # agent = ReActAgent.from_tools([multiply_tool, add_tool], llm=llm, verbose=True)
    # https://docs.llamaindex.ai/en/stable/understanding/agent/
    test_tool = FunctionTool.from_defaults(fn=agent_tool_test)
    agent = ReActAgent.from_tools([test_tool], llm=Settings.llm, verbose=True)
    agent = ReActAgent.from_tools([multiply_tool, add_tool], llm=Settings.llm, verbose=True)
    response = agent.chat("What is 20+(2*4)? Calculate step by step.")
    print(response.response)

    sys.exit(0)

    test_dql_db_tool(Settings.llm)

if __name__ == "__main__":
    main()