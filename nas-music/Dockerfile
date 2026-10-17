FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY library.py server.py mcp_pipe.py ./
RUN useradd --uid 10001 --create-home music
USER music
EXPOSE 8765
CMD ["python", "mcp_pipe.py", "server.py"]
