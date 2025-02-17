import streamlit as st
import asyncio
from competitive_analysis_agent import CompetitiveAnalysis
from pathlib import Path
import os
from difflib import get_close_matches

# Configure Streamlit page
st.set_page_config(
    page_title="Amazon Competitive Analysis",
    page_icon="📊",
    layout="wide"
)

# Ensure dashboards directory exists
os.makedirs("dashboards", exist_ok=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = None
if 'current_dashboard' not in st.session_state:
    st.session_state.current_dashboard = None
if 'brand_validation' not in st.session_state:
    st.session_state.brand_validation = None
if 'pending_analysis' not in st.session_state:
    st.session_state.pending_analysis = None

def validate_brand(brand: str, available_brands: list) -> tuple[bool, list]:
    """Validate and find close matches for a brand name."""
    # First try exact match (case insensitive)
    exact_matches = [b for b in available_brands if b.lower() == brand.lower()]
    if exact_matches:
        return True, exact_matches[0]
    
    # If no exact match, try to find close matches
    close_matches = get_close_matches(brand.upper(), [b.upper() for b in available_brands], n=3, cutoff=0.6)
    if close_matches:
        # Get the original case for the matches
        original_case_matches = [b for b in available_brands if b.upper() in close_matches]
        return False, original_case_matches
    
    return False, []

# Custom CSS for the split screen layout
st.markdown("""
    <style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stChatFloatingInputContainer {
        bottom: 20px;
        background: transparent;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .user-message {
        background-color: #e6f3ff;
    }
    .assistant-message {
        background-color: #f0f0f0;
    }
    .dashboard-container iframe {
        width: 100%;
        border: none;
        height: calc(100vh - 100px);
    }
    </style>
""", unsafe_allow_html=True)

# Create two columns for split screen
chat_col, dashboard_col = st.columns(2)

# Chat interface (left side)
with chat_col:
    st.title("💬 Chat Interface")
    
    # Initialize analyzer if not already done
    if st.session_state.analyzer is None:
        try:
            st.session_state.analyzer = CompetitiveAnalysis(
                "Top Products - categories - sales-performance - amazon.com - 2024-02 - 2025-01.xlsx"
            )
            st.success("Data loaded successfully!")
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
    
    # Create a container for chat messages
    chat_container = st.container()
    
    # Display chat messages in the container
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Handle brand validation if needed
        if st.session_state.brand_validation:
            with st.chat_message("assistant"):
                st.markdown("Did you mean one of these brands?")
                cols = st.columns(len(st.session_state.brand_validation))
                for idx, brand in enumerate(st.session_state.brand_validation, 1):
                    if cols[idx-1].button(f"{idx}. {brand}", key=f"brand_{idx}"):
                        selected_brand = brand
                        st.session_state.brand_validation = None
                        
                        # Process the pending analysis with the selected brand
                        if st.session_state.pending_analysis:
                            analysis_type, competitors = st.session_state.pending_analysis
                            if analysis_type == "brand":
                                result = asyncio.run(st.session_state.analyzer.generate_competitive_dashboard(brand=selected_brand))
                            else:  # competitive
                                result = asyncio.run(st.session_state.analyzer.generate_competitive_dashboard(
                                    brand=selected_brand,
                                    competitors=competitors
                                ))
                            st.session_state.current_dashboard = result
                            st.session_state.pending_analysis = None
                            st.rerun()
                
                if st.button("Use original input"):
                    st.session_state.brand_validation = None
                    st.session_state.pending_analysis = None
                    st.rerun()
    
    # Chat input
    if prompt := st.chat_input("What would you like to analyze?"):
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Process the command
        with st.chat_message("assistant"):
            if "market overview" in prompt.lower() or "overview" in prompt.lower():
                status_msg = st.empty()
                status_msg.write("Generating market overview dashboard...")
                try:
                    result = asyncio.run(st.session_state.analyzer.generate_competitive_dashboard())
                    st.session_state.current_dashboard = result
                    status_msg.write("Dashboard generated successfully!")
                except Exception as e:
                    status_msg.error(f"Error generating dashboard: {str(e)}")
            
            elif "brand analysis" in prompt.lower():
                brand = prompt.split("brand analysis")[-1].strip()
                if not brand:
                    st.markdown("Please specify a brand name.")
                else:
                    # Validate brand name
                    is_exact, matches = validate_brand(brand, st.session_state.analyzer.available_brands)
                    if is_exact:
                        status_msg = st.empty()
                        status_msg.write(f"Generating brand analysis for {matches}...")
                        try:
                            result = asyncio.run(st.session_state.analyzer.generate_competitive_dashboard(brand=matches))
                            st.session_state.current_dashboard = result
                            status_msg.write("Dashboard generated successfully!")
                        except Exception as e:
                            status_msg.error(f"Error generating dashboard: {str(e)}")
                    elif matches:
                        st.session_state.brand_validation = matches
                        st.session_state.pending_analysis = ("brand", None)
                        st.rerun()
                    else:
                        st.error(f"Brand '{brand}' not found. Available brands:")
                        st.json(sorted(st.session_state.analyzer.available_brands))
            
            elif "competitive analysis" in prompt.lower():
                parts = prompt.split("competitive analysis")[-1].strip().split("vs")
                if len(parts) < 2:
                    st.markdown("Please specify your brand and competitors (e.g., 'competitive analysis BrandA vs BrandB, BrandC')")
                else:
                    brand = parts[0].strip()
                    competitors = [comp.strip() for comp in parts[1].split(",")]
                    
                    # Validate main brand first
                    is_exact, matches = validate_brand(brand, st.session_state.analyzer.available_brands)
                    if is_exact:
                        # Validate competitors
                        valid_competitors = []
                        invalid_competitors = []
                        for comp in competitors:
                            is_comp_exact, comp_matches = validate_brand(comp, st.session_state.analyzer.available_brands)
                            if is_comp_exact:
                                valid_competitors.append(comp_matches)
                            elif comp_matches:
                                st.session_state.brand_validation = comp_matches
                                st.session_state.pending_analysis = ("competitive", valid_competitors)
                                st.rerun()
                            else:
                                invalid_competitors.append(comp)
                        
                        if invalid_competitors:
                            st.error(f"Some competitors not found: {', '.join(invalid_competitors)}")
                            st.json(sorted(st.session_state.analyzer.available_brands))
                        else:
                            status_msg = st.empty()
                            status_msg.write(f"Generating competitive analysis for {matches} vs {', '.join(valid_competitors)}...")
                            try:
                                result = asyncio.run(st.session_state.analyzer.generate_competitive_dashboard(
                                    brand=matches,
                                    competitors=valid_competitors
                                ))
                                st.session_state.current_dashboard = result
                                status_msg.write("Dashboard generated successfully!")
                            except Exception as e:
                                status_msg.error(f"Error generating dashboard: {str(e)}")
                    elif matches:
                        st.session_state.brand_validation = matches
                        st.session_state.pending_analysis = ("competitive", competitors)
                        st.rerun()
                    else:
                        st.error(f"Brand '{brand}' not found. Available brands:")
                        st.json(sorted(st.session_state.analyzer.available_brands))
            
            else:
                st.markdown("""I can help you with:
                1. Market Overview - Get an overview of the entire market
                2. Brand Analysis - Analyze a specific brand (e.g., "brand analysis BrandName")
                3. Competitive Analysis - Compare brands (e.g., "competitive analysis BrandA vs BrandB, BrandC")
                """)
            
            # Add assistant response to chat history
            if not st.session_state.brand_validation:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "Dashboard generated successfully!" if st.session_state.current_dashboard else "How can I help you?"
                })

# Dashboard display (right side)
with dashboard_col:
    st.title("📊 Dashboard")
    
    if st.session_state.current_dashboard:
        # Extract the actual path from the result message
        if "dashboards/" in st.session_state.current_dashboard:
            dashboard_path = st.session_state.current_dashboard.split("dashboards/")[-1].split(".html")[0] + ".html"
            dashboard_path = os.path.join("dashboards", dashboard_path)
        else:
            # Try to find the most recent dashboard file
            dashboard_files = [f for f in os.listdir("dashboards") if f.endswith('.html')]
            if dashboard_files:
                dashboard_path = os.path.join("dashboards", sorted(dashboard_files)[-1])
            else:
                dashboard_path = None
        
        st.write(f"Debug - Dashboard path: {dashboard_path}")  # Debug info
        
        if dashboard_path and os.path.exists(dashboard_path):
            st.write(f"Debug - Dashboard file exists")  # Debug info
            with open(dashboard_path, 'r') as f:
                dashboard_html = f.read()
                st.write(f"Debug - Dashboard HTML length: {len(dashboard_html)}")  # Debug info
            
            # Ensure the dashboard HTML is properly embedded
            st.components.v1.html(
                dashboard_html,
                height=800,
                scrolling=True
            )
        else:
            st.warning(f"Dashboard file not found at: {dashboard_path}")
            st.write("Available files in dashboards directory:")
            if os.path.exists("dashboards"):
                files = os.listdir("dashboards")
                st.json([f for f in files if f.endswith('.html')])
            else:
                st.write("Dashboards directory does not exist")
    else:
        st.info("No dashboard generated yet. Use the chat interface to create one!")