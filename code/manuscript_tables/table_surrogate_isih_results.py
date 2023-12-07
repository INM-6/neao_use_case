from manuscript_tables.utils import (
    load_results_csv, save_table_latex, extract_text_from_values,
    get_text_from_values_after_token, aggregate_table,
    SURROGATE_ISIH_BASE_PATH_RE)


###########
# TABLE A #
###########

# Load results of query listing if an interspike interval histogram was plotted
# from a spike train surrogate

raw_results_surrogate_isih_source = \
    load_results_csv("surrogate_isih_source_raw.csv")

# Clean long paths, adding ... as a replacer
results_surrogate_isih_source = \
    get_text_from_values_after_token(raw_results_surrogate_isih_source,
                                                      column="file_path",
                                                      text_token="outputs/analyses/reach2grasp",
                                                      prefix="...")

# Aggregate table to get file counts for each class according to base path
results_surrogate_isih_source_root = extract_text_from_values(
                                                   results_surrogate_isih_source,
                                                   column='file_path',
                                                   regex=SURROGATE_ISIH_BASE_PATH_RE)

aggregated_surrogate_isih_source = aggregate_table(results_surrogate_isih_source_root,
                                        rows=["file_path"])

save_table_latex(aggregated_surrogate_isih_source,
                 "table_surrogate_isih_results_A.txt",
                 columns={'file_path': "Root file path",
                          'values': "File count"},
                 top_row="\\textbf{A}",
                 column_format="lr")


###########
# TABLE B #
###########

# Load results of query listing the surrogate generation method classes and
# the number of surrogates used
raw_results_surrogate_method_and_count = \
    load_results_csv("surrogate_isih_method_and_count_raw.csv")

# Clean long paths, adding ... as a replacer
results_surrogate_method_and_count = \
    get_text_from_values_after_token(raw_results_surrogate_method_and_count,
                                                      column="file_path",
                                                      text_token="outputs/analyses/reach2grasp",
                                                      prefix="...")

# Replace base URI of the class with prefix
results_surrogate_method_and_count = get_text_from_values_after_token(results_surrogate_method_and_count,
                                                      column="neao_class",
                                                      text_token="#",
                                                      prefix="neao_steps:",
                                                      inplace=True)

# Aggregate table to get file counts for each class according to base path
results_surrogate_method_and_count_root = extract_text_from_values(
                                                   results_surrogate_method_and_count,
                                                   column='file_path',
                                                   regex=SURROGATE_ISIH_BASE_PATH_RE)

aggregated_surrogate_method_and_count = aggregate_table(
                                            results_surrogate_method_and_count_root,
                                            rows=["file_path", "n_surr"],
                                            columns="neao_class")

save_table_latex(aggregated_surrogate_method_and_count,
                 "table_surrogate_isih_results_B.txt",
                 columns={'file_path': "Root file path",
                          'n_surr': "Number of surrogates",
                          'neao_class': "NEAO spike train surrogate generation class"},
                 top_row="\\textbf{B}",
                 multicolumn_line="3-4",
                 break_line_patterns=("(.+Generate)(.+)(Surrogate)",),
                 column_format="lP{3cm}P{5cm}P{5cm}",
                 multicolumn=True,
                 multicolumn_format="c")


###########
# TABLE C #
###########

# Load results of query listing the parameter class and value for the
# surrogate generation step of each file that have a ISIH result derived from
# a spike train surrogate
raw_results_surrogate_isih_surr_parameters = load_results_csv(
    "surrogate_isih_surr_parameters_raw.csv")

# Clean long paths, adding ... as a replacer
results_surrogate_isih_surr_parameters = get_text_from_values_after_token(
                                     raw_results_surrogate_isih_surr_parameters,
                                     column="file_path",
                                     text_token="outputs/analyses/reach2grasp",
                                     prefix="...")

# Replace base URI of the class with prefix
results_surrogate_isih_surr_parameters = get_text_from_values_after_token(
                                     results_surrogate_isih_surr_parameters,
                                     column="parameter_class",
                                     text_token="#",
                                     prefix="neao_params:",
                                     inplace=True)

# Aggregate table to get file counts for each parameter/value according to
# base path. Root file paths will be in columns.
results_surrogate_isih_surr_parameters_root = extract_text_from_values(
                                     results_surrogate_isih_surr_parameters,
                                     column='file_path',
                                     regex=SURROGATE_ISIH_BASE_PATH_RE)

aggregated_surrogate_isih_surr_parameters = aggregate_table(
                                     results_surrogate_isih_surr_parameters_root,
                                     rows=["parameter_class",
                                           "value"],
                                     columns="file_path")


save_table_latex(aggregated_surrogate_isih_surr_parameters,
                 "table_surrogate_isih_results_C.txt",
                 columns={'file_path': "File count per root file path",
                          'parameter_class': "NEAO class",
                          'value': "Value"},
                 top_row="\\textbf{C}",
                 column_format="llcc",
                 multicolumn_line="3-4",
                 multicolumn=True,
                 multicolumn_format="c")


###########
# TABLE D #
###########

# Load results of query listing if the bin size of interspike interval
# histograms computed from a spike train surrogate

raw_results_surrogate_isih_bin_size = \
    load_results_csv("surrogate_isih_bin_size_raw.csv")

# Clean long paths, adding ... as a replacer
results_surrogate_isih_bin_size = \
    get_text_from_values_after_token(raw_results_surrogate_isih_bin_size,
                                                      column="file_path",
                                                      text_token="outputs/analyses/reach2grasp",
                                                      prefix="...")

# Aggregate table to get file counts for each class according to base path
results_surrogate_isih_bin_size_root = extract_text_from_values(
                                                   results_surrogate_isih_bin_size,
                                                   column='file_path',
                                                   regex=SURROGATE_ISIH_BASE_PATH_RE)

aggregated_surrogate_isih_bin_size = aggregate_table(results_surrogate_isih_bin_size_root,
                                        rows=["file_path", "bin_size"])

save_table_latex(aggregated_surrogate_isih_bin_size,
                 "table_surrogate_isih_results_D.txt",
                 columns={'file_path': "Root file path",
                          'bin_size': "Bin size",
                          'values': "File count"},
                 top_row="\\textbf{D}",
                 column_format="lcr")
