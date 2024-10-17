# parent img
FROM python:3.9-slim

# working directory in
WORKDIR /app

# copy current directory files into container
COPY . .

# install requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# expose and healthcheck streamlit port
EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# run streamlit app
ENTRYPOINT ["streamlit", "run", "sourcepage_analysis_streamlit.py", "--server.port=8501", "--server.address=0.0.0.0"]
