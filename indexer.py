# -*- coding: utf-8 -*- 

import sys
import os
import csv
import pysolr
import requests
import urllib
import hashlib

reload(sys)
sys.setdefaultencoding("utf-8")

def check_if_archived_IA(url, endpoint="http://web.archive.org/web/xmlquery.jsp"):
    #r = requests.get( endpoint, params={ 'type': 'urlquery', 'url': url} )
    #r = requests.get( 'http://web.archive.org/web/*/%s' % url)
    #return r.status_code
    r = requests.get( "http://archive.org/wayback/available", params={ 'url': url} )
    print("IA %s" % r.text)
    if 'closest' in r.json()['archived_snapshots']:
        if r.json()['archived_snapshots']['closest'].get('available', False):
            return True
    return False
#http://www.webarchive.org.uk/wayback/archive/*/http://cadair.aber.ac.uk/dspace/bitstream/handle/2160/14050/Tomos_Y.pdf

def check_if_archived_UKWA(url, endpoint='http://www.webarchive.org.uk/wayback/archive/*/'):
    r = requests.head( '%s%s' % (endpoint,url) )
    if r.status_code == 200:
        return True
    else:
        return False

def check_if_archived_LDUKWA(url, endpoint='http://crawler03.bl.uk:8080/wayback/*/'):
    r = requests.head( '%s%s' % (endpoint,url) )
    if r.status_code == 200:
        return True
    else:
        return False

def download_file(url, local_filename):
    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
    r.close()
    return local_filename

def cache_url(url):
    hash = hashlib.md5(url).hexdigest()
    file = "tmp/%s" % hash
    if not os.path.exists(file):
        download_file(url, file)
    return file

def generate_txt(file):
    txtfile = '%s.txt' % file
    if not os.path.exists(txtfile) or os.path.getsize(txtfile) == 0:
        os.system("java -jar tika-app-1.13.jar -t %s > %s " % (file, txtfile))
    return txtfile

print( check_if_archived_LDUKWA('http://www.bl.uk') )
print( check_if_archived_LDUKWA('http://www.bl.uk.woolly') )

# Setup a Solr instance. The timeout is optional.
solr = pysolr.Solr('http://192.168.45.251:8983/solr/ethindex', timeout=10)

with open('EThOS-test.csv', 'rb') as csvfile:
    reader = csv.reader(csvfile)
    docs = []
    for row in reader:
        if row[7] and row[7] != 'IR URL':
            url = row[12]
            # Is the URL archived?
            archived_by = []
            if check_if_archived_IA(url):
                archived_by.append('IA')
            if check_if_archived_LDUKWA(url):
                archived_by.append('LDUKWA')
            if check_if_archived_UKWA(url):
                archived_by.append('OUKWA')
            # Parse the ID out of the EThOS URL
            # Build the doc:
            doc = {
                'id': row[13],
                'ir_url_s': row[7],
                'url_s': url,
                'ethos_url_s': row[13],
                'author_s': row[14],
                'title_s': row[15],
                'institution_s': row[16],
                'pub_year_i': row[17],
                'archived_by_ss': archived_by
            }
            # Download to tmp for processing:
            try:
                file = cache_url(url)
                txtfile = generate_txt(file)
                with open(txtfile, 'rb') as txtfo:
                    doc['pages_txt'] = txtfo.read()

                print(doc['id'])
                solr.add([doc])
                docs.append(doc)
            except Exception as e:
                print("Exception '%s' when processing '%s'" % (e,row))
    #solr.add(docs)
