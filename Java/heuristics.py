import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def rank_methods_by_similarity(test_code_csv: str, method_csv: str) -> pd.DataFrame:
    """
    Ranks executed methods based on cosine similarity to the test method code.
    
    Args:
        test_code_csv (str): Path to CSV file with test method code (expects column "test_code").
        method_csv (str): Path to CSV file with executed methods (expects column "Body").

    Returns:
        pd.DataFrame: DataFrame of executed methods ranked by similarity score, descending.
    """
    # Load data
    test_df = pd.read_csv(test_code_csv)
    method_df = pd.read_csv(method_csv)

    # Ensure 'test_code' and 'Body' exist
    if 'test_code' not in test_df.columns:
        raise ValueError("test_code.csv must contain 'test_code' column")
    if 'Body' not in method_df.columns:
        raise ValueError("method-under-test.csv must contain 'Body' column")

    test_code = test_df.iloc[0]['test_code']
    method_bodies = method_df['Body'].tolist()

    # Compute TF-IDF vectors
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([test_code] + method_bodies)

    # Compute cosine similarity of each method to test_code
    similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

    # Attach scores to DataFrame and sort
    method_df['similarity'] = similarities
    method_df = method_df.sort_values(by='similarity', ascending=False).reset_index(drop=True)
    #print(method_df)

    return method_df

