#!/usr/bin/env bash
set -e


# load env file if present
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi


# start scheduler in background and then start streamlit
python -u -c "from app_utils.scheduler import start_scheduler; start_scheduler()" &


# run streamlit server
streamlit run app.py --server.port ${STREAMLIT_SERVER_PORT:-8501} --server.headless true