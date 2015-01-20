from django.core.management.base import BaseCommand
from optparse import make_option
import gzip, re
import json, requests
import logging
from db.management.loaders.VCF import VCFManager
from pip.locations import src_prefix



# Get an instance of a logger
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Use to create an elasticsearch index and add data \n" \
      "python manage.py index_search --snp --build dbSNP142\n" \
      "python manage.py index_search --loadSNP --build dbSNP142 All.vcf.gz"
    
    option_list = BaseCommand.option_list + (
        make_option('--snp',
            dest='snp',
            action="store_true",
            help='Create SNP index mapping'),
        ) + (
        make_option('--loadSNP',
            dest='loadSNP',
            help='Load SNP data'),
        ) + (
        make_option('--build',
            dest='build',
            help='Build number'),
        )

    def _create_snp_index(self, **options):
        
        if options['build']:
            build = options['build'].lower()
        else:
            build = "snp"
            
        data = {
                "mappings": {
                        build: {
                                "properties": {
                                            "ID": { "type": "string", "boost": 4 },
                                            "SRC": { "type": "string" },
                                            "REF": { "type": "string", "index" : "no" },
                                            "ALT": { "type": "string", "index" : "no" },
                                            "POS": { "type": "integer", "index" : "not_analyzed" },
                                        }
                                }
                        }
                }
        response = requests.put('http://127.0.0.1:9200/'+build+'/', data=json.dumps(data))
        print (response.text)
        return

    def _create_load_snp_index(self, **options):
        if options['build']:
            build = options['build'].lower()
        else:
            build = "snp"
            
        if options['loadSNP'].endswith('.gz'):
            f = gzip.open(options['loadSNP'], 'rb')
        else:
            f = open(options['loadSNP'], 'rb')

        data = ''
        n = 0
        nn = 0
        lastSrc = ''

        try:
            for line in f:
                line = line.decode("utf-8")
                parts = re.split('\t', line)
                if(len(parts) != 8 or line.startswith("#")):
                    continue

                src = parts[0]
                pos = int(parts[1])
                id  = parts[2]
                ref = parts[3]
                alt = parts[4]
                
                data += '{"index": {"_id": "%s"}}\n' % nn
                data += json.dumps({
                        "ID": parts[2],
                        "SRC": parts[0],
                        "REF": parts[3],
                        "ALT": parts[4],
                        "POS": int(parts[1])
                        })+'\n'

                n += 1
                nn += 1
                if( n > 5000 ):
                    n = 0
                    
                    if(lastSrc != src):
                        print ('\nLoading '+src)
                    print('.',end="",flush=True)
                    response = requests.put('http://127.0.0.1:9200/'+build+'/snp/_bulk', data=data)
                    #print (response.text)
                    data = ''
                    lastSrc = src
                    
#                 if( nn > 30000):
#                     return

        finally:
            response = requests.put('http://127.0.0.1:9200/'+build+'/snp/_bulk', data=data)

        return

    def handle(self, *args, **options):
        if options['snp']:
          self._create_snp_index(**options)
        elif options['loadSNP']:
          self._create_load_snp_index(**options)
        else:
          print(help)