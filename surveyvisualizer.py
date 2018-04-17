# encoding: utf-8
import codecs
import os
from string import Template

class SurveyVisualizer:
    def __init__(self, survey):
        self.survey = survey

    def get_color(self, n):
        """
        Returns an (r, g, b) tuple from a nice palette (20 colors)

        Parameters
        ---------
        n : int
            Index in the palette
        """
        navy = [(69, 116, 190), (144, 172, 215), (182, 200, 229), (217, 226, 241)]
        blue = [(97, 157, 209), (158, 196, 226), (191, 215, 236), (222, 235, 245)]
        green = [(116, 171, 82), (170, 206, 147), (199, 222, 183), (226, 239, 219)]
        yellow = [(251, 190, 64), (253, 215, 118), (252, 227, 161), (255, 240, 208)]
        red = [(233, 125, 68), (241, 177, 138), (245, 203, 176), (249, 229, 215)]
        colors = []
        for i in range(4):
            colors += [navy[i], blue[i], green[i], yellow[i], red[i]]
        if n >= len(colors): n = n % len(colors)
        return colors[n]

    def visualize_all(self, outputfile):
        """
        Visualizes survey answers for all questions, and saves them into a file

        Parameters
        ----------
        outputfile : str
            Path to the output file
        """
        with open('templates/page.html') as f1, open('templates/question.html') as f2:
            page = Template(f1.read())
            question = Template(f2.read())
        questions = ''
        for column_name in self.survey.data_values.columns[1:]: # Skipping first column because it's usually ids of the respondents
            html_answers = self.visualize_column(column_name) # Visualization of a column = answers to one survey question
            title = str(column_name) + ". " + self.survey.variable_label_mapping[column_name]
            title = title.decode('utf-8')
            questions += question.substitute({'title': title, 'answers': html_answers})
        page = page.substitute({'questions': questions})
        self.save_to_file(outputfile, page)
        return True

    def visualize_column(self, column_name, view = "bars"):
        """
        Visualizes one column of the survey (answers to one survey question)

        Parameters
        ----------
        column_name : str
            Name of the column (aka PSPP variable)
        """
        with open('templates/answer.html') as f:
            answer = Template(f.read())
        value_counts = self.survey.get_column_value_counts(column_name)
        answers = ''
        for i, (value, count) in enumerate(value_counts):
            if count == 0: continue # Don't output values with zero count
            label = self.survey.value_label_mapping[column_name][value]
            label = str(label).decode('utf-8')
            width = 100.0 * count / self.survey.total_weight
            width = "{0:.1f}%".format(width)
            percent = 100.0 * count / self.survey.total_weight
            percent = "{0:.1f}%".format(percent)
            percent = percent.replace("99.9%", "100%") # To make it prettier
            r, g, b = self.get_color(i)
            color = "rgba({}, {}, {}, 1)".format(r, g, b)
            values = {'label': label, 'width': width, 'color': color, 'percent': percent, 'count': count}
            answers += answer.substitute(values)
        return answers

    def save_to_file(self, filename, text):
        """
        Creates a path, if necessary, and saves given text into it

        Parameters
        ---------
        filename : str
            Name and path of the file
        text : str
            Text to save
        """        
        path = filename.split('/')
        path = '/'.join(path[:-1])
        if not os.path.isdir(path):
            os.makedirs(path)
        with codecs.open(filename, "w", "utf-8") as text_file:
            text_file.write(text)

