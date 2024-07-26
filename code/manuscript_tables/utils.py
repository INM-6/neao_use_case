"""
This contains helper functions to load the SPARQL query results and perform
operations that are shared across all tables.
This also provides the paths for input and output files.
"""
import numpy as np
import pandas as pd
import re
from functools import reduce

from pathlib import Path

# Path to where the query results were stored as CSV files and where the
# manuscript tables will be saved as LaTeX code
OUTPUTS_FOLDER = Path(__file__).absolute().parents[2] / "outputs"
QUERY_RESULTS_FOLDER = OUTPUTS_FOLDER / "query_results"
TABLE_OUTPUTS_FOLDER = OUTPUTS_FOLDER / "manuscript_tables"

# Regular expressions
BASE_PATH_RE = r".+\/(isi_histograms|reach2grasp\/[a-z0-9_]+)(\/.+)*\/.+\.png$"
PSD_BASE_PATH_RE = r"([a-z0-9_\.\/]+)\/.+\.png$"
SURROGATE_ISIH_BASE_PATH_RE = r"([a-z0-9_\.\/]+)\/.+\.png$"
ARTIFICIAL_ISIH_BASE_PATH_RE = r".+\/(isi_histograms)\/.+png$"


# Decorator for inplace operations (to avoid modifying the original DataFrame)

def inplace(func):
    def wrapper(data_frame, **kwargs):
        inplace = kwargs.pop('inplace', False)
        if not inplace:
            data_frame = data_frame.copy()
        return func(data_frame, **kwargs)
    return wrapper


# File IO

def load_results_csv(results_file):
    """
    Loads a CSV file with results into a DataFrame.
    """
    return pd.read_csv(QUERY_RESULTS_FOLDER / results_file,
                       index_col=0)


def write_text_file(file_name, text):
    """
    Writes text to a file.
    """
    with open(TABLE_OUTPUTS_FOLDER / file_name, "wt") as output:
        output.write(text)


# Functions to get/modify LaTeX tables from a DataFrame, and save it to a file

def save_table_latex(data_frame, table_file, index=False, columns=None,
                     multicolumn_line=None, top_row=None, bold_header=True,
                     rows_begin=None, rows_end=None, break_line_patterns=None,
                     use_tabularx=False, mbox=None, **kwargs):
    """
    Saves a DataFrame as LaTeX table.

    Parameters
    ----------
    table_file : str
        Name of the file where the LaTeX table will be saved.
    index : bool
        If True, include the index of the DataFrame in the table.
    columns : dict
        Mapping of DataFrame column labels to labels that should be used in
        the LaTeX formatted table.
    multicolumn_line : str
        String range (e.g., "2-3") defining the columns where a horizontal
        line will be added between rows in the header.
    top_row : str
        Text added on top as an additional row.
    bold_header : bool
        If True, change text in the header cells to bold.
    rows_begin : int
        Number of rows to include at the beginning of the table.
    rows_end : int
        Number of rows to include at the end of the table. If None, the same
        number as `row_begin` is used.
    break_line_patterns : tuple of str
        Regex patterns that will be used to insert `\newline` commands in
        column labels, to break the label into several lines. The match groups
        in the pattern define the tokens separated by line breaks. A tuple
        with multiple patterns can be passed. In this case, only text that
        matches a specific pattern will be changed.
    use_tabularx : bool
        Use `tabularx` environment instead of `tabular`.
    mbox : list or tuple
        If defined, put the expressions inside an `mbox`, to avoid line
        breaks.

    Notes
    -----
    1. Any additional keyword argument will be forwarded to the
       `DataFrame.to_latex()` function, use to convert the DataFrame to LaTeX.

    2. When removing rows from the table output, a line will be inserted
       between the remaining rows stating how many rows were omitted.
    """
    # Change column labels if requested
    df = data_frame.copy()
    if columns is not None:
        df = set_labels(df, columns)

    # Convert to LaTeX
    latex_results = df.to_latex(index=index, escape=True, **kwargs)

    # Format LaTeX output as requested
    if multicolumn_line:
        latex_results = add_multicolumn_line(latex_results, multicolumn_line)
    if bold_header or break_line_patterns:
        latex_results = latex_format_header(latex_results,
                                            bold_header, break_line_patterns)
    if mbox:
        if not isinstance(mbox, (list, tuple)):
            mbox = [mbox]
        for expression in mbox:
            latex_results = add_mbox(latex_results, expression)

    if top_row:
        latex_results = add_top_row(latex_results, top_row)
    if rows_begin is not None:
        if rows_end is None:
            rows_end = rows_begin
        latex_results = remove_middle_rows(latex_results, rows_begin, rows_end)

    # Change to tabularx if needed
    if use_tabularx:
        latex_results = change_to_tabularx(latex_results)

    # Save file
    write_text_file(table_file, latex_results)


def add_multicolumn_line(latex_table, columns):
    """
    Adds a line with specified width between rows of a multicolumn.
    """
    table = []
    for line in latex_table.splitlines():
        if "\\multicolumn" in line:
            line = f"{line} \\cmidrule{{{columns}}}"
        table.append(line)
    return "\n".join(table)


def add_top_row(latex_table, title):
    """
    Adds a line above the table. It will span all the table columns.
    """
    start = []
    header = []
    rest = []

    cur_list = start
    for line in latex_table.splitlines():
        if line == "\\toprule":
            cur_list = header
        elif line == "\\midrule":
            cur_list = rest
        cur_list.append(line)

    n_columns = len(rest[1].split("&"))
    title_str = f"\\multicolumn{{{n_columns}}}{{l}}{{{title}}} \\\\"
    table = start + [title_str] + header + rest
    return "\n".join(table)


def latex_format_header(latex_table, bold_header=True,
                        break_line_patterns=None):

    def _change_labels_to_bold(cell_contents):
        if "\\multicolumn" in cell_contents:
            # Insert bold formatting into multicolumn
            match = re.match(
                r"(\\multicolumn\{\d+\}\{.{1}\}\{)(.+)(\})", cell_contents)
            return f" {match.group(1)}\\textbf{{{match.group(2)}}}{match.group(3)}"

        # Just convert cell contents to bold
        return f" \\textbf{{{cell_contents}}}"

    def _insert_line_breaks(cell_contents, patterns):
        for pattern in patterns:
            match = re.match(pattern, cell_contents)
            if match:
                return reduce(
                    lambda before, after: f"{before} \\newline {after}",
                    match.groups()
                )
        return cell_contents

    table = []
    in_header = False
    for line in latex_table.splitlines():
        if line == "\\midrule":
            in_header = False

        if in_header:
            # Line in the header. Process each column to perform the
            # requested modifications
            columns = []
            for column in line.split("&"):

                # Extract column cell contents
                if "\\\\" in column:
                    # End column. Get any extra commands after line break
                    # and extract the text from the cell
                    cell, ending = column.split("\\\\")
                    ending = ending.strip()
                    if len(ending) > 0:
                        ending = f"\\\\ {ending}"
                else:
                    cell = column
                    ending = ""

                contents = cell.strip()  # For blank cells

                # If cell is not blank, modify the contents
                if len(contents) > 0:
                    modified_cell = contents

                    if break_line_patterns:
                        modified_cell = _insert_line_breaks(
                            modified_cell, break_line_patterns)

                    if bold_header:
                        modified_cell = _change_labels_to_bold(modified_cell)

                    modified_cell = f"{modified_cell} {ending}"
                else:
                    modified_cell = " "  # Leave blank

                columns.append(modified_cell)  # Store modified column title

            # Create new line with all modified cells.
            # Add \\ to the end if needed
            line = "&".join(columns)
            if "\\\\" not in line:
                line = f"{line} \\\\"

        if line == "\\toprule":
            in_header = True

        table.append(line)

    return "\n".join(table)


def add_mbox(latex_table, expression):
    """
    Puts the text in `expression` into an `mbox` command".
    """
    expression = re.escape(expression)
    expression = f"({expression})"
    latex_table = re.sub(expression, r"\\mbox{\g<1>}", latex_table)
    return latex_table


def remove_middle_rows(latex_table, number_begin, number_end):
    """
    Removes lines from the middle of a LaTeX table, leaving `number_begin`
    and `number_end`. A line will be inserted between the remaining lines
    stating how many rows were omitted.
    """
    header = []
    footer = []
    rows = []

    cur_list = header
    for line in latex_table.splitlines():
        if line == "\\midrule":
            cur_list = rows
        elif line == "\\bottomrule":
            cur_list = footer
        cur_list.append(line)

    n_removed = len(rows) - number_begin - number_end - 1

    n_columns = len(rows[1].split("&"))
    empty_columns = "&" * (n_columns-1)

    blank_line = f" {empty_columns} \\\\"
    removed_row = f"\\textit{{(omitted {n_removed} lines)}} {empty_columns} \\\\"

    table = header + rows[:number_begin+1] + \
            [blank_line, removed_row, blank_line] + \
            rows[-number_end:] + footer

    return "\n".join(table)


def change_to_tabularx(latex_table, width="\\\\textwidth"):
    """
    Changes to the `tabularx` environment. The width is set according to the
    `width` parameter.
    """
    latex_table = re.sub(
        r"\\begin{tabular}", f"\\\\begin{{tabularx}}{{{width}}}", latex_table)
    latex_table = re.sub(
        r"\\end{tabular}", "\\\\end{tabularx}", latex_table)
    return latex_table

# Functions to modify a DataFrame with query results

@inplace
def remove_text_token_from_values(data_frame, *, column, text_token):
    """
    For a column with string values in a DataFrame, modify the values to
    remove a string `text_token`.
    """
    data_frame[column] = data_frame[column].str.replace(text_token, "")
    return data_frame


@inplace
def extract_text_from_values(data_frame, *, column, regex, group=0):
    """
    For a column with string values in a DataFrame, get only the part that
    matches a regular expression. The matching group may be specified.
    """
    data_frame[column] = data_frame[column].str.extract(
        regex, expand=True)[group]
    return data_frame


@inplace
def add_prefix_to_values(data_frame, *, column, prefix):
    """
    For a column with string values in a DataFrame, add a text prefix to
    the values.
    """
    data_frame[column] = prefix + data_frame[column]
    return data_frame


@inplace
def get_text_from_values_after_token(data_frame, *, column, text_token,
                                     prefix=None):
    """
    For a column with string values in a DataFrame, modify the values to keep
    only the part after a string `text_token`. A prefix may be added.
    """
    data_frame[column] = data_frame[column].str.split(text_token).str[-1]

    if prefix:
        data_frame = add_prefix_to_values(data_frame, column=column,
                                          prefix=prefix)

    return data_frame


def aggregate_table(data_frame, rows, columns=None, values=None,
                    aggfunc="sum", fill_value=0):
    """
    Aggregates a DataFrame to produce summaries of a DataFrame with query
    results.
    """
    if values is None:
        data_frame['values'] = 1
        values = "values"

    cross_tab = data_frame.pivot_table(columns=columns, index=rows,
                                       values=values, aggfunc=aggfunc,
                                       fill_value=fill_value)
    if len(cross_tab.columns) > 1:
        # Multiple values. Create MultiIndex to have a label
        level_0 = [cross_tab.columns.name for _ in cross_tab.columns]
        multi_index = [level_0, cross_tab.columns.values]
        cross_tab.columns = pd.MultiIndex.from_arrays(multi_index)

    return cross_tab.reset_index(drop=False)


def set_labels(data_frame, columns):
    """
    Changes the name of the columns in a DataFrame.
    """
    return data_frame.rename(columns=columns)


@inplace
def sort_table(data_frame, sort_function):
    """
    Uses a custom function to sort the rows in a DataFrame based on column
    values. `sort_function` takes a series corresponding to the row.
    """
    data_frame['sort'] = data_frame.apply(sort_function, axis=1)
    data_frame.sort_values(by=['sort'], inplace=True)
    data_frame.drop(columns='sort', inplace=True)
    return data_frame
