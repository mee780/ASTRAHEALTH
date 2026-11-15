# ASTRAHEALTH — deployable Streamlit prototype

This package contains a rebuilt, deploy-oriented version of the ASTRAHEALTH six-module prototype.

## Included modules
1. Dashboard
2. Physical Health (manual entry + SQLite history)
3. Mental Health (self-report form + SQLite history)
4. Radiation Monitoring (manual dose log; values are not sensor readings)
5. Health Pattern Analysis (transparent rule-based comparisons; **not a trained AI model**)
6. Health Reports (individual CSV exports + combined CSV)

## Run locally
Use Python 3.10 or newer.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud
1. Create a GitHub repository and upload `app.py`, `requirements.txt`, and `.streamlit/config.toml`.
2. Open https://share.streamlit.io/ and sign in with GitHub.
3. Choose **Create app**, select the repository, branch, and `app.py`.
4. Deploy. Streamlit will install packages from `requirements.txt`.

## Important storage note
The app stores entries in `astrahealth.db` using SQLite. This works for local testing and a single running instance. Streamlit Community Cloud's local filesystem is not a guaranteed permanent database: data can be lost when the app restarts, is redeployed, or its environment is replaced. For durable multi-user production use, connect a managed database such as Supabase/PostgreSQL before collecting important data.

## Data and safety boundaries
- The crew identity is fictional/demo by default.
- All readings are manually entered; no spacecraft, wearable, or radiation sensors are connected.
- Radiation totals are sums of user-entered values, not measured astronaut exposure or a safety limit.
- The analysis is a small set of illustrative Python rules, not machine learning, medical advice, diagnosis, or fitness-for-duty assessment.
- Do not enter real sensitive medical or mental-health information into this demonstration app.
- The project is not affiliated with or endorsed by NASA.
