import os
from pymilvus import MilvusClient, DataType

def get_milvus_client():
    uri = os.getenv('MILVUS_URI', 'http://127.0.0.1:19530')
    client = MilvusClient(uri=uri)
    
    collection_name = os.getenv('MILVUS_COLLECTION_NAME', 'document_chunks')

    if not client.has_collection(collection_name):
        schema = MilvusClient.create_schema(auto_id=False, enable_dynamic_field=False)
        schema.add_field(field_name="chunk_id", datatype=DataType.VARCHAR, is_primary=True, max_length=36)
        schema.add_field(field_name="document_id", datatype=DataType.VARCHAR, max_length=36)
        schema.add_field(field_name="embedding", datatype=DataType.FLOAT_VECTOR, dim=384)

        index_params = client.prepare_index_params()
        index_params.add_index(field_name="embedding", index_type="IVF_FLAT", metric_type="COSINE", params={"nlist": 128})

        client.create_collection(
            collection_name=collection_name,
            schema=schema,
            index_params=index_params
        )
        
    return client, collection_name