import os
import unittest
import sqlalchemy
from pipeline import DataPipeline
from sqlalchemy.sql import text

class DataPipelineTestCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("Test Cases: ")

        print("Running the data pipeline...")
        # Initialize and execute the pipeline
        cls.pipeline = DataPipeline(
            ['jamesvandenberg/us-police-shootings-20132020', 'jonathanrevere/fbi-hate-crimes-in-usa-19912020']
        )
        cls.pipeline.save_data_to_sqlite()
        cls.engine = sqlalchemy.create_engine(f"sqlite:///{cls.pipeline.db_path}", echo=False)
        cls.connection = cls.engine.connect()



    @classmethod
    def tearDownClass(cls):
        # Close the database connection after all tests
        cls.engine.dispose()
        cls.connection.close()    


    def test_check_database(self):
        print("Checking database......")
        self.assertTrue(os.path.exists(self.pipeline.db_path), "Database does not exist at the specified path.")

    def test_tables(self):
        print("Checking Tables.....")
        if not os.path.exists(self.pipeline.db_path):
            self.fail(f"Database file '{self.pipeline.db_path}' does not exist.")

        self.inspector = sqlalchemy.inspect(self.engine)

        try:
            tables = self.inspector.get_table_names()
            self.assertIn("Hate Crimes", tables,
                          "Table not found.")
            self.assertIn("USPoliceViolence", tables,
                          "Table not found.")
        except sqlalchemy.exc.OperationalError:
            self.fail("Could not connect to the database.")
    
    

    def test_tables_data(self):
        print("Checking tables data...")

        try:
            # Use text() to execute raw SQL queries
            result_hate_crimes = self.connection.execute(text("SELECT COUNT(*) FROM `Hate Crimes`")).fetchone()
            result_us_police = self.connection.execute(text("SELECT COUNT(*) FROM `USPoliceViolence`")).fetchone()

            # Assert that both tables have at least one row
            self.assertGreater(result_hate_crimes[0], 0, "Table 'Hate Crimes' is empty.")
            self.assertGreater(result_us_police[0], 0, "Table 'USPoliceViolence' is empty.")
        except sqlalchemy.exc.OperationalError:
            self.fail("Could not query the database.")


if __name__ == "__main__":
    unittest.main()
