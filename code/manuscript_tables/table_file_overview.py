from manuscript_tables.utils import (
    load_results_csv, save_table_latex, extract_text_from_values,
    get_text_from_values_after_token, aggregate_table, BASE_PATH_RE)


###########
# TABLE A #
###########

# Load results of query listing any input dataset used
raw_results_input_datasets = load_results_csv(
    "file_overview_input_datasets_raw.csv")

# Clean long paths, adding ... as a replacer
results_input_datasets = get_text_from_values_after_token(
                                           raw_results_input_datasets,
                                           column="input_dataset_file_path",
                                           text_token="datasets_nix",
                                           prefix="...")

results_input_datasets = get_text_from_values_after_token(
                                           results_input_datasets,
                                           column="output_file_path",
                                           text_token="outputs/analyses",
                                           prefix="...", inplace=True)

# Save table to LaTeX, with the first/last three rows
save_table_latex(results_input_datasets,
                 "table_file_overview_A.txt",
                 rows_begin=3,
                 rows_end=3,
                 columns={'input_dataset_file_path': "Input dataset file path",
                          'output_file_path': "Output plot file path"},
                 top_row="\\textbf{A}")


###########
# TABLE B #
###########

# Aggregate table A to get file counts according to base path
results_input_datasets_root = extract_text_from_values(
                                         raw_results_input_datasets,
                                         column='output_file_path',
                                         regex=BASE_PATH_RE)

aggregated_input_datasets_root = aggregate_table(results_input_datasets_root,
                                                 rows="output_file_path")

save_table_latex(aggregated_input_datasets_root,
                 "table_file_overview_B.txt",
                 columns={'output_file_path': "Output plot root file path",
                          'values': "File count"},
                 top_row="\\textbf{B}")


###########
# TABLE C #
###########

# Load results of query listing any file written
raw_results_files_written = load_results_csv(
    "file_overview_files_written_raw.csv")

# Aggregate to get file counts according to base path
results_files_written_root = extract_text_from_values(
                                          raw_results_files_written,
                                          column='output_file_path',
                                          regex=BASE_PATH_RE)

aggregated_files_written_root = aggregate_table(
                                          results_files_written_root,
                                          rows="output_file_path")

save_table_latex(aggregated_files_written_root,
                 "table_file_overview_C.txt",
                 columns={'output_file_path': "Output plot root file path",
                          'values': "File count"},
                 top_row="\\textbf{C}")
