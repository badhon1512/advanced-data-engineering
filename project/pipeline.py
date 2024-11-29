import os
import zipfile
import pandas as pd
from kaggle.api.kaggle_api_extended import KaggleApi
import tempfile
from sqlalchemy import create_engine
import tempfile


class DataPipeline:
    def __init__(self, data_sources) -> None:
        self.data_sources = data_sources
        self.dataframes= []
        self.api = KaggleApi()
        self.api.authenticate()

        # Get the absolute path of the main directory (one level up from the project directory)
        self.main_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))  # Main directory
        self.data_dir = os.path.join(self.main_dir, "data")  # Path to the 'data' folder in the main directory
        os.makedirs(self.data_dir, exist_ok=True)  # Ensure the 'data' directory exists

    def get_dataframes(self):
        
        for i in range(2):
            self.dataframes.append({})
        # Download the dataset to a temporary file
            with tempfile.TemporaryDirectory() as temp_dir:
                print("Downloading dataset...")
                self.api.dataset_download_files(self.data_sources[i], path=temp_dir, unzip=False)
                print("Download complete.")
            
                #Locate the zip file and read each CSV file into a DataFrame
                zip_file_path = os.path.join(temp_dir, f"{self.data_sources[i].split('/')[-1]}.zip")
                with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                    # Iterate over each file in the zip archive
                    for file_name in zip_ref.namelist():
                        if file_name.endswith('.csv'):  # Process only CSV files as all of my files are csv
                            with zip_ref.open(file_name) as csv_file:
                                # Load each CSV file into a separate DataFrame
                                df = pd.read_csv(csv_file, encoding="ISO-8859-1")  # Adjust encoding if necessary
                                self.dataframes[i][file_name.split('/')[-1].replace('.csv', '')] = df
    
    
    def preprocess_data(self):

       for i in range(2):

         if i == 0:
             unusefull_features = ['Unnamed: 0', "Victim's name"]
             self.dataframes[i][list(self.dataframes[i].keys())[0]].drop(unusefull_features, axis=1,  errors='ignore', inplace=True)
             self.dataframes[i][list(self.dataframes[i].keys())[0]] = self.fill_nulls(self.dataframes[i][list(self.dataframes[i].keys())[0]])
         elif i == 1:    
             # need to handle multiple data sets
             self.dataframes[i]['Hate Crimes'] = pd.DataFrame(columns=self.dataframes[i][list(self.dataframes[i].keys())[0]].columns)
 
             for key in list(self.dataframes[i].keys()):
                if key != 'Hate Crimes':  # Skip the key being created
                    hc = self.dataframes[i][key]
                    self.dataframes[i]['Hate Crimes'] = pd.concat([self.dataframes[i]['Hate Crimes'], hc], ignore_index=True)
                    del self.dataframes[i][key]  # Safely delete the original DataFrame
             
             
             # Convert INCIDENT_DATE to datetime
             self.dataframes[i]['Hate Crimes']['INCIDENT_DATE'] = pd.to_datetime(self.dataframes[i]['Hate Crimes']['INCIDENT_DATE'], format='%d-%b-%y', errors='coerce')
            
             # Filter data for 2013-2020
             self.dataframes[i]['Hate Crimes'] = self.dataframes[i]['Hate Crimes'][
                (self.dataframes[i]['Hate Crimes']['INCIDENT_DATE'].dt.year >= 2013) & 
                (self.dataframes[i]['Hate Crimes']['INCIDENT_DATE'].dt.year <= 2020)
             ]
            
             unusefull_features = ["Unnamed: 0", "PUB_AGENCY_UNIT", 'INCIDENT_ID', "PUB_AGENCY_NAME","AGENCY_TYPE_NAME", "ADULT_VICTIM_COUNT", "JUVENILE_VICTIM_COUNT", "ADULT_OFFENDER_COUNT", "JUVENILE_OFFENDER_COUNT","OFFENDER_ETHNICITY"]
             self.dataframes[i]['Hate Crimes'].drop(unusefull_features, axis=1, errors='ignore', inplace=True)
             self.dataframes[i][list(self.dataframes[i].keys())[0]] = self.fill_nulls(self.dataframes[i]['Hate Crimes'])

    def fill_nulls(self, df):
        
        df.dropna(thresh=2, inplace=True)  # Remove rows with 2 or more NA values

        for column in df.columns:
            if pd.api.types.is_numeric_dtype(df[column]):  # Check if the column is numeric (integer or float)
                min_value = df[column].min()
                df[column].fillna(min_value, inplace=True)
            else:  # For string (object) type columns
                mode_value = df[column].mode()
                if not mode_value.empty:  # Check if mode exists
                    df[column].fillna(mode_value.iloc[0], inplace=True)
                else:
                    df[column].fillna("Unknown", inplace=True)  # Use a default value for empty modes
        return df
            

    def save_data_to_sqlite(self, database_name="US"):

        self.get_dataframes()
        self.preprocess_data()

        # Define the SQLite database path
        self.db_path = os.path.join(self.data_dir, f"{database_name}.sqlite")

        # Create SQLite engine
        self.engine = create_engine(f"sqlite:///{self.db_path}", echo=False)

        # Save each DataFrame to the database
        for dataset in self.dataframes:
            for table_name, df in dataset.items():
                df.to_sql(table_name, self.engine, if_exists='replace', index=False)
                print(f"Data saved to table '{table_name}' in database '{database_name}.sqlite'.")

        self.engine.dispose()


if __name__ == '__main__':
    pipeline = DataPipeline(['jamesvandenberg/us-police-shootings-20132020', 'jonathanrevere/fbi-hate-crimes-in-usa-19912020'])
    pipeline.save_data_to_sqlite()
