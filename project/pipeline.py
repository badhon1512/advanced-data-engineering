import os
import zipfile
import pandas as pd
from kaggle.api.kaggle_api_extended import KaggleApi
import tempfile
from sqlalchemy import create_engine

class DataPipeline:
    def __init__(self, data_sources) -> None:
        self.data_sources = data_sources
        self.dataframes= []
        self.api = KaggleApi()
        self.api.authenticate()

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
                self.dataframes[i]['USPoliceViolence'].drop(unusefull_features, axis=1)
                self.dataframes[i]['USPoliceViolence'] = self.fill_nulls(self.dataframes[i]['USPoliceViolence'])
            elif i == 1:    
                # need to handle multiple data sets
                # police killing dataset
                unusefull_features = ['id', "name"]
                self.dataframes[i]['PoliceKillingsUS'].drop(unusefull_features, axis=1)
                self.dataframes[i]['PoliceKillingsUS'] = self.fill_nulls(self.dataframes[i]['PoliceKillingsUS'])
                self.dataframes[i]['MedianHouseholdIncome2015'] = self.fill_nulls(self.dataframes[i]['MedianHouseholdIncome2015'])
                self.dataframes[i]['PercentOver25CompletedHighSchool'] = self.fill_nulls(self.dataframes[i]['PercentOver25CompletedHighSchool'])
                self.dataframes[i]['PercentagePeopleBelowPovertyLevel'] = self.fill_nulls(self.dataframes[i]['PercentagePeopleBelowPovertyLevel'])
                self.dataframes[i]['ShareRaceByCity'] = self.fill_nulls(self.dataframes[i]['ShareRaceByCity'])


                # now need to aggregate remaining dataframe and make a single dataframe, will think and do it later
                #dataframes[i]['SocioeconomicFactorsbyCounty'] =  merge_datasets_on_unique_columns([dataframes[i]['MedianHouseholdIncome2015'], dataframes[i]['PercentOver25CompletedHighSchool'],
                #                   dataframes[i]['PercentagePeopleBelowPovertyLevel'], dataframes[i]['ShareRaceByCity']])
                # remove old dataframes  
                #del dataframes[i]['MedianHouseholdIncome2015']
                #del dataframes[i]['PercentOver25CompletedHighSchool']
                #del dataframes[i]['PercentagePeopleBelowPovertyLevel']
                #del dataframes[i]['ShareRaceByCity']
       
    def fill_nulls(self, df):
        df.dropna(thresh=2, inplace=True)  # Remove rows with 2 or more NA values

        for column in df.columns:
            if pd.api.types.is_numeric_dtype(df[column]):  # Check if the column is numeric (integer or float)
                min_value = df[column].min()
                df[column].fillna(min_value, inplace=True)
            else:  # Check if the column is of string (object) type
                mode_value = df[column].mode().iloc[0]  # Use the mode (most frequent value) for strings
                df[column].fillna(mode_value, inplace=True)
                
        return df            

    def save_data_to_sqlite(self, database_name="US"):

        self.get_dataframes()
        self.preprocess_data()

        # Define the database path and create the directory if it doesn't exist
        path = 'sqlite:///data//' + database_name + '.sqlite'
        engine = create_engine(path, echo=False)
        
        # Save each DataFrame in the dictionary as a separate table in the database
        for dataset in self.dataframes:
            for table_name, df in dataset.items():
               # print(table_name, df.isnull().sum())
                df.to_sql(table_name, engine, if_exists='replace', index=False)
                print(f"Data saved to table '{table_name}' in database '{database_name}.sqlite'.")
        
        # Dispose of the engine when done
        engine.dispose()

                            


if __name__ == '__main__':

    pipeline = DataPipeline(['jamesvandenberg/us-police-shootings-20132020', 'kwullum/fatal-police-shootings-in-the-us'])
    pipeline.save_data_to_sqlite()