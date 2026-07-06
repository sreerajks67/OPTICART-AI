from chatbot.query_to_sql import ask_sql
from chatbot.query_to_sql import generate_responce
from database.main1 import get_connection
from database.main1 import excute_query


def final_result(user_query):
    sql_fitch=ask_sql(user_query)

    conn=get_connection()
    cursor=conn,cursor()

    result=excute_query(cursor,query=user_query)

    product_text = ""
    for r in result:
        product_text += f"{r[1]} - ₹{r[2]} - Rating:{r[3]}\n"
    
    responce=generate_responce(user_query=user_query,product_text=product_text)
    return responce


print(final_result("which product under 90000"))