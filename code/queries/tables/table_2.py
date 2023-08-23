import numpy as np

def process_results(query_results):
    full_table = query_results.to_latex(index_names=False, escape=True)

    # Compute counts
    base_path = lambda x: x['output_file_path'].rsplit("/", 2)[0]
    query_results['base_path'] = query_results.apply(base_path, axis=1)
    query_results['count'] = 1
    cross_tab = query_results.pivot_table(columns='name', index='base_path',
                                          values='count', aggfunc=np.sum,
                                          fill_value=0)

    return full_table, cross_tab.to_latex(index_names=False, escape=True)
