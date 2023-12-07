from manuscript_tables.utils import (
    load_results_csv, save_table_latex, extract_text_from_values,
    get_text_from_values_after_token, aggregate_table, sort_table,
    PSD_BASE_PATH_RE)
from re import match


def sort_psd_method_welch_parameters(row):
    # Function to sort table C, according to the commonality of parameters in
    # the two implementations of Welch.
    # First are parameters shared by both packages, then Elephant, and then
    # Scipy
    if (row[('file_path', '.../psd_by_trial')] and
            row[('file_path', '.../psd_by_trial_3')]):
        return 1
    elif row[('file_path', '.../psd_by_trial')]:
        return 2
    return 3


def convert_exponential_notation(value):
    if match(r".+e[+-].+", value):
        return str(float(value))
    return value


###########
# TABLE A #
###########

# Load results of query listing the method class for each file with PSD results
raw_results_psd_method = load_results_csv("psd_method_raw.csv")

# Clean long paths, adding ... as a replacer
results_psd_method = get_text_from_values_after_token(raw_results_psd_method,
                                                      column="file_path",
                                                      text_token="outputs/analyses/reach2grasp",
                                                      prefix="...")

# Replace base URI of the class with prefix
results_psd_method = get_text_from_values_after_token(results_psd_method,
                                                      column="neao_class",
                                                      text_token="#",
                                                      prefix="neao_steps:",
                                                      inplace=True)

# Aggregate table to get file counts for each class according to base path
results_psd_method_root = extract_text_from_values(results_psd_method,
                                                   column='file_path',
                                                   regex=PSD_BASE_PATH_RE)

aggregated_psd_method = aggregate_table(results_psd_method_root,
                                        rows="file_path",
                                        columns="neao_class")

save_table_latex(aggregated_psd_method,
                 "table_psd_results_A.txt",
                 columns={'file_path': "Root file path",
                          'neao_class': "NEAO PSD computation class"},
                 top_row="\\textbf{A}",
                 multicolumn_line="2-3",
                 break_line_patterns=("(.+Compute)(Power.+Density)(.+)",),
                 column_format="lP{4cm}P{4cm}",
                 multicolumn=True,
                 multicolumn_format="c")


###########
# TABLE B #
###########

# Load results of query listing the package and version for the method
# used to compute the PSD for each file with PSD results
raw_results_psd_method_package = load_results_csv("psd_method_package_raw.csv")

# Clean long paths, adding ... as a replacer
results_psd_method_package = get_text_from_values_after_token(
                                              raw_results_psd_method_package,
                                              column="file_path",
                                              text_token="outputs/analyses/reach2grasp",
                                              prefix="...")


# Aggregate table to get file counts for each package/version according to
# base path. Root file paths will be in columns.
results_psd_method_package_root = extract_text_from_values(
                                              results_psd_method_package,
                                              column='file_path',
                                              regex=PSD_BASE_PATH_RE)

aggregated_psd_method_package = aggregate_table(
                                        results_psd_method_package_root,
                                        rows=["package_name",
                                              "package_version"],
                                        columns="file_path")

save_table_latex(aggregated_psd_method_package,
                 "table_psd_results_B.txt",
                 columns={'file_path': "File count per root file path",
                          'package_name': "Package",
                          'package_version': "Version"},
                 top_row="\\textbf{B}",
                 column_format="llccc",
                 multicolumn_line="3-5",
                 multicolumn=True,
                 multicolumn_format="c")


###########
# TABLE C #
###########

# Load results of query listing the parameter class and value for each file
# that have a PSD result computed by the Welch method
raw_results_psd_method_welch_parameters = load_results_csv(
    "psd_method_welch_parameters_raw.csv")

# Clean long paths, adding ... as a replacer
results_psd_method_welch_parameters = get_text_from_values_after_token(
                                     raw_results_psd_method_welch_parameters,
                                     column="file_path",
                                     text_token="outputs/analyses/reach2grasp",
                                     prefix="...")

# Replace base URI of the class with prefix
results_psd_method_welch_parameters = get_text_from_values_after_token(
                                     results_psd_method_welch_parameters,
                                     column="parameter_class",
                                     text_token="#",
                                     prefix="neao_params:",
                                     inplace=True)

# Aggregate table to get file counts for each parameter/value according to
# base path. Root file paths will be in columns.
results_psd_method_welch_parameters_root = extract_text_from_values(
                                     results_psd_method_welch_parameters,
                                     column='file_path',
                                     regex=PSD_BASE_PATH_RE)

aggregated_psd_method_welch_parameters = aggregate_table(
                                     results_psd_method_welch_parameters_root,
                                     rows=["parameter_class",
                                           "value"],
                                     columns="file_path")

# Format floats nicely, as they are expressed in exponential notation
# when serialized to RDF
aggregated_psd_method_welch_parameters[('value', '')] = \
    aggregated_psd_method_welch_parameters[('value', '')].apply(
        convert_exponential_notation)

# Sort table
aggregated_psd_method_welch_parameters = sort_table(
                               aggregated_psd_method_welch_parameters,
                               sort_function=sort_psd_method_welch_parameters,
                               inplace=True)

save_table_latex(aggregated_psd_method_welch_parameters,
                 "table_psd_results_C.txt",
                 columns={'file_path': "File count per root file path",
                          'parameter_class': "NEAO class",
                          'value': "Value"},
                 top_row="\\textbf{C}",
                 column_format="llcc",
                 multicolumn_line="3-4",
                 multicolumn=True,
                 multicolumn_format="c")
