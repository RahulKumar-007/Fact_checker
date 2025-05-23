import json
import re
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser

class SourceEvaluator:
    def __init__(self, llm):
        self.llm = llm
        
        self.initialize_reliability_db()
        
        self.evaluation_prompt = PromptTemplate(
            template="""
            Evaluate the reliability of the following source based on the provided content:
            
            SOURCE CONTENT: {content}
            
            Please analyze this source considering:
            1. Credibility (official source, established news outlet, etc.)
            2. Objectivity (neutral language vs. biased framing)
            3. Evidence presentation (facts, citations, quotes)
            4. Currency (recent vs. outdated information)
            
            Rate the source on a scale of 1-10 for:
            - RELIABILITY SCORE (1=not reliable, 10=highly reliable)
            - EXPERTISE SCORE (1=no expertise, 10=high expertise)
            - BIAS SCORE (1=highly biased, 10=minimal bias)
            
            Provide your assessment in the following JSON format:
            {{
                "source_domain": "extracted domain or source name",
                "reliability_score": X,
                "expertise_score": X,
                "bias_score": X,
                "overall_score": X,
                "reasoning": "brief explanation"
            }}
            """,
            input_variables=["content"]
        )
        
        self.evaluation_chain = self.evaluation_prompt | self.llm | StrOutputParser()
    
    def initialize_reliability_db(self):
        self.reliability_data = {
            "bbc.com": {"reliability": 8, "expertise": 8, "bias": 7},
            "nytimes.com": {"reliability": 8, "expertise": 8, "bias": 6},
            "reuters.com": {"reliability": 9, "expertise": 9, "bias": 8},
            "wikipedia.org": {"reliability": 7, "expertise": 7, "bias": 7},
            "cnn.com": {"reliability": 7, "expertise": 7, "bias": 5},
            "foxnews.com": {"reliability": 6, "expertise": 6, "bias": 4},
            "theonion.com": {"reliability": 1, "expertise": 5, "bias": 5}, # Satire
            "gov": {"reliability": 8, "expertise": 9, "bias": 6}, # Generic TLD
            "edu": {"reliability": 8, "expertise": 9, "bias": 7}, # Generic TLD
        }
    
    def extract_domain(self, content):
        domains = re.findall(r'(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', content)
        if domains:
            # Handle common subdomains like .co.uk, .ac.uk etc.
            parts = domains[0].lower().split('.')
            if len(parts) > 2 and parts[-2] in ['co', 'com', 'org', 'net', 'ac', 'gov']: # e.g. bbc.co.uk
                return ".".join(parts[-3:])
            return ".".join(parts[-2:]) # e.g. example.com or example.org
        return "unknown"
    
    def evaluate_source(self, content):
        try:
            domain = self.extract_domain(content)
            
            # Check TLDs like .gov or .edu first if domain is specific
            matched_tld_data = None
            for tld_key in ["gov", "edu"]:
                if domain.endswith(f".{tld_key}"):
                    matched_tld_data = self.reliability_data.get(tld_key)
                    break
            
            if domain in self.reliability_data:
                data = self.reliability_data[domain]
            elif matched_tld_data:
                data = matched_tld_data
            else: # For unknown sources, evaluate content
                llm_result_str = self.evaluation_chain.invoke({"content": content})
                try:
                    evaluation = json.loads(llm_result_str)
                    # Ensure domain in evaluation matches extracted, or update if LLM provided one
                    evaluated_domain = evaluation.get("source_domain", domain).lower()
                    if evaluated_domain == "unknown" and domain != "unknown":
                         evaluation["source_domain"] = domain
                    else:
                         domain = evaluated_domain

                    # Update our database with this new source if it's not a generic TLD
                    if domain not in ["gov", "edu"] and domain != "unknown":
                         self.reliability_data[domain] = {
                            "reliability": evaluation["reliability_score"],
                            "expertise": evaluation["expertise_score"],
                            "bias": evaluation["bias_score"]
                        }
                    return evaluation
                except json.JSONDecodeError:
                    return {
                        "source_domain": domain,
                        "reliability_score": 5, "expertise_score": 5, "bias_score": 5,
                        "overall_score": 5,
                        "reasoning": f"Unable to parse LLM evaluation for '{domain}'. Using neutral score. LLM Output: {llm_result_str[:200]}..."
                    }

            # If data was found (pre-assessed or TLD match)
            overall_score = (data["reliability"] + data["expertise"] + data["bias"]) / 3
            return {
                "source_domain": domain,
                "reliability_score": data["reliability"],
                "expertise_score": data["expertise"],
                "bias_score": data["bias"],
                "overall_score": round(overall_score, 2),
                "reasoning": f"Pre-assessed source or TLD with known reliability metrics."
            }

        except Exception as e:
            return {
                "source_domain": self.extract_domain(content) or "error",
                "reliability_score": 3, "expertise_score": 3, "bias_score": 3,
                "overall_score": 3,
                "reasoning": f"Error evaluating source: {str(e)}"
            }