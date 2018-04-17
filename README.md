# research-visualizer
Simple HTML visualization of the quantitative research results

## Motivation
When you run quantitative researches through external agencies, they commonly give you the SAV file (format used by the IBM SPSS software package).

SPSS is very expensive, requires skills, and may be an overkill for most tasks.

The tool uses raw CSV data exported from SAV to create HTML visualizations.

## How to use

I don't have SPSS, so I used a free GNU alternative called <a href="https://www.gnu.org/software/pspp/">PSPP</a>.

The usage is as follows:

<ol>
  <li>
    Load the SAV file in PSPP.
  </li>
  <li>
    Export the data to CSV through running the following commands (syntaxes):
    <ul>
      <li>SAVE TRANSLATE /OUTFILE="data_values.csv" /TYPE=CSV /FIELDNAMES.</li>
      <li>SAVE TRANSLATE /OUTFILE="data_labels.csv" /TYPE=CSV /FIELDNAMES /CELLS=LABELS.</li>
    </ul>
  </li>
  <li>
    Then run the syntax
    <ul>
      <li>DISPLAY LABELS.</li>
    </ul>
    and save the output into a text file, e.g. data_variables.txt.
  </li>
  <li>
    These 3 files contain all the data required to visualize the survey.
  </li>
  <li>
    See the next steps in <b>research-visualizer.py</b>.
  </li>
</ol>

## Result

Here's how it looks in real life:

![Example](https://raw.githubusercontent.com/sympho-ru/research-visualizer/master/example.png)

Good enough to insert into presentations, etc.
