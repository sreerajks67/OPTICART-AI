import google.generativeai as genai
import langchain
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv


try:
    load_dotenv(r"C:\Users\Sajin S\Desktop\vs_code\Gemini_models\opti_cart\key.env")
    key_file=os.getenv("GOOGLE_API_KEY")
    if key_file:
        genai.configure(api_key=key_file)
    else:
        print("not file found")
except KeyError as e:
    print(f"errr{e}")


llm=ChatGoogleGenerativeAI(model="models/gemini-2.5-flash",temperature=0.2)

input_template1 = """
You are an SQL expert.

Rules:
- Only generate SELECT queries
- Do NOT modify database
- Do NOT use DELETE, UPDATE, DROP

User Query: {user_query}

Table: products
Columns: id, name, price, rating, category

Return only SQL query.
"""

from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

prompt=PromptTemplate(template=input_template1,input_variables=["user_query"])

sql_chain=({"user_query":RunnablePassthrough()}|prompt|llm|StrOutputParser())

def ask_sql(query):
    result=sql_chain.invoke(query)
    return result.strip("```sql")



input_template2=prompt =input_template2 = """
You are an intelligent ecommerce AI assistant.

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


prompt=PromptTemplate(template=input_template2,input_variables=["user_query","product_text"])
responce_chain=({"user_query":RunnablePassthrough(),"product_text":RunnablePassthrough()}|prompt|llm|StrOutputParser())


def generate_responce(user_query,product_text):
    result=responce_chain.invoke({"user_query":user_query,
                                  "product_text":product_text})
    return result


a=ask_sql("which product under 90000?")
print(generate_responce(a,"laptop A 80000 high performance"))