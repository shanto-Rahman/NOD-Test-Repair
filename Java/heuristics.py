import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoConfig, AutoModel
import torch


def codebert_model_define():    
    model_name = "microsoft/codebert-base"
    model_config = AutoConfig.from_pretrained(model_name, return_dict=False, output_hidden_states=True)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    auto_model = AutoModel.from_pretrained(model_name, config=model_config) 
    return model_name, tokenizer, auto_model

def get_code_embeddings(code, tokenizer, model, device):
    """Get better code embeddings using attention-weighted pooling"""
    inputs = tokenizer(code, 
                      padding=True,
                      truncation=True,
                      max_length=512,
                      return_tensors="pt").to(device)
    
    with torch.no_grad():
        outputs = model(**inputs)
        # Get last hidden states [batch_size, seq_length, hidden_size]
        hidden_states = outputs[0]
        
        # Use mean pooling instead of attention weights
        # Take mean of token embeddings along sequence length dimension
        mean_embeddings = torch.mean(hidden_states, dim=1)
        
    return mean_embeddings.cpu().numpy()

def rank_methods_by_llm_embedding_similarity(test_df, method_df, llm="codebert") -> pd.DataFrame:
    # Load BERT model (using Microsoft's CodeBERT variant)
    if llm == "codebert":
        model_name, tokenizer, model = codebert_model_define()
    else:
        model_name, tokenizer, model = codebert_model_define()  # Default to CodeBERT if no other model specified 
    
    # Generate embeddings
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)
    model.eval()
    
    # Get code snippets
    test_code = test_df.iloc[0]['test_code']
    method_bodies = method_df['Body'].tolist()
    
    # Generate embeddings
    test_embedding = get_code_embeddings(test_code, tokenizer, model, device)
    #print("test_embedding", len(test_embedding), test_embedding.shape)
    method_embeddings = [get_code_embeddings(body, tokenizer, model, device) for body in method_bodies]
    #print("method_embeddings", len(method_embeddings), method_embeddings[0].shape)
    # Compute cosine similarity
    similarities = [cosine_similarity(test_embedding, method_embedding).item() for method_embedding in method_embeddings]
    #print("similarities", len(similarities), similarities[:5])
    # Add similarity scores to DataFrame
    method_df['similarity'] = similarities
    # Sort by similarity
    method_df = method_df.sort_values(by='similarity', ascending=False).reset_index(drop=True)
    #print("method_df", method_df.shape, method_df.head())
    return method_df

def rank_methods_by_similarity(test_df, method_df) -> pd.DataFrame:
    """
    Ranks executed methods based on cosine similarity to the test method code.
    
    Args:
        test_code_csv (str): Path to CSV file with test method code (expects column "test_code").
        method_csv (str): Path to CSV file with executed methods (expects column "Body").

    Returns:
        pd.DataFrame: DataFrame of executed methods ranked by similarity score, descending.
    """
    # Load data
    #test_df = pd.read_csv(test_code_csv)
    #method_df = pd.read_csv(method_csv)

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

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

def clustering_methods(method_df, n_clusters: int = 5) -> pd.DataFrame: 
    # Read method CSV
    #method_df = pd.read_csv(method_csv)
    
    # Extract method bodies
    method_bodies = method_df["Body"].fillna("")
    
    # Convert method bodies to TF-IDF features
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(method_bodies)
    
    # Perform clustering (e.g., into 5 clusters)
    n_clusters = 5
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    clusters = kmeans.fit_predict(X)
    
    # Add cluster label to dataframe
    method_df["Cluster"] = clusters
    #print(method_df)
    return method_df

