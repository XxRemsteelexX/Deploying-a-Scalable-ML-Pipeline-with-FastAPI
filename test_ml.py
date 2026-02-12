import pytest
import os
import pandas as pd
from sklearn.model_selection import train_test_split
from ml.model import train_model
from sklearn.ensemble import RandomForestClassifier
from pathlib import Path



# TODO: add necessary import


# TODO: implement the first test. Change the function name and input as needed
def test_train_test_split_size():
    """
    checking that the sliced data is ready for testing
    """
    # Your code here
    data_path = './data/census.csv'
    data = pd.read_csv(str(data_path))
    train, test = train_test_split(data, test_size = 0.2)
    assert len(test) >= 2000
    


# TODO: implement the second test. Change the function name and input as needed
def test_column_names():
    """
    testing that all features are in the data
    """
    # Your code here
    data_path = './data/census.csv'
    data = pd.read_csv(data_path)

    features = {
        'age',
        'workclass',
        'fnlgt',
        'education',
        'education-num',
        'marital-status',
        'occupation',
        'relationship',
        'race',
        'sex',
        'capital-gain',
        'capital-loss',
        'hours-per-week',
        'native-country',
        'salary'
    }

    assert set(data.columns) == features


# TODO: implement the third test. Change the function name and input as needed
def test_model_type():
    """
    testing that the model is random forest classifier 
    """
    # Your code here
    sample_x = [[0, 1, 2], [3, 4, 5]]
    sample_y = ['col1', 'col2']

    model = train_model(sample_x, sample_y)

    assert isinstance(model, RandomForestClassifier)
