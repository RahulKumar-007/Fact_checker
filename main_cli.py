from dotenv import load_dotenv
import traceback
import json # For pretty printing dict

# Load environment variables from .env file at the very beginning
load_dotenv()

from fact_checker import FactChecker # Import after load_dotenv

def main():
    fact_checker = FactChecker()
    
    print("Welcome to the Enhanced LLM-Powered Autonomous Fact-Checker (CLI)")
    print("-----------------------------------------------------------------")
    
    while True:
        claim = input("\nEnter a claim to fact-check (or 'quit' to exit): \n> ")
        
        if claim.lower() == 'quit':
            break
        if not claim.strip():
            print("Please enter a claim.")
            continue
            
        print("\nProcessing claim, please wait...")
        try:
            result = fact_checker.process_claim(claim)
            
            print("\n======= CLAIM ANALYSIS =======")
            print(result["analysis"])
            
            print("\n======= EVIDENCE COLLECTED (Snippets) =======")
            # Print only a summary of evidence to keep CLI clean
            evidence_summary = result["evidence"]
            if len(evidence_summary) > 1000:
                evidence_summary = evidence_summary[:1000] + "\n... (evidence truncated for display)"
            print(evidence_summary)
            
            print("\n======= VERDICT =======")
            verdict = result["verdict"] # This should be a dictionary

            if isinstance(verdict, dict):
                print(f"VERDICT: {verdict.get('verdict', 'N/A')}")
                print(f"CONFIDENCE: {verdict.get('confidence_score', 'N/A')}/100")
                print(f"CONFIDENCE REASONING: {verdict.get('confidence_reasoning', 'N/A')}")
                print(f"\nEXPLANATION:\n{verdict.get('explanation', 'N/A')}")
                
                print("\nKEY EVIDENCE POINTS:")
                for ev_point in verdict.get('key_evidence_points', []):
                    print(f"- {ev_point}")
                
                print("\nSUPPORTING SOURCES DOMAINS:")
                for source_domain in verdict.get('supporting_sources_domains', []):
                    print(f"- {source_domain}")

                contradicting = verdict.get('contradicting_evidence_points', [])
                if contradicting and contradicting[0] != 'No significant contradicting evidence found.':
                    print("\nCONTRADICTING EVIDENCE POINTS:")
                    for contradiction in contradicting:
                        print(f"- {contradiction}")
                
                print(f"\nKNOWLEDGE BASE RELEVANCE:\n{verdict.get('knowledge_base_relevance', 'N/A')}")

            else: # Fallback if verdict is not a dict (e.g. parsing error message)
                print("Could not parse verdict structure. Raw output:")
                print(verdict)
            
        except Exception as e:
            print(f"\n--- An error occurred while processing the claim: {str(e)} ---")
            traceback.print_exc()
        print("\n-----------------------------------------------------------------")

if __name__ == "__main__":
    main()