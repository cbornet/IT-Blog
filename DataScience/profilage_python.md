# Profiling in python: Presentation of a few useful tools

_Bruno Goutorbe, Chief Data Scientist at Cdiscount_<br>
_Julien Jouganous, Data Scientist at Cdiscount_

Sometimes, computational performances become a crucial point in production algorithms.
That's especially true in data science where proof of concept pieces of code can have a poor scalability in terms of computation time as well as resource (CPU, memory) use.
There are multiple ways to overcome this type of issues, but before pulling out the heavy artillery (parallel computing, cython...), one may want to make sure his code has been written efficiently.
Optimizing code in python is not always trivial and can be a bit counterintuitive. Hopefully, several profiling tools are here to make python devs and data scientists lives easier!
This presentation (in french) gives a quick overview of the profiling tools we use in the data science team.

[![link to the slides](../images/DataScience/profilage_python.png)](https://www.slideshare.net/slideshow/embed_code/key/4iZepiEL7QPNf3)

The script used to illustrate the slides is provided below.

See you soon!

`similar_products.py`:

```python
"""
This script simulates a dataframe of products (and associated prices)
and a matrix of similarity, and creates from them an output file
which associates with each product a list of similar products.
Similar products must be more expensive, and sorted by decreasing
similarity.
"""

import numpy as np
from scipy import sparse
import pandas as pd
import datetime as dt

# parameters
NPRODUCTS = 100
MAX_SIMPRODUCTS = 5
OUTFILE = 'similar_products.csv'


# utility functions
def get_simproducts(indice_masterproduct, dfproducts, sim_matrix):
    """
    returns dataframe of products similar to product nb <indice_masterproduct>
    """
    # indices and similarity scores of products similar to master product
    start = sim_matrix.indptr[indice_masterproduct]
    stop = sim_matrix.indptr[indice_masterproduct + 1]
    indices_simproducts = sim_matrix.indices[start:stop]
    similarities = sim_matrix.data[start:stop]

    # extracting dataframe of similar products and appending column of similarity
    dfsimproducts = dfproducts.iloc[indices_simproducts]
    dfsimproducts['sim'] = similarities

    return dfsimproducts


def filter_and_sort_simproducts(dfsimproducts, min_price=None):
    """
    removes similar products with too low price and
    sorts them by decreasing similarity
    """
    if min_price:
        dfsimproducts = dfsimproducts[dfsimproducts['price'] >= min_price]
    dfsimproducts.sort_values('sim', ascending=False, inplace=True)
    return dfsimproducts


# starting script
t0 = dt.datetime.now()

# simulated dataframe of products
product_ids = ['product_{}'.format(i) for i in np.arange(NPRODUCTS)]
product_prices = np.random.uniform(low=1.0, high=1000.0, size=NPRODUCTS)
dfproducts = pd.DataFrame(columns=['product_id', 'price'],
                          data=np.column_stack((product_ids, product_prices)))

# simulated (sparse) matrix of similarity:
# sim_matrix[i, j] = similarity between products i-j
sim_matrix = sparse.random(NPRODUCTS, NPRODUCTS, density=1E-2, format='csr')

# preparing output file
f = open(OUTFILE, mode='w')
f.write("product_id\tsimproduct_ids\n")

# loop on lines of similarity matrix:
for iproduct in range(NPRODUCTS):
    # master product = product nb <iproduct>
    master_product = dfproducts.iloc[iproduct]

    dfsimproducts = get_simproducts(indice_masterproduct=iproduct,
                                    dfproducts=dfproducts,
                                    sim_matrix=sim_matrix)

    dfsimproducts = filter_and_sort_simproducts(dfsimproducts=dfsimproducts,
                                                min_price=master_product['price'])

    # exporting results to file
    simproduct_ids = dfsimproducts['product_id'][:MAX_SIMPRODUCTS]
    f.write("{}\t{}\n".format(master_product['product_id'], ','.join(simproduct_ids)))

f.close()
print("Process executed in {}s".format(dt.datetime.now() - t0))
```