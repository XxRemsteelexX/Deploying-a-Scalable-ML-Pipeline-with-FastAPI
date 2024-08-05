# Model Card

## Model Details
- Created by Glenn Dalbey 
- Year: 2024
- Version: v1
- Model type: python "RandomForestClassifier" (default parameters)

## Intended Use
- This model is used to predict the income level of individuals based off attiributes such as demographic and employment-related featues. These values are then used to predict an individuals salary being above or below 50k. 

## Training Data
- US cencus data provided by Udacity, its source is located here: https: (// archive.ics.uci.edu/ml/datasets/census+income).
- This data contains information pertaining to individuals, it was from 1994 Census Bureau data from the UCI Machine Learning Repository.

## Evaluation Data
- The data was split to test and train the model at 20% and 80%. 

## Metrics
- A random Forest Classifier model was  used with the default parameters. 
- This model achieved the metric scores below:
- Metric Performance: Precision: 0.7369 | Recall: 0.6294 | F1: 0.6789

## Ethical Considerations
- This model contains features and variables that should not be used for evaluation. 
- This model would not be considered a fair representation because it uses demgraphics that include sage, sex and race, and therefore should nmot be used in a descision making process when evaluating individuals. 

## Caveats and Recommendations
- Default parameters were used, for a more accurate result other models and parameters could be used. 
- The Census database used is from 1994, the data provided is most likely out of date and inacurate. 
- Individuals that are under represented in these demographics may not be acuratly portrayed. 
 