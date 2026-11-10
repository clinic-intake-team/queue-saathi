"""Phase 1 UI skeleton; run with streamlit run app.py."""
import streamlit as st
from app_extract_v2 import extract_answer  # Shared all-row v2 backend; explicit opt-in required.

st.set_page_config(page_title='Clinic Queue Intake')
st.title('Clinic Queue Intake')
st.caption('Voice intake and summaries. No diagnosis or medical advice.')
patient, doctor = st.tabs(['Patient', 'Doctor'])
with patient:
    st.info('Patient intake flow will be added in Phase 4.')
with doctor:
    st.info('Doctor summaries will be added in Phase 4.')
