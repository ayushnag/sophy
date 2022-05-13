import pyworms
import pandas
from timeit import default_timer as timer


# in: string species name
# out: dictionary w/ WoRMS classification
def get_taxa(species_name):
    result = pyworms.aphiaRecordsByMatchNames(species_name)[0]
    if len(result) > 0:
        return result
    else:
        return "no result found"


# Read columns from CSV file
print("Start read")
data = pandas.read_csv('data_bite_read.csv', encoding='unicode_escape')[['scientificname']]
print("End read \n")

print("Start WoRMS search")
start = timer()
taxa = set()
for x in range(20):
    species = data.loc[x][0]  # accesses xth row in column 0
    if species not in taxa:
        taxa.add(species)
        print(species + ":", end=" ")
        print(get_taxa(species))
end = timer()  # should improve over time as set gets larger and WoRMS does not need to be called
print(f"End WoRMS search {end - start} seconds")
