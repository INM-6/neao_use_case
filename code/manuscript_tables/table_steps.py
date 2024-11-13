from manuscript_tables.utils import (
    load_results_csv, save_table_latex, extract_text_from_values,
    get_text_from_values_after_token, aggregate_table, BASE_PATH_RE)


###########
# TABLE A #
###########

# Load results of query listing the AnalysisStep classes used to generate
# any result file
raw_results_steps = load_results_csv("steps_raw.csv")

# Clean long paths, adding ... as a replacer
results_steps = get_text_from_values_after_token(raw_results_steps,
                                                      column="file_path",
                                                      text_token="outputs/analyses",
                                                      prefix="...")

# Replace base URI of the class with prefix
results_steps = get_text_from_values_after_token(results_steps,
                                                      column="neao_class",
                                                      text_token="#",
                                                      prefix="neao_steps:",
                                                      inplace=True)

# Sort by file path
results_steps = results_steps.sort_values(['file_path', 'neao_class'])

# Save table to LaTeX, with the first/last rows
save_table_latex(results_steps,
                 "table_steps_A.txt",
                 rows_begin=5,
                 rows_end=5,
                 columns={'file_path': "File path",
                          'neao_class': "NEAO step class"},
                 top_row="\\textbf{A}")


###########
# TABLE B #
###########

# Aggregate table to get file counts for each class according to base path
results_steps_root = extract_text_from_values(results_steps,
                                                   column='file_path',
                                                   regex=BASE_PATH_RE)

aggregated_steps = aggregate_table(results_steps_root,
                                        rows="neao_class",
                                        columns="file_path")

# Rearrange column order
columns = list(aggregated_steps.columns.values)
column_order = [columns[0], *columns[2:], columns[1]]
aggregated_steps = aggregated_steps[column_order]

# Save
save_table_latex(aggregated_steps,
                 "table_steps_B.txt",
                 columns={'file_path': "File count per root file path",
                          'neao_class': "NEAO step class"},
                 multicolumn_line="2-7",
                 break_line_patterns=("(.+/)(.+)",),
                 column_format="lP{2.1cm}P{2.3cm}P{2.3cm}P{2.5cm}P{2.5cm}P{2.2cm}",
                 top_row="\\textbf{B}",
                 multicolumn=True,
                 multicolumn_format="c")
