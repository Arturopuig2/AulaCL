
from sqlalchemy import create_engine, inspect, text
import os

# Path to local SQLite DB
db_path = "/Users/arturo/Desktop/Aula_CL/AulaCL/aula_cl.db"
if not os.path.exists(db_path):
    print("Local database aula_cl.db not found.")
    exit()

database_url = f"sqlite:///{db_path}"
engine = create_engine(database_url)

try:
    with engine.connect() as connection:
        # Check if table 'questions' exists
        inspector = inspect(engine)
        if 'questions' not in inspector.get_table_names():
            print("Table 'questions' does not exist in local DB.")
        else:
            # Count questions
            result = connection.execute(text("SELECT count(*) FROM questions"))
            count = result.scalar()
            print(f"Found {count} questions in local SQLite database.")
            
            if count > 0:
                print("Sample questions:")
                rows = connection.execute(text("SELECT id, text_id, question_content FROM questions LIMIT 5"))
                for row in rows:
                    print(row)
except Exception as e:
    print(f"Error accessing database: {e}")
