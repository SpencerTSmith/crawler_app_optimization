import logging
from flask import current_app


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


logger = logging.getLogger(__name__)

def add_to_index(index, model):
    logger.info(f'Adding model {model} to index {index}.')
    if not current_app.elasticsearch:
        logger.warning('Elasticsearch not available. Cannot add to index.')
        return
    payload = {}
    for field in model.__searchable__:
        payload[field] = getattr(model, field)
    current_app.elasticsearch.index(index=index, id=model.id, document=payload)
    logger.info(f'Model {model} indexed successfully.')

def remove_from_index(index, model):
    logger.info(f'Removing model {model} from index {index}.')
    if not current_app.elasticsearch:
        logger.warning('Elasticsearch not available. Cannot remove from index.')
        return
    try:
        current_app.elasticsearch.delete(index=index, id=model.id)
        logger.info(f'Model {model} removed from index successfully.')
    except Exception as e:
        logger.error(f'Error removing model {model} from index: {e}')

def query_index(index, query, page, per_page):
    logger.info(f'Querying index {index} with query "{query}" on page {page}.')
    if not current_app.elasticsearch:
        logger.warning('Elasticsearch not available. Cannot perform query.')
        return [], 0
    search = current_app.elasticsearch.search(
        index=index,
        query={'multi_match': {'query': query, 'fields': ['*']}},
        from_=(page - 1) * per_page,
        size=per_page
    )
    ids = [int(hit['_id']) for hit in search['hits']['hits']]
    logger.info(f'Found {len(ids)} results for query "{query}".')
    return ids, search['hits']['total']['value']
