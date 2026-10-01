from db import get_connection

table_name = ""

sql = f"""
DROP TABLE IF EXISTS {table_name};
"""

with get_connection() as conn:
    conn.execute(sql)