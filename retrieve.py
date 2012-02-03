import urllib2

try:
    xmlfile=urllib2.urlopen('http://export.arxiv.org/oai2?verb=ListRecords&set=physics:quant-ph&from=2012-02-01&until=2012-02-03&metadataPrefix=arXivRaw')
except urllib2.HTTPError, e:
    # don't do anything at the moment, but wait until articles are loaded again
    # in particular, do not add a DownloadAction event 
    if e.code == 503:
        print('we have to wait')
    else:
        raise
    
print('hello world')