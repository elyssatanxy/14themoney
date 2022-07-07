import sqlite3
con = sqlite3.connect('budgetDatabase.db')

def sql_table(con):
    cursor = con.cursor
    cursor.execute("CREATE TABLE BUDGET (CHAT_ID int PRIMARY KEY, BUDGET decimal(5, 2), USERNAME text")
    con.commit()

sql_table(con)