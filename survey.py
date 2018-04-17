# encoding: utf-8
import pandas as pd
import numpy as np

class Survey:
    default_empty_code = 6101
    default_empty_label = '(Not available)'
    
    def __init__(self, data_values, data_labels, data_variables):
        """
        Initialization

        Parameters
        ----------
        data_values : pandas.core.frame.DataFrame
            Pandas DataFrame with numerical survey responses
            Loaded from CSV that is created by running the following command in PSPP:
                SAVE TRANSLATE /OUTFILE="data_values.csv" /TYPE=CSV /FIELDNAMES.
        data_labels: pandas.core.frame.DataFrame
            Pandas DataFrame with text survey responses
            Loaded from CSV that is created by running the following command in PSPP:
                SAVE TRANSLATE /OUTFILE="data_labels.csv" /TYPE=CSV /FIELDNAMES /CELLS=LABELS.
        data_variables: str
            String with survey questions and labels
            Created by running the following command in PSPP:
                DISPLAY LABELS.
        """
        self.data_values = self.process_values(data_values)
        self.data_labels = self.process_labels(data_labels)
        self.data_variables = data_variables # Used to create child objects (survey subsets)
        self.variable_label_mapping = self.parse_variable_label_mapping(data_variables)
        self.add_weights_column()
        self.total_weight = self.calculate_total_weight() # Total weight is opdated automatically when different weights are set
        self.value_label_mapping = self.calculate_value_label_mapping()
        assert len(data_values) == len(data_labels), "Something went wrong, values and labels are not equal"
        self.num_rows, self.num_cols = self.data_values.shape
        
    def process_values(self, data_values, empty_code = default_empty_code):
        """
        Cleans up the DataFrame with values and makes it numerical only

        Parameters
        ----------
        data_values : pandas.core.frame.DataFrame
            Pandas DataFrame with numerical survey responses
        """
        data_values = data_values.replace(' ', np.nan)
        data_values = data_values.dropna(how='all') # When PSPP exports to CSV, it may sometimes create empty rows
        data_values = data_values.replace(np.nan, empty_code)
        data_values = self.convert_to_numbers(data_values, empty_code=empty_code)
        return data_values

    def convert_to_numbers(self, data_values, empty_code = default_empty_code, dtype = 'int32'):
        """
        Makes the DataFrame numerical only

        Parameters
        ----------
        data_values : pandas.core.frame.DataFrame
            Pandas DataFrame with numerical survey responses
        """
        num_cols = data_values.shape[1]
        for i in range(0, num_cols):
            try:
                column = data_values.iloc[:, i].astype(dtype)
            except ValueError:
                # Column contains strings, making it one-hot-encoded. E.g. "Answer1; Answer2; Answer3; Answer1; Answer4" becomes "1; 2; 3; 1; 4"
                column = self.build_one_hot_column(data_values.iloc[:, i], empty_code=empty_code)
                column = column.astype(dtype)
            data_values.iloc[:, i] = column.values
        return data_values

    def build_one_hot_column(self, column, empty_code = default_empty_code):
        """
        Building a one-hot-encoded column from a string column

        Parameters
        ----------
        column : pandas.core.frame.DataFrame
            Column of Pandas DataFrames
        """
        unique_values = np.unique(column)
        for i, value in enumerate(unique_values):
            if value != empty_code:
                column = column.replace(value, i) # Replacing each unique value with its index
        return column

    def process_labels(self, data_labels, empty_code = default_empty_label):
        """
        Cleans up the DataFrame with labels

        Parameters
        ----------
        data_labels : pandas.core.frame.DataFrame
            Pandas DataFrame with text survey responses
        """        
        data_labels = data_labels.replace(' ', np.nan)
        data_labels = data_labels.dropna(how='all') # When PSPP exports to CSV, it may sometimes create empty rows
        data_labels = data_labels.replace(np.nan, empty_code)
        return data_labels

    def parse_variable_label_mapping(self, data_variables):
        """
        Builds a dictionary of variable labels

        Parameters
        ----------
        data_variables : str
            String with survey questions and labels (SPSS/PSPP output)
            Example:
                Variable            Label                                              Position
                ═══════════════════════════════════════════════════════════════════════════════
                                 S5 What field do you work in?                                7
                                 S6 Which of the following better describes your              8
                                    current employment status?
                                 S7 You mentioned you’re currently a full-time student        9
                                    In which of the following levels of school are you
                                    currently enrolled?
            The goal is to extract combinations like {S5 : "What field do you work in"?} and return the resulting dictionary
        """
        coding = {}
        code, description = 'foo', 'bar'
        for line in data_variables.split("\n"):
            line = line.strip()
            if line[0:8] == 'Variable' or '═' in line or line == '':
                # Skipping lines than don't belong to labels
                continue
            if line[-8:].strip().isdigit():
                # If the last 8 symbols of the line are digits (and spaces), then it must be the beginning of a new variable
                code = line[0:line.find(' ')]
                description = line[line.find(' '):-8].strip()
                coding[code] = description
            else:
                # If the line doesn't end with a digit, then it needs to be attached to description
                description += ' ' + line
                coding[code] = description
        return coding

    def drop_rows(self, exclude_values):
        """
        Searches a given column for given values, and removes the respective row if one of the values is found

        Parameters
        ----------
        exclude_values : list
            List of values for which the row needs to be removed
        column_index : int
            Index of the column where to search
        """
        if len(exclude_values) == 0:
            return True
        num_rows = self.data_values.shape[0]
        row_indices = [] # Indices of rows that will be removed from self.data_values and self.data_labels
        column_names = exclude_values.keys()
        for column_name in column_names:
            for row in range(num_rows):
                if self.data_values[column_name].values[row] in exclude_values[column_name]:
                    row_indices.append(row)
        self.data_values.drop(row_indices, axis=0, inplace=True)
        self.data_labels.drop(row_indices, axis=0, inplace=True)
        # Reindexing
        self.data_values.index = range(len(self.data_values))
        self.data_labels.index = range(len(self.data_labels))
        return True

    def add_weights_column(self):
        """
        Adds a new "Weights" column filled with ones
        """
        num_rows = self.data_values.shape[0]
        new_column = np.ones(num_rows)
        self.data_values['Weights'] = new_column
        self.data_labels['Weights'] = new_column
        self.variable_label_mapping['Weights'] = "Weights"
        return True

    def calculate_total_weight(self):
        """
        Sums weights from the "Weights" column
        """
        total_weight = self.data_values['Weights'].sum()
        return total_weight
        
    def set_weights(self, weights):
        """
        Goes through values of a given column, and updates the column "Weights" with weights that each row must have

        Parameters
        ----------
        weights : dict
            Dictionary formatted as {column_name: {value1: weight1, ..., valueN: weightN}}
        """
        if len(weights) == 0:
            return True
        column_name = weights.keys()[0]
        column = self.data_values[column_name]
        # Weights are added so that total weight doesn't change
        total_weight = sum(weights[column_name].values())
        new_column = column.copy()
        unique_values = np.unique(column)
        for value in unique_values:
            value = str(value) # Valid JSON allows string keys only
            new_value = 1.0 * len(unique_values) * weights[column_name][value] / total_weight
            new_column = new_column.replace(value, new_value)
        self.data_values['Weights'] = new_column.values
        self.data_labels['Weights'] = new_column.values
        self.total_weight = self.calculate_total_weight()
        return True

    def calculate_value_label_mapping(self):
        """
        Calculates mapping from values in self.data_values to self.data_labels
        
        Returns a dictionary formatted as {column_name: {value1: label1, ..., valueN: labelN}}
        """
        value_label_mapping = {}
        column_names = self.data_values.columns
        for column_name in column_names:
            values, value_indices = np.unique(self.data_values[column_name], return_index = True) # E.g. ([1, 2, 3, 4, 5], [ 4, 36, 10,  0, 60])
            labels, label_indices  = np.unique(self.data_labels[column_name], return_index = True) # E.g. (['red', 'orange', 'yellow', 'green', 'blue'], [ 4, 10, 60,  0, 36])
            # Sorting by indices, so that unique values and labels appear in the same order
            values_sorted = [value[1] for value in sorted(zip(value_indices, values))]
            labels_sorted = [label[1] for label in sorted(zip(label_indices, labels))]
            column_mapping = {}
            for index, value in enumerate(values_sorted):
                column_mapping[value] = labels_sorted[index]
            value_label_mapping[column_name] = column_mapping
        return value_label_mapping

    def get_column_value_counts(self, column_name, use_weights = True):
        """
        Calculates the number of different answers in a given column

        Returns a list of tuples: [(answer1, count1), ..., (answerN, countN)]

        Parameters
        ----------
        column_name : str
            Name of the column to be analyzed
        """
        column_value_counts = []
        for value in self.value_label_mapping[column_name].keys(): # Using self.value_label_mapping because it's sorted
            value_vector = (self.data_values[column_name] == value)
            if use_weights:
                weighted_count = self.data_values['Weights'][value_vector].sum()
                weighted_count = int(round(weighted_count))
                column_value_counts.append((value, weighted_count))
            else:
                count = value_vector.sum()
                column_value_counts.append((value, count))
        column_value_counts.sort()
        return column_value_counts

    def get_subset_survey(self, filter):
        """
        Filters the survey using a given rule and creates another Survey object

        Parameters
        ----------
        filter : dict
            Dictionary formatted as {column_name: value}
        """
        for variable, value in filter.iteritems():
            rule = (self.data_values[variable] == value)
            subset_data_values = self.data_values[rule]
            subset_data_labels = self.data_labels[rule]
        return Survey(subset_data_values, subset_data_labels, self.data_variables)

