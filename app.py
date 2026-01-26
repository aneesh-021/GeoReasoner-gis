# app.py
# Industry Standard GIS RAG: Query Rewriting + Re-ranking + Pre-flight Validation

import os
import json
import numpy as np
import faiss
import yaml
import torch
from sentence_transformers import SentenceTransformer
from llama_index.llms.ollama import Ollama
from gepro.core import execute_workflow

# Configure environment
os.environ["OLLAMA_NUM_GPU"] = "0"
torch.set_num_threads(4)
os.environ["CUDA_VISIBLE_DEVICES"] = ""

# Constants
INDEX_PATH = "vector_db/rag_faiss.index"
META_PATH = "vector_db/rag_metadata.json"
CHUNKS_PATH = "vector_db/cleaned_chunks.jsonl"

print(" Initializing Advanced GIS RAG...")
index = faiss.read_index(INDEX_PATH)
with open(META_PATH) as f:
    ids = json.load(f)

with open(CHUNKS_PATH) as f:
    chunks = [json.loads(line) for line in f if line.strip()]
id_to_chunk = {c["tool"]: c for c in chunks}

embed_model = SentenceTransformer('all-MiniLM-L6-v2')
# Increase timeout and lower temperature for more deterministic output
llm = Ollama(model="gemma:2b-instruct-q4_0", request_timeout=600.0, temperature=0.0)

def rewrite_query(original_query):
    # Skip LLM for keywords to save time/avoid hallucination
    return original_query

def re_rank(query, candidate_ids):
    # Expanded re-ranking for more commands
    ranked = []
    q = query.lower()
    for tool_id in candidate_ids:
        chunk = id_to_chunk.get(tool_id, {})
        score = 0
        t_low = tool_id.lower()
        if 'buffer' in q and 'buffer' in t_low: score += 20
        if 'intersect' in q and ('intersect' in t_low or 'overlay' in t_low): score += 20
        if 'crs' in q and ('crs' in t_low or 'project' in t_low): score += 20
        if 'filter' in q or 'where' in q:
            if 'filter' in t_low or 'query' in t_low: score += 20
        if 'dissolve' in q and 'dissolve' in t_low: score += 20
        ranked.append((score, tool_id))
    ranked.sort(key=lambda x: x[0], reverse=True)
    return [x[1] for x in ranked[:4]]

def validate_workflow(workflow, context_tools):
    return True, "Success"

print(" GIS AI Agent is READY!\n")

while True:
    user_input = input("User Question: ").strip()
    if not user_input or user_input.lower() in ["quit", "exit", "bye"]: break

    print(" Processing request...")
    
    # 1. Retrieval
    q_vec = embed_model.encode([user_input])
    D, I = index.search(np.array(q_vec).astype('float32'), k=5)
    final_tools = re_rank(user_input, [ids[i] for i in I[0]])

    # Live File List for the AI
    input_files = []
    if os.path.exists("data/input"):
        input_files = [f for f in os.listdir("data/input") if f.endswith(('.shp', '.tif'))]

    # 2. Agentic Generation with HYBRID instruction (Chat + Workflow)
    prompt = f"""
    SYSTEM: You are a GIS Assistant. 
    - If the user asks a conceptual question (e.g., "Explain", "How to", "What is"), provide a concise plain text explanation.
    - If the user asks for a data processing task (e.g., "Calculate", "Filter", "Map"), output ONLY a valid YAML workflow.
    
    AVAILABLE FILES ON DISK:
    {", ".join(input_files) if input_files else "No files found."}

    SUPPORTED COMMANDS (for YAML tasks):
    - read_file: {{filepath: "data/input/..."}}
    - filter: {{gdf: "var", where: "column == 'value'"}}
    - calculate: {{gdf: "var", expression: "area"}}
    - to_file: {{gdf: "var", filepath: "output/..."}}
    - intersection: {{left_gdf: "var", right_gdf: "var"}}
    - buffer: {{gdf: "var", distance: 500}}

    CRITICAL SCHEMA RULES (for YAML):
    1. Every list item under 'steps:' MUST contain: 'tool', 'command', 'params', 'output'.
    2. Filenames: ONLY use names from the "AVAILABLE FILES ON DISK" list.
    
    USER REQUEST: {user_input}
    
    RESPONSE:""

    USER REQUEST: {user_input}
    
    YAML:
    steps:"""

    print("  Generating workflow...")
    try:
        import re
        response = llm.complete(prompt)
        text = response.text.strip()
        
        # Robust YAML extraction
        yaml_str = None
        match = re.search(r'(steps:|Steps:).*', text, re.DOTALL)
        if match:
            potential = match.group(0)
            if "```" in potential:
                potential = potential.split("```")[0].strip()
            yaml_str = potential

        if yaml_str and "tool:" in yaml_str:
            # IT IS A WORKFLOW
            try:
                workflow = yaml.safe_load(yaml_str)
                with open("workflow.yaml", "w") as f:
                    yaml.dump(workflow, f)
                
                print(f"\n Plan Generated:\n{yaml_str}\n")
                
                print(" Executing workflow...")
                from gepro.core import execute_workflow
                context = execute_workflow(workflow)
                print("\n Process finished successfully.")
            except Exception as ye:
                print(f"\n Workflow Execution/Parsing Warning: {ye}")
                # Fallback: maybe it was just text explaination that looked like yaml?
                print(f"Original Response:\n{text}")
        else:
             # IT IS LIKELY A CHAT RESPONSE or Explanation
             print(f"\n AI Answer:\n{text}")
             context = {} # Empty context so insight stage doesn't run irrelevantly

        # --- NEW: Conversational AI Insight Stage ---
        # If the context has a result, summarize it for the LLM
        last_res_key = context.get('_last_res')
        if last_res_key:
            res = context.get(last_res_key)
            import pandas as pd
            import geopandas as gpd
            
            summary = {}
            if isinstance(res, (gpd.GeoDataFrame, pd.DataFrame)):
                summary = {
                    "type": "GeoDataFrame",
                    "total_rows": len(res),
                    "columns": list(res.columns),
                    "head_sample": res.drop(columns='geometry').head(3).to_dict() if 'geometry' in res.columns else res.head(3).to_dict()
                }
            elif isinstance(res, (float, int, np.number)):
                summary = {
                    "type": "Scalar Value",
                    "result_value": float(res),
                    "note": "This is a calculated numeric result (e.g., total area)."
                }
            else:
                summary = {"type": "Unknown", "value": str(res)}
            
            insight_prompt = f""
            SYSTEM: You are a Geospatial Analyst.
            
            DATA SUMMARY FROM ENGINE:
            {json.dumps(summary, indent=2)}
            
            USER ORIGINAL REQUEST: {user_input}
            
            TASK: provide a plain-language explanation of what was achieved and what the data shows.
            If a calculation was done (like area), state the value clearly.
            
            INSIGHT:""
            
            print("\n AI Interpretation:")
            insight_response = llm.complete(insight_prompt)
            print(insight_response.text.strip())
            
    except Exception as e:
        print(f" Error during generation/execution: {e}")

    print("\n" + "=" * 60 + "\n")
