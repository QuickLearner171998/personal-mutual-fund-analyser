#!/bin/bash
# Fix OpenMP crash and run Streamlit

export KMP_DUPLICATE_LIB_OK=TRUE

echo "Starting MF Portfolio Bot..."
streamlit run app.py
