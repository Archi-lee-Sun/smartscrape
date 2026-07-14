from sentence_transformers import SentenceTransformer, util
from ..models import RawItem
from .dsu import DSU

model = SentenceTransformer("all-MiniLM-L6-v2")

def build_similarity_matrix(items: list[RawItem]):
    texts = [item.title + "\n" + item.content[:200] for item in items]
    embeddings = model.encode(texts, convert_to_tensor=True)
    similarity_matrix = util.cos_sim(embeddings, embeddings)

    return similarity_matrix

def group_duplicates(items: list[RawItem], threshold: float = 0.75) -> list[list[RawItem]]:
    n = len(items)
    matrix = build_similarity_matrix(items)
    dsu = DSU(n)

    for i in range(n):
        for j in range(i + 1, n):
            if matrix[i][j] > threshold:
                dsu.union(i, j)

    groups: dict[int, list[RawItem]] = {}
    for i in range(n):
        root = dsu.find(i)
        groups.setdefault(root, []).append(items[i])

    return list(groups.values())

def select_representative_items(groups: list[list[RawItem]]) -> list[RawItem] :
    representative_items = []
    for group in groups :
        pick = group[0]
        for item in group :
            if item.published_at > pick.published_at :
                pick = item
        representative_items.append(pick)
    
    return representative_items