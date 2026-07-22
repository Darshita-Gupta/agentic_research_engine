import os
import asyncio
import streamlit as st
from langchain_core.messages import AIMessage, ToolMessage, SystemMessage, BaseMessage
from src.graph import app
import src.config

# Set up page configurations
st.set_page_config(
    page_title="Scientific Paper Agent Console",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# CUSTOM THEMING & STYLES (GLASSMORPHISM / DARK THEME)
# ==========================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

/* Main font styling */
html, body, [class*="st-"], .stMarkdown {
    font-family: 'Outfit', sans-serif !important;
}

/* Glassmorphic cards for logs and summaries */
.glass-card {
    background: rgba(30, 41, 59, 0.55);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 20px 24px;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    margin-bottom: 24px;
}

.gradient-title {
    background: linear-gradient(135deg, #a5f3fc 0%, #38bdf8 50%, #6366f1 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 700;
    font-size: 2.5em;
    margin-bottom: 10px;
}

/* API status badges */
.badge {
    padding: 5px 12px;
    border-radius: 20px;
    font-size: 0.85em;
    font-weight: 600;
    display: inline-block;
    border: 1px solid;
}
.badge-ok {
    background-color: rgba(16, 185, 129, 0.15);
    color: #10b981;
    border-color: rgba(16, 185, 129, 0.3);
}
.badge-missing {
    background-color: rgba(239, 68, 68, 0.15);
    color: #ef4444;
    border-color: rgba(239, 68, 68, 0.3);
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# SIDEBAR PANEL & API STATUS
# ==========================================
st.sidebar.markdown("<h2 style='margin-bottom:0;'>🔬 Agent Settings</h2>", unsafe_allow_html=True)
st.sidebar.markdown("Configure and inspect API connections.")

# Verify key configurations
groq_key = os.environ.get("GROQ_API_KEY", "")
core_key = os.environ.get("CORE_API_KEY", "")

groq_ok = (groq_key != "DUMMY_KEY_PLACEHOLDER" and len(groq_key) > 0)
core_ok = (len(core_key) > 0)

st.sidebar.markdown("### API Connection Status")

def render_status(label, is_ok):
    badge_class = "badge-ok" if is_ok else "badge-missing"
    status_text = "Connected" if is_ok else "Missing"
    st.sidebar.markdown(f"**{label}** <span class='badge {badge_class}'>{status_text}</span>", unsafe_allow_html=True)

render_status("Groq (Llama 3.3)", groq_ok)
render_status("CORE search API", core_ok)

st.sidebar.markdown("---")
st.sidebar.markdown("### Test Queries")
# Add quick links to select test inputs
example_queries = [
    "Download and summarize the findings of this paper: https://pmc.ncbi.nlm.nih.gov/articles/PMC11379842/pdf/11671_2024_Article_4070.pdf",
    "Can you find 8 papers on quantum machine learning?",
    "Find recent papers (2023-2024) about CRISPR applications in treating genetic disorders, focusing on clinical trials and safety protocols",
    "Find and analyze papers from 2023-2024 about the application of transformer architectures in protein folding prediction, specifically looking for novel architectural modifications with experimental validation."
]

selected_example = st.sidebar.selectbox("Load sample query:", ["Select one..."] + example_queries)

st.sidebar.markdown("<br><br><small style='color:gray;'>Powered by LangGraph, Streamlit, and uv</small>", unsafe_allow_html=True)

# ==========================================
# MAIN PAGE HEADER
# ==========================================
st.markdown("<h1 class='gradient-title'>Scientific Paper Agent</h1>", unsafe_allow_html=True)
st.markdown("An intelligent research assistant that helps retrieve, analyze, and synthesize scientific literature using LangGraph and Groq.")

# Set up target input box
query_input = ""
if selected_example != "Select one...":
    query_input = selected_example

user_query = st.text_area("Enter your research query or question:", value=query_input, height=100, placeholder="E.g., Can you find 8 papers on quantum machine learning?")

# Setup verification alerts before running
run_disabled = not (groq_ok and core_ok)
if run_disabled:
    st.warning("Please configure your API keys in the '.env' file to unlock execution.")

# ==========================================
# REAL-TIME EXECUTION ORCHESTRATOR
# ==========================================
if st.button("Launch Research Agent", disabled=run_disabled):
    if not user_query.strip():
        st.error("Please enter a valid query first.")
    else:
        # Containers for streaming status
        progress_bar = st.progress(0)
        status_message = st.empty()
        
        st.markdown("### ⚙️ Workflow Timeline")
        timeline_container = st.container()
        
        # Helper to execute the async astream inside sync Streamlit
        async def stream_orchestrator():
            all_messages = []
            step = 0
            
            async for chunk in app.astream({"messages": [user_query]}, stream_mode="updates"):
                step += 1
                progress_bar.progress(min(step * 15, 100))
                
                for node_name, updates in chunk.items():
                    # Format node name nicely
                    node_title = node_name.replace("_", " ").title()
                    
                    with timeline_container:
                        with st.expander(f"🔹 Step {step}: Node `{node_title}` Completed", expanded=True):
                            # Display status/progress logs
                            if "messages" in updates:
                                for msg in updates["messages"]:
                                    all_messages.append(msg)
                                    
                                    # Print agent message details
                                    if isinstance(msg, AIMessage):
                                        if msg.content:
                                            st.markdown(f"**Agent Thought:**\n{msg.content}")
                                        if msg.tool_calls:
                                            for tc in msg.tool_calls:
                                                st.info(f"🛠️ **Requesting Tool Call:** `{tc['name']}` with arguments: `{tc['args']}`")
                                    
                                    # Print tool response details
                                    elif isinstance(msg, ToolMessage):
                                        st.success(f"📥 **Tool `{msg.name}` Response:**")
                                        # Decode/truncate long text for safety
                                        try:
                                            preview_data = json.loads(msg.content)
                                            if isinstance(preview_data, str) and len(preview_data) > 1000:
                                                preview_data = preview_data[:1000] + "..."
                                            st.json(preview_data)
                                        except:
                                            text_data = str(msg.content)
                                            if len(text_data) > 1000:
                                                text_data = text_data[:1000] + "..."
                                            st.code(text_data)
                                            
                                    elif isinstance(msg, SystemMessage):
                                        st.text(f"System Message: {msg.content}")
                            
                            # Log other state flags
                            state_flags = {k: v for k, v in updates.items() if k != "messages"}
                            if state_flags:
                                st.write("State Updates:", state_flags)

            return all_messages

        # Run the async loop
        try:
            status_message.info("Agent is planning research strategies... (Waiting for Groq/Gemini calls)")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            messages_history = loop.run_until_complete(stream_orchestrator())
            loop.close()
            
            progress_bar.progress(100)
            status_message.success("Research completed successfully!")
            
            # Display Final Answer Section
            st.markdown("---")
            st.markdown("<h2 style='color:#38bdf8;'>📝 Final Research Summary</h2>", unsafe_allow_html=True)
            
            # Find last AIMessage content that represents the final output
            final_content = None
            for msg in reversed(messages_history):
                if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
                    final_content = msg.content
                    break
                    
            if final_content:
                st.markdown(f"<div class='glass-card'>{final_content}</div>", unsafe_allow_html=True)
            else:
                st.warning("Could not isolate a clean final text response from the message history.")
                
        except Exception as e:
            status_message.error(f"Execution Error: {e}")
            progress_bar.empty()
