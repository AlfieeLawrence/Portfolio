# Snowflake Badge 3 — Streamlit Smoothie App

## Overview
This project is a small Streamlit application connected to Snowflake. It allows a user to build a smoothie order, view nutrition information for selected ingredients, and submit the order back into a Snowflake table.

## What the App Does
- Reads available fruit options from `smoothies.public.fruit_options`
- Lets a user choose up to five ingredients
- Calls the Smoothie Froot API for nutrition details
- Inserts submitted orders into `smoothies.public.orders`

## Tech Stack
- Python
- Streamlit
- Snowflake
- Snowpark for Python
- Pandas
- Requests

## Project Files
- `streamlit_app.py` — main application
- `requirements.txt` — Python dependencies
- `.devcontainer/devcontainer.json` — development container configuration

## How to Run
### Prerequisites
- Python 3.11+
- Access to a Snowflake account
- A configured Streamlit Snowflake connection
- Existing Snowflake tables:
  - `smoothies.public.fruit_options`
  - `smoothies.public.orders`

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Configure Access
The app uses:
```python
st.connection('snowflake')
```

Configure a matching Streamlit connection in your local secrets or deployment environment before starting the app.

### Start the App
```bash
streamlit run streamlit_app.py
```

## Expected Outcome
- The page loads a list of fruit options from Snowflake
- Selecting ingredients displays nutrition information
- Clicking **Submit Order** writes the order to Snowflake

## Notes
- This project assumes the Snowflake schema and tables already exist
- The nutrition lookup depends on the external Smoothie Froot API being available
