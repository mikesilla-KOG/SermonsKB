import sqlite3
c = sqlite3.connect("sermons.db").cursor()
sermons = c.execute("SELECT COUNT(*) FROM sermons").fetchone()[0]
chunks = c.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
print(f"Sermons: {sermons}")
print(f"Chunks: {chunks}")
print(f"Progress: {sermons}/673 videos ({sermons*100//673}%)")
