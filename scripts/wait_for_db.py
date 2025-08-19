import os
import time

import psycopg2


def wait_for_postgres():
    dbname = os.getenv('DB_NAME', 'tickets')
    user = os.getenv('DB_USER', 'tickets')
    password = os.getenv('DB_PASSWORD', 'tickets')
    host = os.getenv('DB_HOST', 'db')
    port = os.getenv('DB_PORT', '5432')

    while True:
        try:
            conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
            conn.close()
            break
        except Exception:
            time.sleep(1)


if __name__ == '__main__':
    wait_for_postgres()



