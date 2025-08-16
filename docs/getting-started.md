# Getting Started

Requirements
- Python 3.10+
- Optional dependencies per feature (see Usage Guide)

Install
```
pip install -r requirements.txt
# Optional: enable rendering
python -m playwright install chromium
```

Quick checks
- Run a simple fetch:
```
python -m crawler.cli urls https://example.com
```
- Run from catalog (optional raw + metrics):
```
export MINIO_ENDPOINT=http://localhost:9000
export MINIO_ACCESS_KEY=minio
export MINIO_SECRET_KEY=minio123
export MINIO_BUCKET=crawler
python -m crawler.cli run --source example-news --country MZ --max-pages 10 --write-raw --metrics-port 8000
```

Run tests
```
python -m unittest discover -v
```
