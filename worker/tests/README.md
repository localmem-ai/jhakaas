# Worker Tests

Test suite for validating AI worker functionality and deployment.

## Test Files

- **test_worker.py** - Unit tests for worker endpoints and model manager
- **test_cloud_run.py** - Integration tests for deployed Cloud Run service
- **test_styles.py** - Comprehensive style transfer testing with HTML report generation

## Utilities

- **utils/generate_html_report.py** - Creates visual comparison reports for style transfer results

## Running Tests

### Unit Tests
```bash
pytest worker/tests/test_worker.py
```

### Cloud Run Integration Tests
```bash
python worker/tests/test_cloud_run.py
```

### Style Transfer Tests
```bash
python worker/tests/test_styles.py
```
This generates an HTML report in `results_html/` with visual comparisons of all style transfers.

## Test Images

Test images should be placed in the project root or specified via command line arguments.
