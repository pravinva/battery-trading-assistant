# Running the Streamlit App Locally

## Quick Start

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Install streamlit if needed
pip install streamlit

# 3. Run the app
streamlit run app/app.py
```

## Features

✅ Energy Australia branded UI
✅ Professional blue/green color scheme
✅ Chat interface with message history
✅ Quick query buttons in sidebar
✅ Logo support (place logo.png in root)
✅ Responsive design

## Logo

Place your `logo.png` file in the project root directory.
The app will automatically use it if available.

## Troubleshooting

If agent import fails:
- Make sure scripts/02_agent_development_local.py exists
- Check that all dependencies are installed
- Verify Databricks credentials are configured

