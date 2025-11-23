#!/usr/bin/env python3
"""
Generate HTML report from test results
"""
import subprocess
import os
import shutil
from datetime import datetime

# Test results data from the test run
RESULTS_DATA = [
    {
        "name": "Professional Headshot",
        "number": "1/3",
        "processing_time": "18.0",
        "prompt": "professional headshot, studio lighting, sharp focus, cinematic, cinematic style, high quality, detailed",
        "style": "Cinematic",
        "original_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400",
        "generated_id": "ac7bcf91-cd83-4737-9d59-f7b981448a22"
    },
    {
        "name": "Portrait Enhancement",
        "number": "2/3",
        "processing_time": "12.2",
        "prompt": "beautiful portrait, natural lighting, high quality, professional photography, natural style, high quality, detailed",
        "style": "Natural",
        "original_url": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=400",
        "generated_id": "176367ce-5b2e-4161-a0ed-cbb50eee5af2"
    },
    {
        "name": "Business Professional",
        "number": "3/3",
        "processing_time": "12.2",
        "prompt": "corporate headshot, professional attire, office background, high resolution, corporate style, high quality, detailed",
        "style": "Corporate",
        "original_url": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=400",
        "generated_id": "9ad137e6-a81a-4db6-980b-3d7ef324dbe6"
    }
]

def download_images():
    """Download all images needed for the report"""
    print("📥 Downloading images for HTML report...")

    # Create directories
    os.makedirs("results_html/images", exist_ok=True)

    # Download generated images from GCS
    for i, result in enumerate(RESULTS_DATA, 1):
        gcs_path = f"gs://jhakaas-images-jhakaas-dev/generated/{result['generated_id']}.jpg"
        local_path = f"results_html/images/test{i}_generated.jpg"

        print(f"  Downloading test {i} generated image...")
        subprocess.run([
            '/opt/homebrew/share/google-cloud-sdk/bin/gcloud', 'storage', 'cp',
            gcs_path, local_path
        ], check=True, capture_output=True)

    # Download original images
    for i, result in enumerate(RESULTS_DATA, 1):
        local_path = f"results_html/images/test{i}_original.jpg"
        print(f"  Downloading test {i} original image...")
        subprocess.run([
            'curl', '-s', result['original_url'], '-o', local_path
        ], check=True, capture_output=True)

    print("✅ All images downloaded!")

def generate_test_html(result, test_num):
    """Generate HTML for a single test result"""
    return f'''
        <!-- Test {test_num}: {result['name']} -->
        <div class="test-result">
            <div class="test-header">
                <h2 class="test-title">{result['name']}</h2>
                <span class="test-number">Test {result['number']}</span>
            </div>

            <div class="image-comparison">
                <div class="image-container">
                    <div class="image-label">Original Image</div>
                    <div class="image-wrapper">
                        <img src="images/test{test_num}_original.jpg" alt="Original">
                    </div>
                </div>
                <div class="image-container">
                    <div class="image-label">AI Generated Image</div>
                    <div class="image-wrapper">
                        <img src="images/test{test_num}_generated.jpg" alt="Generated">
                    </div>
                </div>
            </div>

            <div class="metadata">
                <h3 class="metadata-title">Generation Metadata</h3>
                <div class="metadata-grid">
                    <div class="metadata-item">
                        <span class="metadata-label">Processing Time</span>
                        <span class="metadata-value"><span class="badge badge-success">{result['processing_time']} seconds</span></span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Model</span>
                        <span class="metadata-value">stabilityai/stable-diffusion-xl-base-1.0</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">VAE</span>
                        <span class="metadata-value">madebyollin/sdxl-vae-fp16-fix</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Inference Steps</span>
                        <span class="metadata-value"><span class="badge badge-info">20 steps</span></span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Guidance Scale</span>
                        <span class="metadata-value">7.5</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Resolution</span>
                        <span class="metadata-value">1024 × 1024</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Precision</span>
                        <span class="metadata-value">FP16</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Optimizations</span>
                        <span class="metadata-value">Attention Slicing + xFormers</span>
                    </div>
                </div>

                <div class="metadata-item" style="margin-top: 20px;">
                    <span class="metadata-label">Prompt</span>
                    <span class="metadata-value code">{result['prompt']}</span>
                </div>

                <div class="metadata-item" style="margin-top: 15px;">
                    <span class="metadata-label">Style</span>
                    <span class="metadata-value"><span class="badge badge-warning">{result['style']}</span></span>
                </div>
            </div>
        </div>
'''

def generate_html():
    """Generate the full HTML report"""
    print("🎨 Generating HTML report...")

    # Read the template
    with open('results_html/index.html', 'r') as f:
        template = f.read()

    print("✅ HTML report generated!")
    return "results_html/index.html"

def open_html(html_path):
    """Open HTML in default browser"""
    abs_path = os.path.abspath(html_path)
    file_url = f"file://{abs_path}"

    print(f"\n📊 Opening HTML report...")
    print(f"\n🌐 View the report at:")
    print(f"   {file_url}")

    # Open in default browser
    subprocess.run(['open', abs_path])

    return file_url

def main():
    """Main function to generate and open the HTML report"""
    print("\n╔═══════════════════════════════════════════════════════╗")
    print("║   GENERATING HTML TEST REPORT                        ║")
    print("╚═══════════════════════════════════════════════════════╝\n")

    try:
        # Download images
        download_images()

        # HTML is already generated, just get the path
        html_path = "results_html/index.html"

        # Open in browser
        file_url = open_html(html_path)

        print("\n✅ HTML report ready!")
        print(f"\n💡 To view again, open:")
        print(f"   {file_url}")

    except Exception as e:
        print(f"\n❌ Error generating HTML report: {e}")
        return 1

    return 0

def create_comparison_html(all_results, output_file):
    """Create a simple HTML comparison report from test results"""
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jhakaas Worker Test Results - {datetime.now().strftime('%Y-%m-%d %H:%M')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        h1 {{ color: #333; }}
        .test-group {{ background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .style-test {{ display: inline-block; margin: 10px; text-align: center; vertical-align: top; }}
        .style-test img {{ max-width: 200px; border: 2px solid #ddd; border-radius: 4px; }}
        .success {{ color: green; }}
        .failed {{ color: red; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 10px; }}
        td, th {{ padding: 8px; text-align: left; border: 1px solid #ddd; }}
        th {{ background: #f0f0f0; }}
    </style>
</head>
<body>
    <h1>Jhakaas Worker - Style Transfer Test Results</h1>
    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
"""

    for image_name, results in all_results.items():
        html_content += f"""
    <div class="test-group">
        <h2>Test Image: {image_name}</h2>
        <table>
            <tr>
                <th>Style</th>
                <th>Status</th>
                <th>Time (s)</th>
                <th>Preview</th>
            </tr>
"""
        for result in results:
            if result.get('success'):
                status_class = "success"
                status_text = "✅ SUCCESS"
                time_text = f"{result['time']:.1f}s"
                img_html = f'<img src="../images/{os.path.basename(result["image_path"])}" width="150">'
            else:
                status_class = "failed"
                status_text = "❌ FAILED"
                time_text = "-"
                error = result.get('error', 'Unknown error')
                img_html = f'<span style="color: red;">{error}</span>'

            html_content += f"""
            <tr>
                <td>{result['style']['name']}</td>
                <td class="{status_class}">{status_text}</td>
                <td>{time_text}</td>
                <td>{img_html}</td>
            </tr>
"""

        html_content += """
        </table>
    </div>
"""

    # Summary
    total_tests = sum(len(results) for results in all_results.values())
    successful_tests = sum(1 for results in all_results.values() for r in results if r.get('success'))

    html_content += f"""
    <div class="test-group">
        <h2>Summary</h2>
        <p>Total tests: {total_tests}</p>
        <p class="success">Successful: {successful_tests}</p>
        <p class="failed">Failed: {total_tests - successful_tests}</p>
    </div>
</body>
</html>
"""

    with open(output_file, 'w') as f:
        f.write(html_content)

    print(f"HTML report created: {output_file}")
    return output_file


if __name__ == "__main__":
    exit(main())
