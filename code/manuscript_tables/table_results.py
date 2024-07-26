from manuscript_tables.utils import (
    load_results_csv, save_table_latex, extract_text_from_values,
    get_text_from_values_after_token, aggregate_table, BASE_PATH_RE)


# Function to process each set of raw results and produce the tables
def process_query_results(*, raw_query_results_file,
                          supplement_table_file,
                          manuscript_table_file,
                          manuscript_table_label):

    # Load results of query listing which files contain the requested
    # analysis results
    raw_results = load_results_csv(raw_query_results_file)

    # Clean long paths, adding ... as a replacer
    results = get_text_from_values_after_token(raw_results,
                                               column="file_path",
                                               text_token="outputs/analyses",
                                               prefix="...")

    # Save table to LaTeX, with the first/last 15 rows (supplement)
    save_table_latex(results,
                     supplement_table_file,
                     rows_begin=15,
                     rows_end=15,
                     columns={'file_path': "File path"},
                     use_tabularx=True)

    # Aggregate table to get file counts according to base path
    results_root = extract_text_from_values(raw_results,
                                            column='file_path',
                                            regex=BASE_PATH_RE)

    aggregated_results_root = aggregate_table(results_root,
                                              rows="file_path")

    # Save aggregated table to use in the manuscript
    save_table_latex(aggregated_results_root,
                     manuscript_table_file,
                     columns={'file_path': "Root file path",
                              'values': "File count"},
                     top_row=manuscript_table_label)


###########
# TABLE A #
###########

process_query_results(raw_query_results_file="steps_psd_raw.csv",
                      supplement_table_file="supplement_table_psd_results.txt",
                      manuscript_table_file="table_results_A.txt",
                      manuscript_table_label="\\textbf{A}")


###########
# TABLE B #
###########

process_query_results(raw_query_results_file="steps_isih_raw.csv",
                      supplement_table_file="supplement_table_isih_results.txt",
                      manuscript_table_file="table_results_B.txt",
                      manuscript_table_label="\\textbf{B}")


###########
# TABLE C #
###########

process_query_results(raw_query_results_file="steps_artificial_raw.csv",
                      supplement_table_file="supplement_table_artificial_results.txt",
                      manuscript_table_file="table_results_C.txt",
                      manuscript_table_label="\\textbf{C}")
