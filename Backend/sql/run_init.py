"""
执行 init_tables.sql：读取 Backend/.env 的 MySQL 配置 → 连接 → 建表 → 校验。
仅用于本地初始化，不依赖项目业务代码。
"""
import os
import re
import sys

ENV_PATH = os.path.join(os.path.dirname(__file__), "..", ".env")
SQL_PATH = os.path.join(os.path.dirname(__file__), "init_tables.sql")


def load_env(path):
    cfg = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # 去掉行内注释（# 前为值）并去掉引号
            line = line.split("#", 1)[0].strip()
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            v = v.strip().strip('"').strip("'")
            cfg[k.strip()] = v
    return cfg


def main():
    cfg = load_env(ENV_PATH)
    required = ["MYSQL_HOST", "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DATABASE"]
    missing = [k for k in required if not cfg.get(k)]
    if missing:
        print(f"[ERROR] .env 缺少数据库配置: {missing}")
        sys.exit(1)

    port = int(cfg.get("MYSQL_PORT", "3306"))
    host = cfg["MYSQL_HOST"]
    user = cfg["MYSQL_USER"]
    pwd = cfg["MYSQL_PASSWORD"]
    db = cfg["MYSQL_DATABASE"]

    import pymysql
    print(f"[INFO] 连接 MySQL -> host={host} port={port} user={user} db={db}")
    conn = pymysql.connect(
        host=host, port=port, user=user, password=pwd,
        database=db, charset="utf8mb4", autocommit=False,
    )

    with open(SQL_PATH, "r", encoding="utf-8") as f:
        sql = f.read()

    # 去掉注释行（-- 开头）后按分号切分
    statements = []
    for raw in sql.split(";"):
        cleaned = "\n".join(
            ln for ln in raw.splitlines() if not ln.strip().startswith("--")
        ).strip()
        if cleaned:
            statements.append(cleaned)

    try:
        with conn.cursor() as cur:
            for stmt in statements:
                # 取首行作为标识
                first = stmt.strip().splitlines()[0]
                cur.execute(stmt)
                print(f"[OK] 执行: {first[:60]}")
            conn.commit()
        print("\n[INFO] 建表完成，开始校验...")
        with conn.cursor() as cur:
            cur.execute("SHOW TABLES")
            tables = [r[0] for r in cur.fetchall()]
            for t in tables:
                cur.execute(f"SELECT COUNT(*) FROM `{t}`")
                cnt = cur.fetchone()[0]
                cur.execute(f"SELECT COUNT(*) FROM information_schema.columns "
                            f"WHERE table_schema=%s AND table_name=%s", (db, t))
                cols = cur.fetchone()[0]
                print(f"  - {t:<18} 列数={cols:<3} 当前行数={cnt}")
            print(f"\n[SUCCESS] 共 {len(tables)} 张表：{', '.join(tables)}")
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] 执行失败，已回滚：{e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
