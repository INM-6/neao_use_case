from manuscript_tables.utils import (
    load_results_csv, save_table_latex, extract_text_from_values,
    get_text_from_values_after_token, aggregate_table)
import re


INTERVALS = ((1, 100), (101, 200))


def split_file_names_by_range(data_frame, *intervals):
    # For the column with file names, generates a new column with a string
    # stating if the number in the file name belongs to a specific range
    # (e.g., ".../100.png" --> "1-100", ".../101.png" --> "101-200"). The
    # specific ranges are passed as tuples defining closed bound intervals.

    def get_range(value):
        re_match = re_pattern.match(value)
        if re_match:
            file_number = int(re_match.group(1))
            for key, interval in range_map_dictionary.items():
                if file_number in interval:
                    return key
        return ""

    range_map_dictionary = {f"{interval[0]}-{interval[1]}":
                            range(interval[0], interval[1] + 1)
                            for interval in intervals}
    re_pattern = re.compile(r"\.{3}\/isi_histograms\/(\d+)\.png$")

    data_frame['file_range'] = data_frame['file_path'].apply(get_range)
    return data_frame


###########
# TABLE A #
###########

# Load results of a query listing the data generation method for files
# that saved an ISIH derived from artificial data

raw_results_artificial_isih_method = \
    load_results_csv("artificial_isih_method_raw.csv")

# Clean long paths, adding ... as a replacer
results_artificial_isih_method = \
    get_text_from_values_after_token(raw_results_artificial_isih_method,
                                                      column="file_path",
                                                      text_token="outputs/analyses",
                                                      prefix="...")

# Replace base URI of the class with prefix
results_artificial_isih_method = get_text_from_values_after_token(results_artificial_isih_method,
                                                      column="neao_class",
                                                      text_token="#",
                                                      prefix="neao_steps:",
                                                      inplace=True)

# Extract the range each file name belongs to
results_artificial_isih_method = split_file_names_by_range(
    results_artificial_isih_method, *INTERVALS)

# Aggregate table to get file counts for each class according to file name
# range
aggregated_artificial_isih_method = aggregate_table(
                                            results_artificial_isih_method,
                                            rows="file_range",
                                            columns="neao_class")

save_table_latex(aggregated_artificial_isih_method,
                 "table_artificial_isih_results_A.txt",
                 columns={'file_range': "File name range",
                          'neao_class': "NEAO spike train generation class"},
                 top_row="\\textbf{A}",
                 multicolumn_line="2-3",
                 break_line_patterns=("(.+Generate)(.+)",),
                 column_format="lP{5cm}P{5cm}",
                 multicolumn=True,
                 multicolumn_format="c")


###########
# TABLE B #
###########

# Load results of query listing the parameter class and value for the
# data generation step of each file that have a ISIH result derived from
# artificial data
raw_results_artificial_isih_generation_parameters = load_results_csv(
    "artificial_isih_generation_parameters_raw.csv")

# Clean long paths, adding ... as a replacer
results_artificial_isih_generation_parameters = \
    get_text_from_values_after_token(raw_results_artificial_isih_generation_parameters,
                                     column="file_path",
                                     text_token="outputs/analyses",
                                     prefix="...")

# Replace base URI of the class with prefix
results_artificial_isih_generation_parameters  = \
    get_text_from_values_after_token(results_artificial_isih_generation_parameters,
                                     column="parameter_class",
                                     text_token="#",
                                     prefix="neao_params:",
                                     inplace=True)

# Extract the range each file name belongs to
results_artificial_isih_generation_parameters = split_file_names_by_range(
    results_artificial_isih_generation_parameters, *INTERVALS)

# Aggregate table to get file counts for each class according to file name
# range
aggregated_artificial_isih_generation_parameters = aggregate_table(
                                            results_artificial_isih_generation_parameters,
                                            rows=["parameter_class", "value"],
                                            columns="file_range")

save_table_latex(aggregated_artificial_isih_generation_parameters,
                 "table_artificial_isih_results_B.txt",
                 columns={'file_range': "File name range",
                          'parameter_class': "NEAO class",
                          'value': "Value"},
                 top_row="\\textbf{B}",
                 multicolumn_line="3-4",
                 column_format="llcc",
                 multicolumn=True,
                 multicolumn_format="c")


###########
# TABLE C #
###########

# Load results of query listing the bin size of interspike interval
# histograms computed from artificial data

raw_results_artificial_isih_bin_size = \
    load_results_csv("artificial_isih_bin_size_raw.csv")

# Clean long paths, adding ... as a replacer
results_artificial_isih_bin_size = \
    get_text_from_values_after_token(raw_results_artificial_isih_bin_size,
                                                      column="file_path",
                                                      text_token="outputs/analyses",
                                                      prefix="...")

# Extract the range each file name belongs to
results_artificial_isih_bin_size = split_file_names_by_range(
    results_artificial_isih_bin_size, *INTERVALS)

# Aggregate table to get file counts for each file name range
aggregated_artificial_isih_bin_size = aggregate_table(
                                        results_artificial_isih_bin_size,
                                        rows=["file_range", "bin_size"])

save_table_latex(aggregated_artificial_isih_bin_size,
                 "table_artificial_isih_results_C.txt",
                 columns={'file_range': "File name range",
                          'bin_size': "Bin size",
                          'values': "File count"},
                 top_row="\\textbf{C}",
                 column_format="lcr")


###########
# TABLE D #
###########

# Load results of query listing the method used to compute interspike interval
# variability from artificial data

raw_results_artificial_variability = \
    load_results_csv("artificial_isih_variability_raw.csv")

# Clean long paths, adding ... as a replacer
results_artificial_isih_variability = \
    get_text_from_values_after_token(raw_results_artificial_variability,
                                                      column="file_path",
                                                      text_token="outputs/analyses",
                                                      prefix="...")

# Replace base URI of the class with prefix
results_artificial_isih_variability = get_text_from_values_after_token(
                                                      results_artificial_isih_variability,
                                                      column="neao_class",
                                                      text_token="#",
                                                      prefix="neao_steps:",
                                                      inplace=True)

# Extract the range each file name belongs to
results_artificial_isih_variability = split_file_names_by_range(
    results_artificial_isih_variability, *INTERVALS)


# Aggregate table to get file counts per each file name range
aggregated_artificial_isih_variability = aggregate_table(
                                        results_artificial_isih_variability,
                                        rows="file_range",
                                        columns="neao_class")

save_table_latex(aggregated_artificial_isih_variability,
                 "table_artificial_isih_results_D.txt",
                 columns={'file_range': "File name range",
                          'neao_class': "NEAO spike interval variability analysis class"},
                 top_row="\\textbf{D}",
                 multicolumn_line="2",
                 multicolumn=True,
                 column_format="lc")
