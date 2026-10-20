import os
import django
import datetime
import decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

def get_sqlserver_type(data_type, char_len, num_prec, num_scale, col_type):
    dt = data_type.lower()
    if dt in ['bigint']:
        return 'BIGINT'
    elif dt in ['int', 'mediumint', 'smallint']:
        return 'INT'
    elif dt in ['tinyint']:
        if col_type.startswith('tinyint(1)'):
            return 'BIT'
        return 'TINYINT'
    elif dt in ['varchar']:
        if char_len and char_len > 0 and char_len <= 4000:
            return f'NVARCHAR({char_len})'
        return 'NVARCHAR(MAX)'
    elif dt in ['char']:
        return f'NVARCHAR({char_len if char_len else 10})'
    elif dt in ['text', 'longtext', 'mediumtext']:
        return 'NVARCHAR(MAX)'
    elif dt in ['date']:
        return 'DATE'
    elif dt in ['time']:
        return 'TIME'
    elif dt in ['datetime', 'timestamp']:
        return 'DATETIME2'
    elif dt in ['decimal']:
        return f'DECIMAL({num_prec or 12}, {num_scale or 2})'
    elif dt in ['double', 'float']:
        return 'FLOAT'
    else:
        return 'NVARCHAR(MAX)'

def format_val(val, col_type):
    if val is None:
        return "NULL"
    if col_type == 'BIT':
        return "1" if val else "0"
    if isinstance(val, (int, float, decimal.Decimal)):
        return str(val)
    if isinstance(val, (datetime.datetime, datetime.date, datetime.time)):
        return f"N'{str(val)}'"
    # String
    s = str(val).replace("'", "''")
    return f"N'{s}'"

with connection.cursor() as cursor:
    # 1. Get tables
    cursor.execute("SHOW TABLES;")
    tables = [r[0] for r in cursor.fetchall()]
    
    # 2. Get FKs
    cursor.execute("""
        SELECT 
            TABLE_NAME, 
            COLUMN_NAME, 
            CONSTRAINT_NAME, 
            REFERENCED_TABLE_NAME, 
            REFERENCED_COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = DATABASE()
          AND REFERENCED_TABLE_NAME IS NOT NULL
        ORDER BY TABLE_NAME, COLUMN_NAME;
    """)
    fk_list = cursor.fetchall()

sql_lines = []
sql_lines.append("-- ======================================================================")
sql_lines.append("-- EMS DATABASE MIGRATION: MYSQL -> MICROSOFT SQL SERVER (T-SQL)")
sql_lines.append("-- Generated automatically by Antigravity")
sql_lines.append("-- ======================================================================")
sql_lines.append("USE [master];")
sql_lines.append("GO")
sql_lines.append("IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'ems')")
sql_lines.append("BEGIN")
sql_lines.append("    CREATE DATABASE [ems];")
sql_lines.append("END")
sql_lines.append("GO")
sql_lines.append("USE [ems];")
sql_lines.append("GO\n")

# Drop FKs if any exist
sql_lines.append("-- Drop foreign keys if re-running")
for fk in fk_list:
    tbl, col, cname, ref_tbl, ref_col = fk
    sql_lines.append(f"IF OBJECT_ID('dbo.{cname}', 'F') IS NOT NULL ALTER TABLE [dbo].[{tbl}] DROP CONSTRAINT [{cname}];")
sql_lines.append("GO\n")

# Process each table
table_col_info = {}

for tbl in tables:
    with connection.cursor() as cursor:
        # Columns
        cursor.execute(f"""
            SELECT 
                COLUMN_NAME, 
                DATA_TYPE, 
                CHARACTER_MAXIMUM_LENGTH, 
                NUMERIC_PRECISION, 
                NUMERIC_SCALE, 
                IS_NULLABLE, 
                COLUMN_KEY, 
                EXTRA,
                COLUMN_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = '{tbl}'
            ORDER BY ORDINAL_POSITION;
        """)
        cols = cursor.fetchall()
        
        # Primary key cols
        cursor.execute(f"""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = DATABASE() 
              AND TABLE_NAME = '{tbl}' 
              AND CONSTRAINT_NAME = 'PRIMARY';
        """)
        pk_cols = [r[0] for r in cursor.fetchall()]
        
        col_defs = []
        has_identity = False
        col_type_map = {}
        col_names = []
        
        for c in cols:
            cname, dtype, clen, nprec, nscale, isnull, ckey, extra, col_type = c
            mssql_type = get_sqlserver_type(dtype, clen, nprec, nscale, col_type)
            col_type_map[cname] = mssql_type
            col_names.append(cname)
            
            is_pk = (cname in pk_cols)
            is_autoincrement = ('auto_increment' in extra.lower()) or (is_pk and mssql_type in ['INT', 'BIGINT'] and len(pk_cols) == 1)
            
            def_str = f"[{cname}] {mssql_type}"
            if is_autoincrement:
                def_str += " IDENTITY(1,1)"
                has_identity = True
                
            if isnull.upper() == 'NO':
                def_str += " NOT NULL"
            else:
                def_str += " NULL"
                
            col_defs.append(def_str)
            
        table_col_info[tbl] = {
            'col_type_map': col_type_map,
            'col_names': col_names,
            'has_identity': has_identity
        }
        
        sql_lines.append(f"-- --------------------------------------------------")
        sql_lines.append(f"-- Table structure for [{tbl}]")
        sql_lines.append(f"-- --------------------------------------------------")
        sql_lines.append(f"IF OBJECT_ID('dbo.[{tbl}]', 'U') IS NOT NULL DROP TABLE [dbo].[{tbl}];")
        sql_lines.append("GO")
        sql_lines.append(f"CREATE TABLE [dbo].[{tbl}] (")
        for idx, cdef in enumerate(col_defs):
            comma = "," if (idx < len(col_defs) - 1 or pk_cols) else ""
            sql_lines.append(f"    {cdef}{comma}")
            
        if pk_cols:
            pk_str = ", ".join([f"[{p}]" for p in pk_cols])
            sql_lines.append(f"    CONSTRAINT [PK_{tbl}] PRIMARY KEY CLUSTERED ({pk_str})")
            
        sql_lines.append(");")
        sql_lines.append("GO\n")

# Data Migration
sql_lines.append("-- ======================================================================")
sql_lines.append("-- DATA INSERTION")
sql_lines.append("-- ======================================================================")

for tbl in tables:
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT * FROM `{tbl}`;")
        rows = cursor.fetchall()
        
        if not rows:
            continue
            
        info = table_col_info[tbl]
        col_names = info['col_names']
        col_map = info['col_type_map']
        has_id = info['has_identity']
        
        sql_lines.append(f"-- Data for [{tbl}] ({len(rows)} records)")
        if has_id:
            sql_lines.append(f"SET IDENTITY_INSERT [dbo].[{tbl}] ON;")
            
        cols_joined = ", ".join([f"[{c}]" for c in col_names])
        
        # Batch inserts in chunks of 50
        chunk_size = 50
        for i in range(0, len(rows), chunk_size):
            chunk = rows[i:i+chunk_size]
            sql_lines.append(f"INSERT INTO [dbo].[{tbl}] ({cols_joined}) VALUES")
            val_clauses = []
            for row in chunk:
                vals = [format_val(val, col_map[col_names[ci]]) for ci, val in enumerate(row)]
                val_clauses.append(f"    ({', '.join(vals)})")
            sql_lines.append(",\n".join(val_clauses) + ";")
            
        if has_id:
            sql_lines.append(f"SET IDENTITY_INSERT [dbo].[{tbl}] OFF;")
        sql_lines.append("GO\n")

# Add Foreign Keys
sql_lines.append("-- ======================================================================")
sql_lines.append("-- FOREIGN KEY CONSTRAINTS")
sql_lines.append("-- ======================================================================")
for fk in fk_list:
    tbl, col, cname, ref_tbl, ref_col = fk
    # Truncate constraint name if too long for SQL Server (max 128 chars)
    safe_cname = cname[:120] if len(cname) > 120 else cname
    sql_lines.append(f"ALTER TABLE [dbo].[{tbl}] WITH CHECK")
    sql_lines.append(f"    ADD CONSTRAINT [{safe_cname}] FOREIGN KEY ([{col}]) REFERENCES [dbo].[{ref_tbl}] ([{ref_col}]);")
    sql_lines.append("GO")

target_file = r"E:\Project\HeThongQuanLyNhanVien\ems_sqlserver.sql"
with open(target_file, "w", encoding="utf-8") as f:
    f.write("\n".join(sql_lines))

print(f"Generated SQL Server script: {target_file} ({len(sql_lines)} lines)")
