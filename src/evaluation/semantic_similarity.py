from sentence_transformers import SentenceTransformer, util
import torch

class SemanticSimilarity:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)

    def calculate_cosine_similarity(self, text1: str, text2: str) -> float:
        """
        Calculates cosine similarity between two text strings using vector embeddings.
        """
        embeddings1 = self.model.encode(text1, convert_to_tensor=True)
        embeddings2 = self.model.encode(text2, convert_to_tensor=True)
        
        cosine_score = util.cos_sim(embeddings1, embeddings2)
        return cosine_score.item()

    def verify_destination_intent(self, intent_description: str, page_content: str, threshold: float = 0.70) -> bool:
        """
        Flags a High-Risk Routing Failure if Cosine Similarity falls below threshold.
        """
        similarity = self.calculate_cosine_similarity(intent_description, page_content)
        return similarity >= threshold, similarity
