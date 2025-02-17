import streamlit as st
import asyncio
from competitive_analysis_agent import CompetitiveAnalysis
from pathlib import Path
import os

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
                    status_msg = st.empty()
                    status_msg.write(f"Generating brand analysis for {brand}...")
                    try:
                        result = asyncio.run(st.session_state.analyzer.generate_competitive_dashboard(brand=brand))
                        st.session_state.current_dashboard = result
                        status_msg.write("Dashboard generated successfully!")
                    except Exception as e:
                        status_msg.error(f"Error generating dashboard: {str(e)}")
            
            elif "competitive analysis" in prompt.lower():
                parts = prompt.split("competitive analysis")[-1].strip().split("vs")
                if len(parts) < 2:
                    st.markdown("Please specify your brand and competitors (e.g., 'competitive analysis BrandA vs BrandB, BrandC')")
                else:
                    brand = parts[0].strip()
                    competitors = [comp.strip() for comp in parts[1].split(",")]
                    status_msg = st.empty()
                    status_msg.write(f"Generating competitive analysis for {brand} vs {', '.join(competitors)}...")
                    try:
                        result = asyncio.run(st.session_state.analyzer.generate_competitive_dashboard(
                            brand=brand,
                            competitors=competitors
                        ))
                        st.session_state.current_dashboard = result
                        status_msg.write("Dashboard generated successfully!")
                    except Exception as e:
                        status_msg.error(f"Error generating dashboard: {str(e)}")
            
            else:
                st.markdown("""I can help you with:
                1. Market Overview - Get an overview of the entire market
                2. Brand Analysis - Analyze a specific brand (e.g., "brand analysis BrandName")
                3. Competitive Analysis - Compare brands (e.g., "competitive analysis BrandA vs BrandB, BrandC")
                """)
            
            # Add assistant response to chat history
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