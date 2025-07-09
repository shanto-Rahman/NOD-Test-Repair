import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoConfig, AutoModel
import torch
from transformers import BigBirdTokenizer, BigBirdForSequenceClassification
from transformers import BigBirdModel
from transformers import T5Tokenizer, T5EncoderModel
from transformers import LlamaTokenizer, LlamaModel

def qwen_model_define():
    model_name = "Qwen/Qwen-7B"
    tokenizer  = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True,
        use_fast=False,
        use_auth_token=True
    )
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        trust_remote_code=True,
        use_auth_token=True
    )
    return model_name, tokenizer, model

import torch
import numpy as np

def get_qwen_embeddings(code: str,
                        tokenizer,
                        model,
                        device: torch.device) -> np.ndarray:
    """
    1. Tokenizes the code (no padding).
    2. Runs the Qwen model with `output_hidden_states=True`.
    3. Mean‐pools the final hidden layer weighted by the attention mask.
    4. Casts to float32 and returns a NumPy array of shape (1, hidden_size).
    """
    # 1) Tokenize with truncation only
    inputs = tokenizer(
        code,
        return_tensors="pt",
        truncation=True,
        max_length=tokenizer.model_max_length,
        return_attention_mask=True
    ).to(device)

    # 2) Forward pass, request hidden states
    with torch.no_grad():
        outputs = model(**inputs, output_hidden_states=True)
        # Grab the last hidden layer: (1, seq_len, hidden_size)
        last_hidden = outputs.hidden_states[-1]

    # 3) Compute attention‐mask‐weighted mean over seq_len
    mask = inputs.attention_mask.unsqueeze(-1)  # (1, seq_len, 1)
    summed = (last_hidden * mask).sum(dim=1)    # (1, hidden_size)
    counts = mask.sum(dim=1)                    # (1, 1)
    emb    = summed / counts                    # (1, hidden_size)

    # 4) Cast to float32 (avoid bfloat16→NumPy errors) and return
    return emb.cpu().to(torch.float32).numpy()  # → array shape (1, hidden_size)

def llama3_model_define():
    #model_name = "meta-llama/Llama-3-8b-hf"  # or the exact HF repo ID you have
    model_name = "meta-llama/Meta-Llama-3-8B"

    # 1) load the tokenizer (slow) and model
    #tokenizer = LlamaTokenizer.from_pretrained(model_name, use_fast=False)
    #model     = LlamaModel.from_pretrained(model_name)
    # We use trust_remote_code to load Meta’s custom code if needed:
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True,
        use_fast=False,       # force the SentencePiece (slow) tokenizer
        use_auth_token=True   # if it’s gated, ensure you’ve run `huggingface-cli login`
    )
    # Llama doesn’t define a pad token, so we’ll skip padding and use mask-pooling
    model = AutoModel.from_pretrained(
        model_name,
        trust_remote_code=True,
        use_auth_token=True
    )

    return model_name, tokenizer, model

def get_llama3_embeddings(code: str,
                          tokenizer: LlamaTokenizer,
                          model: LlamaModel,
                          device: torch.device) -> np.ndarray:
    """
    1) Tokenize with truncation only (no pad token needed).
    2) Forward through the encoder to get last_hidden_state.
    3) Attention‐mask–weighted mean‐pool to get [1, hidden_size].
    4) Cast to float32 and return a NumPy array of shape (1, hidden_size).
    """
    # 1) Tokenize (up to model’s context window; typically 4096 for Llama-3)
    max_len = tokenizer.model_max_length
    # clamp to a sane maximum (e.g. 4096 tokens)
    if max_len > 8192:
        max_len = 8192

    inputs = tokenizer(
        code,
        return_tensors="pt",
        truncation=True,
        max_length=max_len,
        return_attention_mask=True
    ).to(device)

    # 2) Forward pass (encoder only)
    with torch.no_grad():
        outputs = model(**inputs)
        # last_hidden_state: [1, seq_len, hidden_size]
        hidden_states = outputs.last_hidden_state

    # 3) Mask‐weighted mean‐pool
    mask        = inputs.attention_mask.unsqueeze(-1)   # [1, seq_len, 1]
    summed      = (hidden_states * mask).sum(dim=1)     # [1, hidden_size]
    lengths     = mask.sum(dim=1)                       # [1, 1]
    emb         = summed / lengths                      # [1, hidden_size]

    # 4) to float32 and numpy
    return emb.cpu().to(torch.float32).numpy() 

def llama_model_define():
    model_name = "meta-llama/Llama-2-7b-hf"
    # Load the tokenizer & model
    tokenizer = LlamaTokenizer.from_pretrained(model_name, use_fast=False)
    # Llama doesn’t define a pad token by default—set it to eos
    tokenizer.pad_token = tokenizer.eos_token
    model = LlamaModel.from_pretrained(model_name)
    # Tell the model which ID is pad
    model.config.pad_token_id = tokenizer.eos_token_id
    return model_name, tokenizer, model

def get_llama_embeddings(code: str,
                         tokenizer: LlamaTokenizer,
                         model: LlamaModel,
                         device: torch.device) -> np.ndarray:
    """
    Tokenize up to the model's context length (default 4096 for Llama-2),
    run the encoder, then mean-pool over tokens to get a [1, hidden_size] vector.
    """
    inputs = tokenizer(
        code,
        return_tensors="pt",
        truncation=True,
        padding="longest",
        max_length=4096   # adjust if you use a smaller Llama variant
    ).to(device)

    with torch.no_grad():
        outputs = model(**inputs)
        # last_hidden_state: [1, seq_len, hidden_size]
        hidden_states = outputs.last_hidden_state

    # mean-pool → [1, hidden_size]
    emb = hidden_states.mean(dim=1)

    # return a 2D numpy array so cosine_similarity still works
    return emb.cpu().numpy()


def gpt2_model_define():
    model_name = "gpt2-medium"
    tokenizer  = AutoTokenizer.from_pretrained(model_name, use_fast=False)
    # tell GPT-2 to pad with its EOS token
    tokenizer.pad_token = tokenizer.eos_token
    model      = AutoModel.from_pretrained(model_name)
    # also set the model’s padding‐token‐id so it won’t warn you
    model.config.pad_token_id = model.config.eos_token_id
    return model_name, tokenizer, model

def bigbird_model_define():
    model_name = "google/bigbird-roberta-base"  # 4096-token variant
    tokenizer = BigBirdTokenizer.from_pretrained(model_name)
    auto_model = BigBirdModel.from_pretrained(model_name)
    return model_name, tokenizer, auto_model

def codet5_model_define():
    model_name = "Salesforce/codet5-large"
    # Use AutoTokenizer and force the slow (sentencepiece) version
    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False)
    model     = T5EncoderModel.from_pretrained(model_name)
    return model_name, tokenizer, model
#def codet5_model_define():
#    model_name = "Salesforce/codet5-large"
#    tokenizer  = T5Tokenizer.from_pretrained(model_name)
#    model      = T5EncoderModel.from_pretrained(model_name)
#    return model_name, tokenizer, model

def codebert_model_define():    
    model_name = "microsoft/codebert-base"
    model_config = AutoConfig.from_pretrained(model_name, return_dict=False, output_hidden_states=True)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    auto_model = AutoModel.from_pretrained(model_name, config=model_config) 
    return model_name, tokenizer, auto_model

def get_gpt2_embeddings(code: str,
                        tokenizer,
                        model,
                        device: torch.device) -> np.ndarray:
    """
    Encode up to 1024 tokens with GPT2-Medium and mean-pool to get a 1024-dim vector.
    """
    inputs = tokenizer(
        code,
        return_tensors="pt",
        truncation=True,
        padding="longest",
        max_length=1024    # now matches GPT-2’s context window
    ).to(device)

    with torch.no_grad():
        outputs = model(**inputs)
        # outputs.last_hidden_state: [1, seq_len, hidden_size=1024]
        hidden_states = outputs.last_hidden_state

    # mean-pool across the sequence → [1, 1024]
    emb = hidden_states.mean(dim=1)
    return emb.cpu().numpy()  # → (1024,)

def get_bigbird_embeddings(code: str, tokenizer, model, device):
    # Tokenize up to 4096 tokens
    inputs = tokenizer(
        code,
        return_tensors="pt",
        truncation=True,
        padding="max_length",
        max_length=1024
    ).to(device)
    
    with torch.no_grad():
        outputs = model(**inputs)
        # last_hidden_state: [batch, seq_len, hidden_size]
        hidden_states = outputs.last_hidden_state

    # Mean-pool across the sequence dimension
    emb = hidden_states.mean(dim=1)  # → [batch, hidden_size]
    return emb.cpu().numpy()


def get_codebert_embeddings(code, tokenizer, model, device):
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
        mean_embeddings = torch.mean(hidden_states, dim=1)
        
    return mean_embeddings.cpu().numpy()

import torch

def get_codet5_embeddings(code: str,
                          tokenizer,
                          model,
                          device: torch.device) -> np.ndarray:
    """
    Get code embeddings from CodeT5-Large by mean-pooling its encoder outputs.

    Args:
      code: the code snippet to embed
      tokenizer: a T5Tokenizer from 'Salesforce/codet5-large'
      model: a T5EncoderModel from 'Salesforce/codet5-large'
      device: torch.device ('cuda' or 'cpu')

    Returns:
      A NumPy array of shape (hidden_size,)—for CodeT5-Large that is (1024,).
    """
    # 1) Tokenize & move inputs to device
    inputs = tokenizer(
        code,
        return_tensors="pt",
        truncation=True,
        padding="longest",
        max_length=512
    ).to(device)

    # 2) Forward pass, grab last_hidden_state
    with torch.no_grad():
        outputs = model(**inputs)
        # outputs.last_hidden_state: [batch, seq_len, hidden_size]
        hidden_states = outputs.last_hidden_state

    # 3) Mean-pool over the sequence dimension → [batch, hidden_size]
    embeddings = hidden_states.mean(dim=1)

    # 4) Detach, move to CPU, convert to NumPy → (hidden_size,)
    return embeddings.cpu().numpy()


def rank_methods_by_llm_embedding_similarity(test_df, method_df, fail_log_df, llm="codebert") -> pd.DataFrame:
    # Load BERT model (using Microsoft's CodeBERT variant)
    if llm == "codebert":
        model_name, tokenizer, model = codebert_model_define()
    elif llm == "codet5":
        model_name, tokenizer, model = codet5_model_define()  # Default to CodeBERT if no other model specified 
    elif llm == "bigbird":
        model_name, tokenizer, model = bigbird_model_define()  # Default to CodeBERT if no other model specified 
    elif llm == "gpt2":
        model_name, tokenizer, model = gpt2_model_define()
    elif llm == "llama":
        #model_name, tokenizer, model = llama_model_define()
        model_name, tokenizer, model = llama3_model_define()
    elif llm == "qwen":
        model_name, tokenizer, model = qwen_model_define()

    # Generate embeddings
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)
    model.eval()
    
    # Get code snippets
    test_code = test_df.iloc[0]['test_code']
    method_bodies = method_df['Body'].tolist()
    fail_log = fail_log_df.iloc[0]['Failure']
    
    # Generate embeddings
    if llm == "codebert":
        test_embedding = get_codebert_embeddings(test_code, tokenizer, model, device) 
        method_embeddings = [get_codebert_embeddings(body, tokenizer, model, device) for body in method_bodies]
    elif llm  == "codet5":
        test_embedding = get_codet5_embeddings(test_code, tokenizer, model, device)
        method_embeddings = [get_codet5_embeddings(body, tokenizer, model, device) for body in method_bodies]
    elif llm == "bigbird":
        test_embedding = get_bigbird_embeddings(test_code, tokenizer, model, device)
        method_embeddings = [get_bigbird_embeddings(body, tokenizer, model, device) for body in method_bodies]
    elif llm == "gpt2":
        test_embedding   = get_gpt2_embeddings(test_code, tokenizer, model, device)
        log_embedding = get_gpt2_embeddings(fail_log, tokenizer, model, device)
        method_embeddings = [get_gpt2_embeddings(body, tokenizer, model, device) for body in method_bodies]
    elif llm == "llama":
        test_embedding   = get_llama3_embeddings(test_code, tokenizer, model, device)
        method_embeddings = [get_llama3_embeddings(body, tokenizer, model, device) for body in method_bodies]

    elif llm == "qwen":
        test_embedding   = get_qwen_embeddings(test_code, tokenizer, model, device)
        method_embeddings = [get_qwen_embeddings(body, tokenizer, model, device) for body in method_bodies]
    
    '''# Compute cosine similarity
    similarities = [cosine_similarity(test_embedding, method_embedding).item() for method_embedding in method_embeddings]
    #print("similarities", len(similarities), similarities[:5])
    # Add similarity scores to DataFrame
    method_df['similarity'] = similarities
    # Sort by similarity
    method_df = method_df.sort_values(by='similarity', ascending=False).reset_index(drop=True)
    return method_df'''

    test_sims = [cosine_similarity(test_embedding, m)[0,0] for m in method_embeddings]
    log_sims  = [cosine_similarity(log_embedding,  m)[0,0] for m in method_embeddings]

    # 5) assemble into a DataFrame
    df = method_df.copy()
    df["sim_to_test"]    = test_sims
    df["sim_to_log"]     = log_sims
    #df["combined_sim"]   = (df["sim_to_test"] + df["sim_to_log"]) / 2
    df["combined_sim"]   = (0.3*df["sim_to_test"] + 0.7*df["sim_to_log"])

    # 6) rank and return
    return df.sort_values("combined_sim", ascending=False).reset_index(drop=True) 




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

