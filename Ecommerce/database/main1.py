import pymysql


def get_connection():

    return pymysql.connect(
        host="localhost",
        user="root",
        password="12345678",
        database="opti_cart"
    )


def execute_query(cursor, query):

    cursor.execute(query)

    return cursor.fetchall()