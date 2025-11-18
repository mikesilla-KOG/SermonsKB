import sqlite3

conn = sqlite3.connect('sermons.db')
c = conn.cursor()

c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in c.fetchall()]
print('Tables:', tables)

if 'chunks' in tables:
    c.execute('SELECT COUNT(*) FROM chunks')
    count = c.fetchone()[0]
    print(f'chunks table: {count} rows')
else:
    print('chunks table does NOT exist - need to create and populate it')

conn.close()
