
import csv
import pysolr


# Setup a Solr instance. The timeout is optional.
solr = pysolr.Solr('http://localhost:8983/solr/ethindex', timeout=10)

with open('EThOS-test.csv', 'rb') as csvfile:
    reader = csv.reader(csvfile)
    docs = []
    for row in reader:
        if row[7] and row[7] != 'IR URL':
          doc = {
            'ir_url_s': row[7],
            'url_s': row[12],
            'ethos_url_s': row[13],
            'author_s': row[14],
            'title_s': row[15],
            'institution_s': row[16],
            'pub_year_i': row[17]
          }
          docs.append(doc)
    solr.add(docs)
