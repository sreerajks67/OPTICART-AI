# %%
import pymysql

# %%
def get_connection():
    return pymysql.connect(host="localhost",
    user="root",
    password="v777@777v",
    database="opti_cart"
)


# %%
# cursor.execute("INSERT INTO products (name, price, rating, category) VALUES (%s, %s, %s, %s)",
#     ("Laptop A", 50000, 4.2, "laptop"))
# conn.commit()

# %%
def excute_query(cursor,query):
    cursor.execute(query)
    return cursor.fetchall()


