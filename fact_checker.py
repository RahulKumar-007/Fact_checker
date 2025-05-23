import re
import time
import random
import json # For the fallback in process_claim, though verdict_generator handles primary JSON
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser

from llm_utils import init_llm, init_search_tool
from source_evaluator import SourceEvaluator
from knowledge_base import KnowledgeBase
from verdict_generator import EnhancedVerdictGenerator
from cache_manager import CacheManager

class FactChecker:
    def __init__(self):
        self.llm = init_llm()
        self.search_tool = init_search_tool()
        self.cache_manager = CacheManager()
        
        self.source_evaluator = SourceEvaluator(self.llm)
        self.knowledge_base = KnowledgeBase() # Consider passing embeddings model name if configurable
        
        self.setup_claim_analyzer()
        # EnhancedVerdictGenerator is initialized in setup_verdict_generator
        self.setup_verdict_generator() 
    
    def setup_claim_analyzer(self):
        claim_template = """
        Analyze the following claim and break it down into key components for verification:
        CLAIM: {claim}
        
        Identify:
        1. Main assertion(s) being made.
        2. Key entities (people, organizations, locations, concepts) mentioned.
        3. Specific factual sub-claims or questions that need to be checked to verify the overall claim.
        4. Generate 3 to 5 diverse and specific search queries that would help gather evidence to verify these sub-claims.
           Focus on queries that seek factual information, not opinions.
        
        Provide your output in the following format:
        Main Assertion: <The central point of the claim>
        Key Entities: <Entity1, Entity2, ...>
        Facts to Check:
        - <Fact/Question 1>
        - <Fact/Question 2>
        ...
        Search Queries:
        - "<Query 1>"
        - "<Query 2>"
        - "<Query 3>"
        """
        # Removed the 5-7 query constraint, 3-5 is more typical for initial search
        
        claim_prompt = PromptTemplate(template=claim_template, input_variables=["claim"])
        self.claim_analyzer = claim_prompt | self.llm | StrOutputParser()
    
    def setup_verdict_generator(self):
        self.verdict_generator = EnhancedVerdictGenerator(
            self.llm, 
            self.source_evaluator, 
            self.knowledge_base
        )
    
    def process_claim(self, claim):
        cached_result = self.cache_manager.get_verdict(claim)
        if cached_result:
            print("Using cached verdict for claim.")
            return cached_result
            
        print(f"\nProcessing claim: {claim}")
        analysis_result_str = self.claim_analyzer.invoke({"claim": claim})
        print("1. Claim Analysis Complete.")
        print(f"   Analysis: {analysis_result_str[:200]}...") # Print snippet
        
        # Extract search queries robustly
        # Original regex: r'- "(.*)"' might miss queries not in quotes.
        # More robust: find lines starting with '-' under "Search Queries:"
        search_queries = []
        try:
            queries_section = analysis_result_str.split("Search Queries:")[1]
            for line in queries_section.splitlines():
                line = line.strip()
                if line.startswith("-"):
                    query = line[1:].strip().strip('"') # Remove leading '-' and any quotes
                    if query: # Ensure not an empty query
                        search_queries.append(query)
        except IndexError: # "Search Queries:" not found
            print("Warning: 'Search Queries:' section not found in analysis. Using fallback regex.")
            search_queries = re.findall(r'-\s*"?([^"\n]+)"?', analysis_result_str) # broader match
        
        if not search_queries:
            print("Warning: No search queries extracted. Using claim as a single query.")
            search_queries = [claim] # Fallback to searching the claim itself

        print(f"   Extracted {len(search_queries)} search queries: {search_queries[:3]}")

        evidence_parts = []
        unique_queries_processed = set() # To avoid redundant searches if LLM repeats queries
        
        # Limit queries to a reasonable number, e.g., first 3-5 unique ones
        for query in search_queries[:3]: 
            if query in unique_queries_processed:
                continue
            unique_queries_processed.add(query)

            print(f"   Searching for: {query[:70]}...")
            cached_search = self.cache_manager.get_search_result(query)
            if cached_search:
                search_output = cached_search
            else:
                try:
                    search_output = self.search_tool.run(query)
                    self.cache_manager.cache_search_result(query, search_output)
                    time.sleep(random.uniform(1.0, 2.0)) # Shorter delay, adjust if rate limited
                except Exception as e:
                    search_output = f"Error during search: {str(e)}"
                    print(f"      Error searching for '{query}': {e}")
            evidence_parts.append(f"Query: {query}\nResult:\n{search_output}\n---")
        
        combined_evidence = "\n\n".join(evidence_parts)
        print("2. Evidence Retrieval Complete.")
        if not combined_evidence:
            combined_evidence = "No evidence gathered from web search."
        
        verdict_json = self.verdict_generator.generate_verdict(claim, combined_evidence)
        print("3. Verdict Generation Complete.")
        
        # Add high-confidence facts to knowledge base
        if isinstance(verdict_json, dict) and verdict_json.get("confidence_score", 0) >= 75:
            verdict_status = verdict_json.get("verdict", "").lower()
            if verdict_status == "true":
                self.knowledge_base.add_fact(f"It is true that: {claim}")
            elif verdict_status == "false":
                self.knowledge_base.add_fact(f"It is false that: {claim}")
        
        final_result = {
            "claim": claim,
            "analysis": analysis_result_str,
            "evidence": combined_evidence,
            "verdict": verdict_json # This is already a dict from EnhancedVerdictGenerator
        }
        
        self.cache_manager.cache_verdict(claim, final_result)
        return final_result