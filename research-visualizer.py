import json
import pandas as pd
from survey import Survey
from surveyvisualizer import SurveyVisualizer

# Survey parameters
survey_name = 'privacy'
segment_name = 'all' # Overwritten later
values_file = 'data/{}_values.csv'.format(survey_name)
labels_file = 'data/{}_labels.csv'.format(survey_name)
variables_file = 'data/{}_variables.txt'.format(survey_name)
settings_file = 'data/{}.json'.format(survey_name)

# Loading data and settings
data_values = pd.read_csv(values_file, sep=',')
data_labels = pd.read_csv(labels_file, sep=',')
with open(variables_file, 'r') as f_vars:
    data_variables = f_vars.read()
try:
    with open(settings_file, 'r') as settings: settings_json = json.load(settings)
except IOError:
    settings_json = json.loads('{}')

# Parsing settings
exclude_ids = []
suspicious_ids = []
weights = {}
if 'exclude_ids' in settings_json: exclude_ids = settings_json['exclude_ids']
if 'exclude_ids' in settings_json: suspicious_ids = settings_json['suspicious_ids']
if 'weights' in settings_json: weights = settings_json['weights']

# Building survey
survey = Survey(data_values, data_labels, data_variables)

# Dropping bad answers
survey.drop_rows(exclude_ids)
survey.drop_rows(suspicious_ids)

# Normalizing survey
survey.set_weights(weights)

# Segment
segment_name = 'usa' # Overwrite later
survey = survey.get_subset_survey({"COUNTRY" : 9})
survey.set_weights(weights)

# Visualizing
vis = SurveyVisualizer(survey)
outputfile = "output/{}/{}.html".format(survey_name, segment_name)
vis.visualize_all(outputfile=outputfile)

