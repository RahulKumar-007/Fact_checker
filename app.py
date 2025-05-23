# app.py
import streamlit as st # Streamlit import
import time
import json
import pandas as pd
import plotly.express as px
from streamlit_agraph import agraph, Node, Edge, Config
import pickle
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file at the very beginning
# This is NOT a Streamlit command, so it's fine here.
load_dotenv()

# --- Page Configuration (MUST BE THE FIRST STREAMLIT COMMAND) ---
st.set_page_config(
    layout="wide",
    page_title="LLM Fact-Checker",
    page_icon="🔬"
)

# Import your fact checker components (after load_dotenv and page_config)
from fact_checker import FactChecker

# Initialize session state for history (Now after set_page_config)
if 'history' not in st.session_state:
    st.session_state.history = []
if 'selected_history' not in st.session_state:
    st.session_state.selected_history = None

# Load existing history if available
history_file = "fact_check_history.pkl"
if os.path.exists(history_file):
    if not st.session_state.history: # Load only if session history is empty
        try:
            with open(history_file, 'rb') as f:
                st.session_state.history = pickle.load(f)
        except (pickle.UnpicklingError, EOFError, AttributeError, ImportError, IndexError) as e: # Added more specific exceptions
            st.session_state.history = [] # Start fresh if unpickling fails
            if os.path.exists(history_file): # Remove corrupted file
                 try:
                     os.remove(history_file)
                     st.warning(f"Corrupted history file ({history_file}) found and removed. Starting with a fresh history. Error: {e}")
                 except Exception as remove_err:
                     st.error(f"Could not remove corrupted history file {history_file}. Error: {remove_err}")


# Initialize the fact checker (using st.cache_resource, now after set_page_config)
@st.cache_resource
def get_fact_checker_instance():
    return FactChecker()

fact_checker = get_fact_checker_instance()

# --- UI Layout ---
# st.set_page_config(layout="wide") # MOVED TO THE TOP

st.title("🔬 LLM-Powered Autonomous Fact-Checker")
st.markdown("### Verify claims using AI, web search, knowledge base integration, and source evaluation.")

# Mobile-friendly UI adjustments
st.markdown("""
<style>
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        /* background-color: #f0f2f6; */ /* Optional: Light grey background for input fields */
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    @media (max-width: 768px) {
        .block-container {
            padding-top: 0.5rem;
            padding-bottom: 0.5rem;
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }
    }
    .stButton>button { /* Make sidebar buttons full width */
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)


# --- Helper Functions for Visualization ---
def extract_entities_from_analysis(analysis_text):
    try:
        if "Key Entities:" in analysis_text:
            # Ensure we split correctly even if "Facts to Check:" is missing
            parts = analysis_text.split("Key Entities:", 1)
            if len(parts) > 1:
                entities_section = parts[1].split("Facts to Check:")[0] # Take section before "Facts to Check:"
                entities = [e.strip() for e in entities_section.splitlines() if e.strip() and not e.strip().startswith("- ") and not e.strip().lower().startswith("facts to check")]
                # Further refine by splitting by comma if entities are on one line
                refined_entities = []
                for entity_line in entities:
                    refined_entities.extend([e.strip() for e in entity_line.split(',') if e.strip()])
                return [e for e in refined_entities if e][:5] # Limit for viz
        return []
    except Exception as e:
        # st.warning(f"Error extracting entities: {e}")
        return []

def extract_evidence_snippets_from_combined(combined_evidence, max_snippets=3):
    snippets = []
    if not combined_evidence or not isinstance(combined_evidence, str):
        return snippets
    query_blocks = combined_evidence.split("Query:")[1:]
    for block in query_blocks:
        if "Result:" in block:
            query_part, result_part = block.split("Result:", 1)
            query_text = query_part.strip()
            result_summary = "\n".join(result_part.strip().splitlines()[:3]) # First 3 lines of result
            snippets.append(f"Q: {query_text[:30].strip()}...\nA: {result_summary[:70].strip()}...")
            if len(snippets) >= max_snippets:
                break
    return snippets


def create_reasoning_visualization(claim_text, analysis_text, combined_evidence, verdict_data):
    nodes = []
    edges = []

    claim_node_id = "claim_node"
    nodes.append(Node(id=claim_node_id, label=f"Claim: {claim_text[:50]}...", size=20, color="#FF6347")) # Tomato Red

    entities = extract_entities_from_analysis(analysis_text)
    for i, entity in enumerate(entities):
        entity_id = f"entity_{i}"
        nodes.append(Node(id=entity_id, label=f"Entity: {entity}", size=15, color="#4682B4")) # Steel Blue
        edges.append(Edge(source=claim_node_id, target=entity_id, label="mentions", length=150))

    evidence_snippets = extract_evidence_snippets_from_combined(combined_evidence)
    evidence_node_ids = []
    for i, snippet in enumerate(evidence_snippets):
        evidence_id = f"evidence_{i}"
        evidence_node_ids.append(evidence_id)
        nodes.append(Node(id=evidence_id, label=snippet, size=18, color="#3CB371", shape="box")) # Medium Sea Green
        edges.append(Edge(source=claim_node_id, target=evidence_id, label="checked by", length=200))

    verdict_text = verdict_data.get("verdict", "N/A") if isinstance(verdict_data, dict) else "N/A"
    verdict_color_map = {
        "true": "#2E8B57", "false": "#DC143C",
        "partially true": "#FFD700", "unverifiable": "#808080", "error": "#A9A9A9"
    }
    verdict_node_color = verdict_color_map.get(verdict_text.lower(), "#D3D3D3") # Default color
    verdict_node_id = "verdict_node"
    nodes.append(Node(id=verdict_node_id, label=f"Verdict: {verdict_text}", size=25, color=verdict_node_color))

    for ev_id in evidence_node_ids:
        edges.append(Edge(source=ev_id, target=verdict_node_id, label="informs", length=150))

    confidence = verdict_data.get("confidence_score", 0) if isinstance(verdict_data, dict) else 0
    confidence_node_id = "confidence_node"
    nodes.append(Node(id=confidence_node_id, label=f"Confidence: {confidence}%", size=15, color="#BA55D3")) # Medium Orchid
    edges.append(Edge(source=verdict_node_id, target=confidence_node_id, label="has score", length=100))

    config = Config(width=700, height=450, directed=True, physics=True, hierarchical=False,
                    node={'font': {'size': 10, 'strokeWidth':0, 'strokeColor':'#fff'}}, # Smaller font
                    edge={'font': {'size': 8}},
                    minVelocity=0.75)
    try:
        return agraph(nodes=nodes, edges=edges, config=config)
    except Exception as e:
        st.error(f"Failed to generate reasoning graph: {e}")
        return None

# --- Sidebar ---
with st.sidebar:
    st.header("📜 Fact Check History")
    if st.session_state.history:
        if st.button("Clear All History", type="secondary", key="clear_history_btn"):
            st.session_state.history = []
            st.session_state.selected_history = None
            if os.path.exists(history_file):
                try:
                    os.remove(history_file)
                except Exception as e:
                    st.error(f"Could not delete history file: {e}")
            st.rerun()

        # Display history items
        for i, item in enumerate(reversed(st.session_state.history)): # Show newest first
            claim_display = item.get("claim", "Unknown Claim")[:30] + "..."
            verdict_val = "N/A"
            if isinstance(item.get("verdict"), dict): # Make sure verdict is a dict
                verdict_val = item["verdict"].get("verdict", "N/A")
            
            button_label = f"{claim_display} ({verdict_val})"
            if st.button(button_label, key=f"history_{i}"):
                st.session_state.selected_history = item
                # No rerun here; main panel will check st.session_state.selected_history
    else:
        st.info("No previous fact checks.")

# --- Main Content Area ---
active_result = None # To store either selected history or new result

if st.session_state.get('selected_history'):
    active_result = st.session_state.selected_history
    st.session_state.selected_history = None # Clear after processing to avoid re-display on simple interactions

# Input form for new claims (always visible)
st.markdown("---") # Visual separator
st.header("🔍 Fact Check a New Claim")
with st.form("fact_check_form"):
    claim_input_main = st.text_area("Enter the claim you want to verify:", height=100, key="claim_input_main_form")
    submit_button_main = st.form_submit_button("✨ Verify Claim")

if submit_button_main and claim_input_main:
    with st.spinner("🕵️‍♀️ Fact-checking in progress... This might take a moment."):
        start_time = time.time()
        current_result_data = fact_checker.process_claim(claim_input_main)
        processing_time = time.time() - start_time

        current_result_data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_result_data['processing_time'] = processing_time
        st.session_state.history.append(current_result_data) # Append to keep order
        st.session_state.history = st.session_state.history[-50:] # Keep last 50

        try:
            with open(history_file, 'wb') as f:
                pickle.dump(st.session_state.history, f)
        except Exception as e:
            st.error(f"Failed to save history: {e}")
        
        active_result = current_result_data # Set the new result as active for display
        st.success(f"Fact check complete! ({processing_time:.2f}s)")
        # We don't rerun here immediately to allow the active_result to be displayed below.
        # The next natural interaction or a targeted rerun will refresh the sidebar.

elif not claim_input_main and submit_button_main:
    st.warning("Please enter a claim to verify.")


# Display area for the active result (either selected history or new result)
if active_result:
    with st.container(): # Use a container to group the display
        st.markdown("---") # Separator before displaying result
        
        claim_text = active_result.get("claim", "N/A")
        analysis_text = active_result.get("analysis", "N/A")
        evidence_text = active_result.get("evidence", "No evidence collected.")
        verdict_data = active_result.get("verdict", {}) # Ensure verdict_data is a dict
        if not isinstance(verdict_data, dict): # Handle case where verdict might be a string (e.g. error)
            verdict_data = {"verdict": str(verdict_data), "confidence_score": 0, "explanation": "Could not parse verdict."}

        processing_time_display = active_result.get("processing_time", 0)
        timestamp_display = active_result.get("timestamp", "N/A")

        st.caption(f"Displaying result for: \"{claim_text[:70]}...\"")
        st.caption(f"Fact check performed on: {timestamp_display} | Processing time: {processing_time_display:.2f}s")

        # Verdict Card
        verdict_value = verdict_data.get("verdict", "N/A")
        confidence_value = verdict_data.get("confidence_score", 0)
        verdict_color_map = {"True": "#e6ffe6", "False": "#ffe6e6", "Partially True": "#fff0e6", "Unverifiable": "#f2f2f2", "Error": "#ffcccc"}
        card_bg_color = verdict_color_map.get(verdict_value, "#e6f7ff") # Default blueish

        st.markdown(f"""
        <div style="padding:15px; margin-bottom:15px; border-radius:10px; background-color:{card_bg_color}; border: 1px solid #ccc;">
            <h2 style="color:black; margin-top:0;">Verdict: {verdict_value}</h2>
            <h4 style="color:black;">Confidence: {confidence_value}/100</h4>
        </div>
        """, unsafe_allow_html=True)

        # Tabs for details
        detail_tab1, detail_tab2, detail_tab3, detail_tab4 = st.tabs(["📝 Explanation", "📊 Analysis & Evidence", "🧠 Reasoning Flow", "📚 Knowledge Base Info"])

        with detail_tab1:
            st.subheader("Explanation of Verdict")
            st.markdown(f"**Confidence Reasoning:** {verdict_data.get('confidence_reasoning', 'N/A')}")
            st.markdown(f"{verdict_data.get('explanation', 'No explanation provided.')}")
            
            cols = st.columns(2)
            with cols[0]:
                st.subheader("Key Evidence Points")
                key_ev = verdict_data.get("key_evidence_points", [])
                if key_ev and isinstance(key_ev, list):
                    for item in key_ev: st.markdown(f"- {item}")
                else: st.info("No key evidence listed.")
            
            with cols[1]:
                st.subheader("Supporting Sources")
                sources = verdict_data.get("supporting_sources_domains", [])
                if sources and isinstance(sources, list):
                    for src in sources: st.markdown(f"- {src}")
                else: st.info("No supporting sources listed.")

            contr_ev = verdict_data.get("contradicting_evidence_points", [])
            if contr_ev and isinstance(contr_ev, list) and (len(contr_ev) > 1 or (len(contr_ev) == 1 and contr_ev[0] != 'No significant contradicting evidence found.')):
                st.subheader("Contradicting Evidence")
                for item in contr_ev: st.markdown(f"- {item}")
        
        with detail_tab2:
            st.subheader("Claim Analysis")
            st.text_area("LLM Analysis Output", value=analysis_text, height=200, disabled=True, key=f"analysis_text_{timestamp_display}")
            st.subheader("Collected Evidence Snippets")
            st.text_area("Raw Evidence Data", value=evidence_text, height=300, disabled=True, key=f"evidence_text_{timestamp_display}")

        with detail_tab3:
            st.subheader("Visualized Reasoning Network")
            if claim_text and analysis_text and evidence_text and verdict_data: # Ensure data is present
                 graph_viz = create_reasoning_visualization(claim_text, analysis_text, evidence_text, verdict_data)
                 if graph_viz:
                     pass # agraph renders itself if it's the last expression in the block
            else:
                st.info("Insufficient data to generate reasoning graph.")

        with detail_tab4:
            st.subheader("Knowledge Base Interaction")
            st.markdown(f"**Relevance to Verdict:** {verdict_data.get('knowledge_base_relevance', 'N/A')}")


# Instructions / About section at the bottom
st.markdown("---") # Visual separator
st.markdown("""
### About This Fact-Checker
This tool leverages Large Language Models (LLMs), web search capabilities, a dynamic knowledge base, and source reliability assessment to provide comprehensive fact-checking. 
- **Enter a claim** in the text box above.
- **The system will:**
    1. Analyze the claim to identify key checkable components.
    2. Search the web for relevant evidence.
    3. Evaluate the reliability of information sources.
    4. Consult its internal knowledge base for existing facts.
    5. Synthesize all information to generate a verdict (True, False, Partially True, Unverifiable) along with a confidence score and detailed explanation.
- **Review results**, including the verdict, evidence, and analysis steps.
- **Browse past checks** using the history panel in the sidebar.

**Disclaimer:** This tool is for informational purposes and uses AI, which may sometimes produce incorrect or incomplete results. Always cross-verify critical information.
""")