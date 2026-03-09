@app.post("/secure-generate")
def secure_generate(q: Query):
    # Step 1: Semantic Deconstruction (Prompt Analyzer)
    terms = deconstruct(q.query)['nouns']
    
    # Step 2: Path A (Knowledge Graph Navigator)
    concept_map = kg_navigator.get_semantic_context(terms)
    
    # Step 3: Path B (RAG Engine / Resource Manager)
    # Ensuring WORM integrity before loading
    if verify_worm_integrity("secure-code.yaml", "EXPECTED_SHA"):
        grounding_docs = load_yaml("secure-code.yaml")
    
    # Step 4: Reasoning Bridge (Synthesis)
    # We combine the semantic roots with the hard constraints
    reliability = evaluate_source_quality(str(grounding_docs), len(grounding_docs))
    
    return {
        "verified_plan": {
            "concepts": concept_map,
            "constraints": grounding_docs['constraints']['hard']
        },
        "reliability": reliability
    }
