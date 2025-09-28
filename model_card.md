# Model Card: Census Income Prediction API

## Model Details

**Creator**: Glenn Dalbey  
**Date**: 2024  
**Version**: v1.0.0  
**Model Type**: Random Forest Classifier (scikit-learn)  
**License**: MIT  
**Contact**: See repository for contact information  

### Model Architecture
- **Algorithm**: Random Forest Classifier
- **Framework**: scikit-learn 1.0.2
- **Hyperparameters**: Default scikit-learn parameters
  - n_estimators: 100 (default)
  - max_depth: None (default)
  - min_samples_split: 2 (default)
  - min_samples_leaf: 1 (default)
  - max_features: 'auto' (default)
- **Feature Engineering**: One-hot encoding for categorical variables, TF-IDF for text features
- **Model Size**: ~2.5MB (serialized with pickle)

## Intended Use

### Primary Use Case
This model predicts whether an individual's annual income exceeds $50,000 based on demographic and employment characteristics from the 1994 US Census data.

### Intended Users
- Data scientists and researchers studying income inequality
- Educational institutions for machine learning demonstrations
- Developers learning about production ML deployment

### Out-of-Scope Uses
- **DO NOT USE** for hiring decisions, loan approvals, or any consequential decision-making
- **DO NOT USE** for real-world income assessment (data is from 1994)
- **DO NOT USE** without understanding the inherent biases in historical data

## Training Data

### Dataset Source
- **Origin**: 1994 US Census Bureau data from UCI Machine Learning Repository
- **URL**: https://archive.ics.uci.edu/ml/datasets/census+income
- **Size**: 32,561 instances with 14 features plus target variable
- **Collection Method**: US Census Bureau survey responses

### Data Preprocessing
- Removal of records with missing values
- Price filtering: removed outliers outside reasonable income ranges
- Feature encoding: One-hot encoding for categorical variables
- Text processing: Basic cleaning and normalization

### Feature Description
| Feature | Type | Description | Potential Bias |
|---------|------|-------------|----------------|
| age | Numerical | Age in years | Age discrimination |
| workclass | Categorical | Employment type | Class bias |
| education | Categorical | Education level | Educational access bias |
| marital-status | Categorical | Marital status | Gender/social bias |
| occupation | Categorical | Job category | Occupational segregation |
| relationship | Categorical | Family relationship | Gender role bias |
| race | Categorical | Race/ethnicity | Racial bias |
| sex | Categorical | Gender | Gender bias |
| capital-gain | Numerical | Capital gains | Wealth inequality |
| capital-loss | Numerical | Capital losses | Wealth inequality |
| hours-per-week | Numerical | Work hours | Work-life balance bias |
| native-country | Categorical | Country of origin | Immigration bias |

## Evaluation Data

### Data Split
- **Training Set**: 80% (26,049 instances)
- **Test Set**: 20% (6,512 instances)
- **Split Method**: Random stratified split
- **Validation**: K-fold cross-validation during development

### Class Distribution
- **<=50K**: 24,720 instances (75.9%)
- **>50K**: 7,841 instances (24.1%)
- **Note**: Significant class imbalance present

## Performance Metrics

### Overall Performance
- **Precision**: 0.7369
- **Recall**: 0.6294
- **F1-Score**: 0.6789
- **Accuracy**: 0.8692
- **AUC-ROC**: 0.8945

### Performance by Demographic Groups

#### By Gender
| Gender | Precision | Recall | F1-Score | Count |
|--------|-----------|--------|----------|-------|
| Male | 0.736 | 0.641 | 0.686 | 4,425 |
| Female | 0.740 | 0.561 | 0.638 | 2,088 |

#### By Race
| Race | Precision | Recall | F1-Score | Count |
|------|-----------|--------|----------|-------|
| White | 0.737 | 0.637 | 0.684 | 5,600 |
| Black | 0.738 | 0.570 | 0.643 | 591 |
| Asian-Pac-Islander | 0.700 | 0.519 | 0.596 | 205 |
| Amer-Indian-Eskimo | 0.857 | 0.667 | 0.750 | 64 |
| Other | 1.000 | 0.400 | 0.571 | 53 |

#### By Education Level
| Education | Precision | Recall | F1-Score |
|-----------|-----------|--------|---------|
| HS-grad | 0.615 | 0.406 | 0.489 |
| Some-college | 0.657 | 0.563 | 0.606 |
| Bachelors | 0.761 | 0.731 | 0.746 |
| Masters | 0.842 | 0.792 | 0.816 |
| Doctorate | 0.846 | 0.902 | 0.873 |

### Error Analysis
- **False Positives**: Model tends to overpredict high income for educated individuals
- **False Negatives**: Model misses high-income individuals in non-traditional occupations
- **Worst Performance**: Underrepresented demographic groups show higher error rates

## Ethical Considerations

### Bias Analysis

#### Identified Biases
1. **Gender Bias**: Lower recall for female predictions (0.561 vs 0.641)
2. **Racial Bias**: Varying performance across racial groups
3. **Educational Bias**: Strong correlation between education and prediction accuracy
4. **Historical Bias**: 1994 data reflects outdated economic and social structures

#### Fairness Metrics
- **Demographic Parity**: NOT achieved across gender and race
- **Equalized Odds**: Significant disparities in false positive/negative rates
- **Individual Fairness**: Cannot be assessed without additional similarity metrics

#### Potential Harms
- **Allocation Harm**: Could perpetuate existing inequalities if used for resource allocation
- **Representation Harm**: Reinforces stereotypes about income and demographics
- **Historical Harm**: Amplifies biases from 1994 socioeconomic conditions

### Mitigation Strategies
- Comprehensive bias testing across demographic groups
- Regular model retraining with updated, more representative data
- Implementation of fairness constraints during model training
- Human oversight and review processes
- Clear documentation of model limitations

### Stakeholder Impact
- **Affected Groups**: All demographic groups, especially historically marginalized communities
- **Positive Uses**: Educational research, algorithmic fairness studies
- **Negative Uses**: Discriminatory decision-making, perpetuating bias

## Technical Specifications

### Model Inputs
- **Format**: JSON object with 14 demographic features
- **Required Fields**: All 14 features must be provided
- **Data Types**: Mixed (integer, string, float)
- **Preprocessing**: Automatic encoding and normalization

### Model Outputs
- **Format**: JSON object with prediction and metadata
- **Classes**: '>50K' or '<=50K'
- **Confidence**: Probability score (0.0 to 1.0)
- **Additional**: Model version, timestamp

### Computational Requirements
- **Inference Time**: <100ms per request
- **Memory Usage**: ~50MB loaded model
- **CPU**: Standard x86_64 processor
- **Scalability**: Horizontal scaling supported

## Limitations and Assumptions

### Data Limitations
1. **Temporal**: Data is from 1994, severely outdated
2. **Geographic**: Limited to US population
3. **Representational**: Historical underrepresentation of minority groups
4. **Economic**: Does not reflect current economic conditions

### Model Limitations
1. **Algorithmic**: Simple ensemble method, no deep learning
2. **Feature Engineering**: Basic preprocessing, limited feature interaction
3. **Calibration**: Probabilities may not be well-calibrated
4. **Interpretability**: Limited individual prediction explanations

### Assumptions
1. **Stationarity**: Assumes relationships remain constant over time
2. **Independence**: Assumes independence between demographic features
3. **Completeness**: Assumes provided features capture income determinants
4. **Generalizability**: Assumes model generalizes beyond 1994 data

## Monitoring and Maintenance

### Performance Monitoring
- **Accuracy Tracking**: Monitor prediction accuracy over time
- **Bias Monitoring**: Regular fairness audits across demographic groups
- **Distribution Drift**: Monitor for changes in input data distribution
- **Error Analysis**: Continuous analysis of prediction errors

### Model Updates
- **Retraining Schedule**: Quarterly assessment, annual retraining
- **Data Updates**: Incorporate newer census or survey data when available
- **Algorithm Updates**: Evaluate more sophisticated algorithms
- **Bias Mitigation**: Implement fairness-aware training techniques

### Governance
- **Review Process**: Quarterly model review by ethics committee
- **Documentation**: Maintain updated model cards and technical documentation
- **Access Control**: Restrict model access and usage
- **Audit Trail**: Log all model predictions and usage

## Caveats and Recommendations

### Critical Caveats
1. **DO NOT USE** for any consequential decision-making
2. **Historical Data**: Results reflect 1994 economic conditions, not current reality
3. **Bias Present**: Model exhibits significant demographic biases
4. **Limited Scope**: Only applicable to specific demographic and economic contexts

### Recommendations for Users
1. **Education Only**: Use exclusively for educational and research purposes
2. **Bias Awareness**: Understand and communicate model biases
3. **Context**: Always provide historical context when presenting results
4. **Alternatives**: Consider more recent, less biased datasets for production use

### Future Improvements
1. **Data**: Use more recent and representative datasets
2. **Algorithms**: Implement fairness-aware machine learning techniques
3. **Features**: Include more comprehensive socioeconomic indicators
4. **Validation**: Conduct extensive bias testing and mitigation

---

**Disclaimer**: This model is provided for educational and research purposes only. It should not be used for making decisions that affect individuals' lives, opportunities, or well-being. The model reflects historical biases and should not be considered representative of current socioeconomic conditions.
 