# My Modules
import explore as ex
import stats_conclude as sc

# Imports
import env
import os

# Numbers
import pandas as pd 
import numpy as np
from scipy import stats

# Vizzes
import matplotlib.pyplot as plt
import seaborn as sns

# Splits
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler

# -------------------------------------------------------------------------

# ACQUIRE

def get_connection(db):
    '''This functions grants access to server with eny credentials'''
    return f'mysql+pymysql://{env.user}:{env.password}@{env.host}/{db}'

def check_file_exists(fn, query, url):
    '''check if file exists in my local directory, if not, pull from sql db
    return dataframe'''
    if os.path.isfile(fn):
        print('CSV file found and loaded')
        return pd.read_csv(fn, index_col=0)
    else: 
        print('Creating df and exporting CSV...')
        df = pd.read_sql(query, url)
        df.to_csv(fn)
        return df 
print(f'Load in successful, awaiting commands...')

def get_data(db, query):
    """This function returns a df from the selected SQL database and specific query
    ---
    Format: df = functions()
    """
    url = env.get_connection(db)
    filename = db+'.csv'
    df = check_file_exists(filename, query, url)

    return df

# -------------------------------------------------------------------------

#  EXPLORE

def wrangle_zillow(df):
    """This function is meant to clean and return the prepared df with identifying
    and removing outliers.
    ---
    Further shrinking the outliers to prevent skewing of the data for the 
    target audience.
    """
    print(f"Prepare Details")
    
    # rename columns
    df = df.rename(columns = {'bedroomcnt':'bed', 'bathroomcnt':'bath', 'calculatedfinishedsquarefeet':\
    'sqft', 'taxvaluedollarcnt': 'assessed_worth', 'fips':'county', 'transactiondate':'date'})
    print(f"--------------------------------------------")
    print(f"Renamed columns for ease of use")

    # drop parcelid and use (used for initial exploration only)
    df = df.drop(columns=['parcelid'])

    # drop all nulls
    df_clean = df.dropna()
    print(f"Nulls removed: Percent Original Data Remaining: {round(df_clean.shape[0]/df.shape[0]*100,0)}")

    # change data types and map FIPS code
    df_clean.county = df_clean.county.map({6037:"LA", 6059:"Orange", 6111:"Ventura"})
    df_clean.bed = df_clean.bed.astype(int)
    print(f"Bed datatype changed from float to integer\nChanged FIPS code to actual county name")
    print(f"--------------------------------------------")

    # outliers ACTUAL
    col_cat = [] #this is for my categorical variables 
    col_num = [] #this is for my numerical variables 
    for col in df_clean.columns: 
        if col in df_clean.select_dtypes(include=['int64', 'float64']): 
            col_num.append(col) 
        else: 
            col_cat.append(col) 

    for col in col_cat: 
        print(f"{col.capitalize().replace('_', ' ')} is a categorical column.") 
    print(f"--------------------------------------------")
    print('Outliers Calculated with IQR Ranges, multiplier 1.5')

    for col in col_num: 
        q1 = df_clean[col].quantile(.25) 
        q3 = df_clean[col].quantile(.75) 
        iqr = q3 - q1 
        upper_bound = q3 + (1.5 * iqr) 
        lower_bound = q1 - (1.5 * iqr) 
        print(f"{col.capitalize().replace('_', ' ')} < = {upper_bound.round(2)} and > {lower_bound.round(2)}") 
        df_clean = df_clean[(df_clean[col] <= upper_bound) & (df_clean[col] >= lower_bound)] 

    print(f"Outliers removed: Percent Original Data Remaining: {round(df_clean.shape[0]/df.shape[0]*100,0)}")

    return df_clean

def outliers_zillow(df,m):
    """This function uses a built-in outlier function to scientifically identify
    all outliers in the zillow dataset and then print them out for each column.
    """
    col_cat = [] #this is for my categorical varibles
    col_num = [] #this is for my numerical varibles

    for col in df.columns:
        if col in df.select_dtypes(include=['int64', 'float64']):
            col_num.append(col)
        else:
            col_cat.append(col)

    for col in col_cat:
        print(f"{col.capitalize().replace('_',' ')} is a categorical column.")
    
    for col in col_num:
        q1 = df[col].quantile(.25)
        q3 = df[col].quantile(.75)
        iqr = q3 - q1
        upper_bound = q3 + (m * iqr)
        lower_bound = q1 - (m * iqr)
        # print(f"{col.capitalize().replace('_',' ')}: upper,lower ({upper_bound}, {lower_bound})")
    return upper_bound, lower_bound

# -------------------------------------------------------------------------

# SPLIT

def split_zillow(df):
    '''
    This function takes in a DataFrame and returns train, validate, and test DataFrames.

    (train, validate, test = split_zillow() to assign variable and return shape of df.)
    '''
    train_validate, test = train_test_split(df, test_size=.2,
                                        random_state=123)
    train, validate = train_test_split(train_validate, test_size=.25,
                                       random_state=123)
    
    print(f'Prepared DF: {df.shape}')
    print(f'Train: {train.shape}')
    print(f'Validate: {validate.shape}')
    print(f'Test: {test.shape}')
    
    return train, validate, test

# X_train, y_train, X_validate, y_validate, X_test, y_test

def x_y_train_validate_test(train, validate, test, target):
    """This function takes in the train, validate, and test dataframes and assigns 
    the chosen features to X_train, X_validate, X_test, and y_train, y_validate, 
    and y_test.
    ---
    Format: X_train, y_train, X_validate, y_validate, X_test, y_test = function()
    """ 
    # X_train, validate, and test to be used for modeling
    X_train = train.drop(columns=[target])
    y_train = train[{target}]

    X_validate = validate.drop(columns=[target])
    y_validate = validate[{target}]
   
    X_test = test.drop(columns=[target])
    y_test = test[{target}]

    print(f"Variable assignment successful...")

    # verifying number of features and target
    print(f"Verifying number of features and target:")
    print(f'Train: {X_train.shape, y_train.shape}')
    print(f'Validate: {X_validate.shape, y_validate.shape}')
    print(f'Test: {X_test.shape, y_test.shape}')

    return X_train, y_train, X_validate, y_validate, X_test, y_test

# -------------------------------------------------------------------------

# SCALING
   
def scale_split_data(train, validate, test, to_scale):
    """to_scale = X_train.columns.tolist()
    ---
    Format: X_train_scaled, X_validate_scaled, X_test_scaled = function()"""

    #make copies for scaling
    X_train_scaled = train.copy()
    X_validate_scaled = validate.copy()
    X_test_scaled = test.copy()

    #scale them!
    #make the thing
    scaler = MinMaxScaler()

    #fit the thing with column names
    scaler.fit(train[to_scale])

    #use the thing
    X_train_scaled[to_scale] = scaler.transform(train[to_scale])
    X_validate_scaled[to_scale] = scaler.transform(validate[to_scale])
    X_test_scaled[to_scale] = scaler.transform(test[to_scale])
    
    return X_train_scaled, X_validate_scaled, X_test_scaled

def scale_unsplit_data(df):
    """Scales unsplit data returning split X df
    ---
    Format: df_scaled = function()
    """
    #make copies for scaling
    to_scale = df.columns.tolist()
    df_scaled = df.copy()

    #scale
    #make the scaler
    scaler = MinMaxScaler()

    #fit the thing with column names
    scaler.fit(df[to_scale])

    #use the scaler
    df_scaled[to_scale] = scaler.transform(df[to_scale])

    return df_scaled


def inverse_minmax(scaled_df):
    """This function takes in the MinMaxScaler object and returns the inverse
    of a single scaled df input.
    
    format to return original df = minmaxscaler_back = function()
    """
    from sklearn.preprocessing import MinMaxScaler
    minmaxscaler_inverse = pd.DataFrame(MinMaxScaler.inverse_transform(scaled_df))

    # visualize if you want it too
    # plt.figure(figsize=(13, 6))
    # plt.subplot(121)
    # plt.hist(X_train_scaled_ro, bins=50, ec='black')
    # plt.title('Scaled')
    # plt.subplot(122)
    # plt.hist(robustscaler_back, bins=50, ec='black')
    # plt.title('Inverse')
    # plt.show()

    return minmaxscaler_inverse