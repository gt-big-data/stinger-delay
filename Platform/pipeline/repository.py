import io
import pandas as pd
import psycopg2

class DbRepository:
    def __init__(self, dsn: str):
        self.dsn = dsn
    
    def copy_to_staging(self, df: pd.DataFrame, table: str, extra_cols: dict) -> int:
        if df.empty: return 0
        frame = df.assign(**extra_cols)
        buf = io.StringIO()
        cols = list(frame.columns)
        frame.to_csv(buf, index=False, header=False)
        buf.seek(0)
        with psycopg2.connect(self.dsn) as conn, conn.cursor() as cur:
            cur.copy_expert(f"COPY {table} ({','.join(cols)}) FROM STDIN WITH CSV", buf)
        return len(frame)

    def merge_core(self, sql: str) -> int:
        with psycopg2.connect(self.dsn) as conn, conn.cursor() as cur:
            cur.execute(sql)
            return cur.rowcount