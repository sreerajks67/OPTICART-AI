import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser


# =====================================================
# LOAD ENV FILE
# =====================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

load_dotenv(
    os.path.join(BASE_DIR, 'key.env')
)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    print("WARNING: GOOGLE_API_KEY not found in key.env")


# =====================================================
# GEMINI MODEL  (uses google-genai under the hood via langchain)
# =====================================================

# Try models in order — gemini-2.5-flash is the primary model
_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.5-flash-lite",
]

llm = ChatGoogleGenerativeAI(
    model=_MODELS[0],
    temperature=0.2,
    google_api_key=GOOGLE_API_KEY,
)


# =====================================================
# SQL GENERATION PROMPT
# =====================================================

input_template1 = """
You are an SQL expert.

IMPORTANT:
The ONLY table available is:

product

Available columns:
id
name
rating
category
price

DO NOT use any other columns.

Rules:
- Only generate SELECT queries
- Never modify database
- Never use DELETE, UPDATE, DROP

User Query:
{user_query}

Return ONLY the raw SQL query, no markdown code blocks.
"""

sql_prompt = PromptTemplate(
    template=input_template1,
    input_variables=["user_query"]
)

sql_chain = (
    {"user_query": RunnablePassthrough()}
        | sql_prompt
    | llm
    | StrOutputParser()
)


def ask_sql(query):
    result = sql_chain.invoke(query)
    result = result.replace("```sql", "")
    result = result.replace("```", "")
    return result.strip()


# =====================================================
# RESPONSE GENERATION PROMPT
# =====================================================

input_template2 = """
You are an intelligent ecommerce AI assistant for OptiCart.

Your job is to:
- Analyze user needs
- Understand product details
- Recommend the BEST product
- Explain naturally like a real shopping assistant

RULES:
- Never explain SQL queries
- Never mention databases
- Never say "this product is a match"
- Talk naturally and professionally
- Keep response short and useful
- Focus on product quality, price, and features
- If multiple products exist, compare them
- Mention why the product is recommended

User Request:
{user_query}

Available Products:
{product_text}

Give response in this format:

Recommended Product:
<Name>

Price:
<Price>

Why This Product?
- point 1
- point 2
- point 3

Final Recommendation:
<short final sentence>
"""


response_prompt = PromptTemplate(
    template=input_template2,
    input_variables=[
        "user_query",
        "product_text"
    ]
)

response_chain = (
    {
        "user_query": RunnablePassthrough(),
        "product_text": RunnablePassthrough()
    }
    | response_prompt
    | llm
    | StrOutputParser()
)


def generate_response(user_query, product_text):
    result = response_chain.invoke({
        "user_query": user_query,
        "product_text": product_text
    })
    return result


# =====================================================
# TESTING
# =====================================================

if __name__ == "__main__":

    sql_query = ask_sql(
        "Which laptops are under 90000?"
    )

    print("Generated SQL:")
    print(sql_query)

    print("\n============================\n")

    response = generate_response(
        "Which laptops are under 90000?",
        """
        Laptop A - Rs.80000
        RTX Graphics
        High Performance
        16GB RAM
        """
    )

    print(response)