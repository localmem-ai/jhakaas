# Worker Tests

Clean test plugin system for Cloud Run worker style transfer.

## Structure

```
tests/
├── config.py              # Test configuration
├── test_styles.py         # Main test script
├── test-images/           # Place test images here
├── results/               # Test outputs (gitignored)
│   ├── html/             # HTML reports
│   └── images/           # Generated images
└── utils/
    └── generate_html_report.py  # Report generator
```

## Quick Start

1. **Add test images** to `test-images/` folder:
   ```bash
   cp ~/my-portrait.jpg worker/tests/test-images/
   ```

2. **Run tests:**
   ```bash
   cd worker/tests
   python test_styles.py
   ```

3. **View results** in `results/html/test_report_*.html`

## How It Works

1. Reads all images from `test-images/` (.jpg, .jpeg, .png)
2. Uploads them to GCS temporary bucket
3. Calls Cloud Run worker API for each style
4. Downloads generated images to `results/images/`
5. Creates HTML comparison report in `results/html/`

## Configuration

Edit [config.py](config.py) to customize:
- `WORKER_URL` - Cloud Run worker URL
- `TEST_BUCKET` - GCS bucket for uploading test images
- `STYLES` - List of styles to test
- Output directories

## Requirements

- Python 3.8+ with `requests` and `Pillow`
- GCloud CLI authenticated (`gcloud auth login`)
- Access to Cloud Run worker service
- GCS bucket for temporary test image uploads

## Supported Styles

- Natural (minimal changes)
- Anime
- Cartoon
- Bollywood
- Cinematic
- Vintage
- Glamour

Configure in [config.py](config.py)
