from FlagEmbedding import BGEM3FlagModel
import numpy as np
import time
model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)

def get_embeddings(sentence, asFloat16=True):
    embeddings = model.encode(sentence, return_dense=True, return_sparse=True, return_colbert_vecs=True)
    if asFloat16:
        embeddings['dense_vecs'] = [float(embed) for embed in embeddings['dense_vecs']]
    return embeddings

def get_dense_embeddings(sentence, asFloat16=True) -> list[float]: # This is the only function currently in use
    embeddings: list[float] = list(model.encode(sentence, return_dense=True, return_sparse=False, return_colbert_vecs=False)['dense_vecs'])
    if not asFloat16:
        embeddings = [float(embed) for embed in embeddings]
    return embeddings

# once I get to seriously comparing embeddings, I will likely need to see about using more than just two sentences at a time
def get_simple_similarity(embeddings, embeddings_2, asFloat16=True):
    colbert_similarity_mat = embeddings['colbert_vecs'] @ embeddings_2['colbert_vecs'].T
    dense_similarity_mat = embeddings['dense_vecs'] @ embeddings_2['dense_vecs'].T
    colbert_similarity = colbert_similarity_mat.mean()
    dense_similarity = dense_similarity_mat.mean()
    if not asFloat16:
        dense_similarity = [float(embed) for embed in dense_similarity]

    return {"colbert": colbert_similarity, "dense": dense_similarity}

def get_full_similarity(embeddings, embeddings_2):
    colbert_similarity_mat = embeddings['colbert_vecs'] @ embeddings_2['colbert_vecs'].T
    dense_similarity_mat = embeddings['dense_vecs'] @ embeddings_2['dense_vecs'].T
    similarity_dict = {"colbert": colbert_similarity_mat, "dense": dense_similarity_mat}
    return similarity_dict

def get_simple_dense_similarity(embeddings: list, embeddings_2: list, asFloat16: bool = True):
    if not asFloat16:
        embeddings = [np.float16(embed) for embed in embeddings]
        embeddings_2 = [np.float16(embed) for embed in embeddings_2]

    _embeddings = np.array(embeddings)
    _embeddings_2 = np.array(embeddings_2)

    dense_similarity_mat = _embeddings @ _embeddings_2.T
    dense_similarity = dense_similarity_mat.mean()
    
    if asFloat16:
        return dense_similarity
    else:
        return [float(embed) for embed in dense_similarity]
