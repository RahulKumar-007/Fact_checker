import json
import re
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser

class EnhancedVerdictGenerator:
    def __init__(self, llm, source_evaluator, knowledge_base):
        self.llm = llm
        self.source_evaluator = source_evaluator
        self.knowledge_base = knowledge_base
        
        self.verdict_prompt = PromptTemplate(
            template="""
            You are an impartial fact-checker evaluating the truth of a claim based on evidence.
            
            CLAIM: {claim}
            
            EVIDENCE FROM SEARCH (snippets from web search results):
            {evidence}
            
            RELEVANT FACTS FROM KNOWLEDGE BASE:
            {knowledge_base_facts}
            
            SOURCE RELIABILITY ANALYSIS (scores 1-10, 10=best):
            {source_reliability}
            
            Carefully analyze all provided information. Consider:
            1. How directly the evidence addresses the claim.
            2. Reliability of sources (higher weight to more reliable sources).
            3. Consistency across multiple sources and with the knowledge base.
            4. Contradictions or nuances in the evidence.
            
            Provide your verdict as a detailed JSON object with the following structure:
            {{
                "verdict": "True/False/Partially True/Unverifiable",
                "confidence_score": <number_between_0_and_100>,
                "confidence_reasoning": "Brief explanation of why this confidence level was chosen, considering evidence strength and source reliability.",
                "explanation": "Detailed step-by-step explanation of the verdict, citing specific evidence and how it supports or refutes the claim. Mention how knowledge base facts and source reliability influenced the decision.",
                "key_evidence_points": ["List of the most important pieces of evidence (direct quotes or summaries from search results) that led to this verdict."],
                "supporting_sources_domains": ["List of domains of the most reliable sources that support the verdict."],
                "contradicting_evidence_points": ["List any significant evidence that contradicts the verdict or introduces nuance. If none, state 'No significant contradicting evidence found.'"],
                "knowledge_base_relevance": "Briefly describe how knowledge base facts (if any) were relevant to the verdict."
            }}
            
            Ensure your verdict is evidence-based and your confidence score accurately reflects the strength and reliability of the evidence.
            If evidence is weak, conflicting, or from unreliable sources, state 'Unverifiable' and explain why.
            """,
            input_variables=["claim", "evidence", "knowledge_base_facts", "source_reliability"]
        )
        
        self.verdict_chain = self.verdict_prompt | self.llm | StrOutputParser()
    
    def generate_verdict(self, claim, evidence_str):
        source_evaluations = []
        # Assuming evidence_str is a single string with "Query: ... Result: ..." blocks
        # For source evaluation, we need to pass content that might contain a URL or source name
        # A simple approach: evaluate based on the whole evidence string if individual sources aren't easily separable
        # A better approach would be to parse evidence_str for distinct source snippets if possible.
        
        # For now, let's assume evidence_str might contain discernible source info or evaluate it as a whole
        # If evidence_str is structured like: "Source: [URL/Name]\nContent: ...\n\nSource: ..."
        # Then split and process. If not, evaluate the whole thing or skip fine-grained eval here.
        # The current structure `evidence.append(f"Query: {query}\nResult: {search_result}\n")` makes it hard
        # to isolate individual sources from DuckDuckGo results unless search_result itself is structured.
        
        # Let's try to extract domains from the evidence string if possible
        temp_evidence_snippets = evidence_str.split("Query:")[1:] # Split by query
        processed_snippets_for_eval = []
        for snippet_block in temp_evidence_snippets:
            # Try to get the result part for evaluation
            if "Result:" in snippet_block:
                result_part = snippet_block.split("Result:", 1)[1]
                processed_snippets_for_eval.append(result_part.strip())

        for snippet in processed_snippets_for_eval[:5]: # Evaluate up to 5 snippets
            if snippet:
                evaluation = self.source_evaluator.evaluate_source(snippet)
                source_evaluations.append(evaluation)
        
        source_reliability_summary = json.dumps(source_evaluations, indent=2)
        
        knowledge_facts_list = self.knowledge_base.query_knowledge_base(claim)
        knowledge_base_facts_str = "\n".join(knowledge_facts_list) if knowledge_facts_list else "No relevant facts found in knowledge base."

        llm_input = {
            "claim": claim,
            "evidence": evidence_str,
            "knowledge_base_facts": knowledge_base_facts_str,
            "source_reliability": source_reliability_summary
        }
        
        raw_verdict_output = self.verdict_chain.invoke(llm_input)
        
        try:
            # Try to extract JSON from the string if it's embedded in markdown
            json_match = re.search(r'```json\s*(.*?)\s*```', raw_verdict_output, re.DOTALL)
            if json_match:
                parsed_verdict = json.loads(json_match.group(1))
            else:
                # Otherwise try to parse the whole string
                parsed_verdict = json.loads(raw_verdict_output)
            
            # Basic validation of expected keys
            expected_keys = ["verdict", "confidence_score", "explanation"]
            if not all(key in parsed_verdict for key in expected_keys):
                 raise json.JSONDecodeError("Missing expected keys in parsed JSON.", raw_verdict_output, 0)
            return parsed_verdict

        except json.JSONDecodeError as e:
            print(f"Warning: JSON parsing failed for verdict. Error: {e}. Raw output: {raw_verdict_output[:500]}...")
            # Fallback with more detail about the parsing error
            return {
                "verdict": "Error",
                "confidence_score": 0,
                "confidence_reasoning": "Failed to parse the LLM's verdict output. The structure was not valid JSON.",
                "explanation": f"Could not generate a structured verdict due to a parsing error. Raw LLM output (partial): {raw_verdict_output}",
                "key_evidence_points": [],
                "supporting_sources_domains": [],
                "contradicting_evidence_points": [],
                "knowledge_base_relevance": "Could not be determined due to parsing error."
            }