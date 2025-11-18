import sqlite3

conn = sqlite3.connect('sermons.db')
c = conn.cursor()

# Get table schema
c.execute("SELECT sql FROM sqlite_master WHERE name='sermons'")
result = c.fetchone()
print("Table schema:")
print(result[0] if result else "Table not found")

conn.close()
