from django import template
from db.models import FeatureDbxref, FeatureSynonym
from search.elastic_model import Elastic, ElasticQuery, BoolQuery, Query,\
    RangeQuery
from search.elastic_settings import ElasticSettings

register = template.Library()


@register.inclusion_tag('gene/gene_section.html')
def show_gene_section(gene_feature):
    ''' Template inclusion tag to render a gene section given a
    chado gene feature. '''

    feature_dbxrefs = FeatureDbxref.objects.filter(feature=gene_feature)
    gene_dbxrefs = []
    for feature_dbxref in feature_dbxrefs:
        gene_dbxrefs.append(feature_dbxref.dbxref)

    feature_synonyms = FeatureSynonym.objects.filter(feature=gene_feature)
    gene_synonyms = []
    for feature_synonym in feature_synonyms:
        gene_synonyms.append(feature_synonym.synonym)

    return {'feature': gene_feature,
            'synonyms': gene_synonyms,
            'dbxrefs': gene_dbxrefs}


@register.inclusion_tag('gene/es_gene_section.html')
def show_es_gene_section(gene_symbol=None, seqid=None,
                         start_pos=None, end_pos=None):
    ''' Template inclusion tag to render a gene section given a
    chado gene feature. '''
    if seqid is not None and isinstance(seqid, str) and seqid.startswith("chr"):
        seqid = seqid
    else:
        seqid = 'chr'+str(seqid)
    if gene_symbol is not None:
        ''' gene symbol query'''
        query = ElasticQuery.query_match("gene_symbol", gene_symbol)
    elif end_pos is None:
        ''' start and end are same, range query for snp'''
        query_bool = BoolQuery(must_arr=[Query.match("seqid", seqid),
                                         RangeQuery("featureloc.start", lte=start_pos),
                                         RangeQuery("featureloc.end", gte=start_pos)])
        query = ElasticQuery.bool(query_bool)
    else:
        ''' start and end are same, range query for snp'''
        query_bool = BoolQuery(must_arr=[Query.match("seqid", seqid),
                                         RangeQuery("featureloc.start", gte=start_pos),
                                         RangeQuery("featureloc.end", lte=end_pos)])
        query = ElasticQuery.bool(query_bool)

    elastic = Elastic(query, db=ElasticSettings.idx(name='GENE'))
    return {'es_genes': elastic.get_result()["data"]}
