import tiktoken

def count_prompt_tokens(messages, model="gpt-4o"):
    """
    messages = [{"role":"system","content":"..."}, {"role":"user","content":"..."}]
    Returns an estimate of prompt tokens for Chat Completions.
    Works for gpt-4o / gpt-4 / 3.5, etc.
    """
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        # sensible fallbacks
        enc = tiktoken.get_encoding("o200k_base" if "4o" in model else "cl100k_base")

    total = 0
    for m in messages:
        role = str(m.get("role", ""))
        content = m.get("content", "")
        if not isinstance(content, str):
            content = str(content)
        # rough-but-safe per-message overhead (+6) plus role+content tokens
        total += len(enc.encode(role)) + len(enc.encode(content)) + 6

    # small priming overhead
    return total + 2

#import math
#import tiktoken
#
#def count_prompt_tokens(messages, model="gpt-4o"):
#    """
#    Rough-but-safe token count for chat prompts.
#    Works for gpt-4o/4o-mini/4/3.5 (tiktoken picks the right encoding).
#    """
#    enc = tiktoken.encoding_for_model(model)
#    # Per-message overhead varies by model; +6/msg is a conservative cushion.
#    total = 0
#    for m in messages:
#        total += len(enc.encode(m.get("role",""))) + len(enc.encode(m.get("content",""))) + 6
#    # small extra priming overhead
#    return total + 2
#
#def estimate_cost(prompt_tokens, completion_tokens=0, in_per_1k=0.0, out_per_1k=0.0):
#    """Optional: plug your model’s $/1k token rates to get a cost estimate."""
#    return (prompt_tokens/1000.0)*in_per_1k + (completion_tokens/1000.0)*out_per_1k
