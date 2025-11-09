# Add Multi-Agent Supervisor support to Streamlit app

# Add this function after load_agent
@st.cache_resource
def load_supervisor(_file_mtime, _force_reload=False):
    """Load Multi-Agent Supervisor lazily"""
    SUPERVISOR_AVAILABLE = False
    SUPERVISOR_ERROR = None
    supervisor = None
    
    try:
        supervisor_script_path = Path(__file__).parent.parent / "scripts" / "02_agent_supervisor.py"
        if supervisor_script_path.exists():
            import sys
            import importlib
            # Clear cached modules
            modules_to_remove = [k for k in sys.modules.keys() if 'supervisor' in k.lower() or 'agents' in k.lower()]
            for mod in modules_to_remove:
                if mod in sys.modules:
                    del sys.modules[mod]
            
            importlib.invalidate_caches()
            
            spec = importlib.util.spec_from_file_location("supervisor_module", supervisor_script_path)
            supervisor_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(supervisor_module)
            
            supervisor = supervisor_module.supervisor
            SUPERVISOR_AVAILABLE = True
        else:
            SUPERVISOR_ERROR = f"Supervisor script not found at {supervisor_script_path}"
    except Exception as e:
        SUPERVISOR_AVAILABLE = False
        SUPERVISOR_ERROR = str(e)
    
    return SUPERVISOR_AVAILABLE, supervisor, SUPERVISOR_ERROR

