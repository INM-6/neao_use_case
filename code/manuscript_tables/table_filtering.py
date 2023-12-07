from manuscript_tables.utils import (
    load_results_csv, save_table_latex, extract_text_from_values,
    get_text_from_values_after_token, aggregate_table, PSD_BASE_PATH_RE)


###########
# TABLE A #
###########

# Load results of query listing if the PSD results had an input that derived
# from the output of a filter step
raw_results_psd_filter = load_results_csv("psd_filter_raw.csv")

# Clean long paths, adding ... as a replacer
results_psd_filter = get_text_from_values_after_token(raw_results_psd_filter,
                                                      column="file_path",
                                                      text_token="outputs/analyses/reach2grasp",
                                                      prefix="...")


# Aggregate table to get file counts for each class according to base path
results_psd_filter_root = extract_text_from_values(results_psd_filter,
                                                   column='file_path',
                                                   regex=PSD_BASE_PATH_RE)

aggregated_psd_filter = aggregate_table(results_psd_filter_root,
                                        rows="file_path")

save_table_latex(aggregated_psd_filter,
                 "table_filtering_A.txt",
                 columns={'file_path': "Root file path",
                          'values': "File count"},
                 top_row="\\textbf{A}")


###########
# TABLE B #
###########

# Load results of query listing the class for the method used to filter a
# time series used to compute the PSD for each file with PSD results
raw_results_psd_filter_method = load_results_csv("psd_filter_method_raw.csv")

# Clean long paths, adding ... as a replacer
results_psd_filter_method = get_text_from_values_after_token(
                                              raw_results_psd_filter_method,
                                              column="file_path",
                                              text_token="outputs/analyses/reach2grasp",
                                              prefix="...")

# Replace base URI of the class with prefix
results_psd_filter_method = get_text_from_values_after_token(
                                              results_psd_filter_method,
                                              column="neao_class",
                                              text_token="#",
                                              prefix="neao_steps:",
                                              inplace=True)

# Aggregate table to get file counts for class according to base path
results_psd_filter_method_root = extract_text_from_values(
                                              results_psd_filter_method,
                                              column='file_path',
                                              regex=PSD_BASE_PATH_RE)

aggregated_psd_filter_method = aggregate_table(
                                        results_psd_filter_method_root,
                                        rows="file_path",
                                        columns="neao_class")

save_table_latex(aggregated_psd_filter_method,
                 "table_filtering_B.txt",
                 columns={'file_path': "Root file path",
                          'neao_class': "NEAO filtering class"},
                 top_row="\\textbf{B}",
                 multicolumn_line="2",
                 column_format="lP{4cm}",
                 multicolumn=True,
                 multicolumn_format="c")


###########
# TABLE C #
###########

# Load results of query listing the parameter class and value for the filter
# step of each file that have a PSD result
raw_results_psd_filter_parameters = load_results_csv(
    "psd_filter_parameters_raw.csv")

# Clean long paths, adding ... as a replacer
results_psd_filter_parameters = get_text_from_values_after_token(
                                     raw_results_psd_filter_parameters,
                                     column="file_path",
                                     text_token="outputs/analyses/reach2grasp",
                                     prefix="...")

# Replace base URI of the class with prefix
results_psd_filter_parameters = get_text_from_values_after_token(
                                     results_psd_filter_parameters,
                                     column="parameter_class",
                                     text_token="#",
                                     prefix="neao_params:",
                                     inplace=True)

# Aggregate table to get file counts for each parameter/value according to
# base path. Root file paths will be in columns.
results_psd_filter_parameters_root = extract_text_from_values(
                                     results_psd_filter_parameters,
                                     column='file_path',
                                     regex=PSD_BASE_PATH_RE)

aggregated_psd_filter_parameters = aggregate_table(
                                     results_psd_filter_parameters_root,
                                     rows=["parameter_class",
                                           "value"],
                                     columns="file_path")


save_table_latex(aggregated_psd_filter_parameters,
                 "table_filtering_C.txt",
                 columns={'file_path': "File count per root file path",
                          'parameter_class': "NEAO class",
                          'value': "Value"},
                 top_row="\\textbf{C}",
                 column_format="llccc",
                 multicolumn_line="3-5",
                 multicolumn=True,
                 multicolumn_format="c")
