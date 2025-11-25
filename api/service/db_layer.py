import pandas as pd
from sqlalchemy import create_engine, text, inspect

from api.configuration.configuration import DATABASE_URL


class PostgresManager:
    def __init__(self):
        self.engine = create_engine(DATABASE_URL)
        self._init_metadata_table()

    def _init_metadata_table(self):
        """Creates a metadata table to store column descriptions if it doesn't exist."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("""
                                  CREATE TABLE IF NOT EXISTS column_metadata
                                  (
                                      table_name
                                      TEXT,
                                      column_name
                                      TEXT,
                                      description
                                      TEXT,
                                      PRIMARY
                                      KEY
                                  (
                                      table_name,
                                      column_name
                                  )
                                      )
                                  """))
                conn.commit()
        except Exception as e:
            print(f"⚠️ Could not initialize metadata table: {e}")

    def ingest_csv(self, file_path: str, table_name: str):
        """
        Loads a CSV into PostgreSQL and returns the list of columns.
        Returns: (success: bool, columns: list)
        """
        print(f"📦 Ingesting '{file_path}' into table '{table_name}'...")

        try:
            # Read CSV
            df = pd.read_csv(file_path)
            # Standardize columns
            df.columns = [c.lower().replace(" ", "_") for c in df.columns]

            # Load to SQL
            df.to_sql(table_name, self.engine, if_exists='replace', index=False)
            print(f"✅ Successfully loaded {len(df)} rows into '{table_name}'.")

            return True, df.columns.tolist()

        except Exception as e:
            print(f"❌ Error loading CSV: {e}")
            return False, []

    def save_column_metadata(self, table_name: str, descriptions: dict):
        """
        Stores user-provided descriptions in the metadata table.
        """
        data = [
            {"table_name": table_name, "column_name": col, "description": desc}
            for col, desc in descriptions.items()
        ]

        if not data:
            return

        try:
            with self.engine.connect() as conn:
                # Clean up old metadata for this table to avoid stale data
                conn.execute(text("DELETE FROM column_metadata WHERE table_name = :t"), {"t": table_name})

                # Insert new metadata
                conn.execute(text("""
                                  INSERT INTO column_metadata (table_name, column_name, description)
                                  VALUES (:table_name, :column_name, :description)
                                  """), data)
                conn.commit()
            print("✅ Column descriptions saved to metadata table.")
        except Exception as e:
            print(f"❌ Error saving metadata: {e}")

    def execute_query(self, query: str):
        """
        Executes a SQL query and returns the result.
        """
        try:
            with self.engine.connect() as connection:
                result_df = pd.read_sql(text(query), connection)

                if result_df.empty:
                    return {"success": True, "data": "No results found.", "raw_df": None}

                return {"success": True, "data": result_df.to_markdown(index=False), "raw_df": result_df}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_schema_string(self):
        """
        Generates the schema string, enriched with user descriptions from the metadata table.
        """
        inspector = inspect(self.engine)
        table_names = inspector.get_table_names()

        # Fetch all metadata into a dictionary for quick lookup
        # Structure: {(table, col): description}
        metadata_map = {}
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT table_name, column_name, description FROM column_metadata"))
                for row in result:
                    metadata_map[(row[0], row[1])] = row[2]
        except Exception:
            pass  # If metadata table fails, just proceed without descriptions

        schema_str = ""

        for table in table_names:
            # Skip internal tables if any
            if table == 'column_metadata':
                continue

            schema_str += f"\nTable: {table}\nColumns:\n"
            columns = inspector.get_columns(table)

            for col in columns:
                col_name = col['name']
                col_type = col['type']

                # Get description if exists
                desc = metadata_map.get((table, col_name), "")
                desc_text = f" -- Description: {desc}" if desc else ""

                schema_str += f"- {col_name} ({col_type}){desc_text}\n"

        return schema_str