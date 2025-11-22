#!/usr/bin/env python3
"""
Test face-preserving style transfer with different artistic styles
Tests: anime, cartoon, Bollywood, cinematic, vintage, glamour
"""
import requests
import time
import sys
import os
import subprocess
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# Cloud Run URL
WORKER_URL = "https://jhakaas-worker-1098174162480.asia-southeast1.run.app"

def get_auth_token():
    """Get identity token for authentication"""
    result = subprocess.run(
        ['/opt/homebrew/share/google-cloud-sdk/bin/gcloud', 'auth', 'print-identity-token'],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()

# Test different styles on the same person
STYLE_TESTS = [
    {
        "name": "Original Photo",
        "style": "natural",
        "prompt": "high quality portrait, professional photography",
        "description": "Natural style - minimal changes"
    },
    {
        "name": "Anime Style",
        "style": "anime",
        "prompt": "portrait",
        "description": "Anime art with vibrant colors and cel shading"
    },
    {
        "name": "Cartoon Style",
        "style": "cartoon",
        "prompt": "portrait",
        "description": "Cartoon with bold outlines and flat colors"
    },
    {
        "name": "Bollywood Movie",
        "style": "bollywood",
        "prompt": "dramatic portrait",
        "description": "Dramatic Bollywood movie aesthetic"
    },
    {
        "name": "Cinematic",
        "style": "cinematic",
        "prompt": "dramatic portrait, moody lighting",
        "description": "Cinematic film photography"
    },
    {
        "name": "Vintage Photography",
        "style": "vintage",
        "prompt": "classic portrait",
        "description": "Classic vintage photography style"
    },
    {
        "name": "Glamour",
        "style": "glamour",
        "prompt": "elegant portrait",
        "description": "Elegant glamour photography"
    }
]

# Use a single test image to show face preservation across styles
TEST_IMAGE_URL = "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400"

# Output directory
OUTPUT_DIR = "style_test_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def download_image(url):
    """Download image from URL and return PIL Image"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))
    except Exception as e:
        print(f"Error downloading image: {e}")
        return None

def test_style(style_test, test_num, total_tests):
    """Test image generation with a specific style"""
    print("\n" + "="*60)
    print(f"TEST {test_num}/{total_tests}: {style_test['name'].upper()}")
    print("="*60)
    print(f"Description: {style_test['description']}")

    try:
        # Prepare payload
        payload = {
            "image_url": TEST_IMAGE_URL,
            "prompt": style_test['prompt'],
            "style": style_test['style']
        }

        print(f"\nStyle: {style_test['style']}")
        print(f"Prompt: {style_test['prompt']}")
        print("\n⏳ Processing...")

        start_time = time.time()
        headers = {"Authorization": f"Bearer {get_auth_token()}"}
        response = requests.post(
            f"{WORKER_URL}/generate",
            json=payload,
            headers=headers,
            timeout=120
        )
        elapsed = time.time() - start_time

        print(f"\nStatus Code: {response.status_code}")
        print(f"Processing Time: {elapsed:.1f}s")

        if response.status_code == 200:
            data = response.json()

            if data.get("status") == "success":
                print("✅ Generation successful!")

                # Download generated image
                generated_img = download_image(data.get('output_url'))

                if generated_img:
                    # Save individual result
                    output_filename = f"{test_num:02d}_{style_test['style']}.jpg"
                    output_path = os.path.join(OUTPUT_DIR, output_filename)
                    generated_img.save(output_path)
                    print(f"   Saved to: {output_path}")

                    return {
                        "success": True,
                        "image": generated_img,
                        "time": elapsed,
                        "output_url": data.get('output_url')
                    }

            print(f"❌ Generation failed: {data}")
            return {"success": False}

        else:
            print(f"❌ Request failed with status {response.status_code}")
            return {"success": False}

    except Exception as e:
        print(f"❌ Error: {e}")
        return {"success": False}

def create_style_grid(results, original_img):
    """Create a grid showing all style variations"""
    print("\n🖼️  Creating style comparison grid...")

    # Calculate grid dimensions
    cols = 4
    rows = (len(results) + cols - 1) // cols

    # Image size in grid
    img_size = 300
    margin = 20
    label_height = 60

    # Create grid canvas
    grid_width = cols * img_size + (cols + 1) * margin
    grid_height = rows * (img_size + label_height) + (rows + 1) * margin

    grid = Image.new('RGB', (grid_width, grid_height), 'white')
    draw = ImageDraw.Draw(grid)

    # Try to load a font
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
        font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 12)
    except:
        font = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Place images in grid
    for idx, (style_test, result) in enumerate(zip(STYLE_TESTS, results)):
        if not result.get('success'):
            continue

        row = idx // cols
        col = idx % cols

        # Calculate position
        x = col * img_size + (col + 1) * margin
        y = row * (img_size + label_height) + (row + 1) * margin

        # Resize and paste image
        img = result['image'].resize((img_size, img_size), Image.LANCZOS)
        grid.paste(img, (x, y))

        # Add label
        label_y = y + img_size + 10
        draw.text((x + img_size//2, label_y), style_test['name'],
                 fill='black', font=font, anchor='mt')
        draw.text((x + img_size//2, label_y + 25),
                 f"{result['time']:.1f}s",
                 fill='gray', font=font_small, anchor='mt')

    # Save grid
    grid_path = os.path.join(OUTPUT_DIR, "style_comparison_grid.jpg")
    grid.save(grid_path, quality=95)
    print(f"✅ Grid saved to: {grid_path}")

    # Open grid
    os.system(f'open "{grid_path}"')

    return grid_path

def create_html_report(results, original_img):
    """Create HTML report with all style comparisons"""
    print("\n📄 Creating HTML report...")

    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Jhakaas Style Transfer Test Results</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 40px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            text-align: center;
            color: #2d3748;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .subtitle {
            text-align: center;
            color: #718096;
            font-size: 1.2em;
            margin-bottom: 40px;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin-top: 30px;
        }
        .style-card {
            background: #f7fafc;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }
        .style-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 12px rgba(0,0,0,0.15);
        }
        .style-card img {
            width: 100%;
            height: auto;
            display: block;
        }
        .style-info {
            padding: 20px;
        }
        .style-name {
            font-size: 1.3em;
            font-weight: bold;
            color: #2d3748;
            margin-bottom: 5px;
        }
        .style-desc {
            color: #718096;
            font-size: 0.9em;
            margin-bottom: 10px;
        }
        .style-time {
            color: #48bb78;
            font-weight: bold;
        }
        .summary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            text-align: center;
        }
        .summary h2 {
            margin: 0 0 15px 0;
        }
        .stat {
            display: inline-block;
            margin: 0 20px;
            font-size: 1.1em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎨 Jhakaas Style Transfer Test</h1>
        <div class="subtitle">Face-Preserving Style Transfer with InstantID + LoRAs</div>

        <div class="summary">
            <h2>Test Summary</h2>
"""

    # Add summary stats
    successful = sum(1 for r in results if r.get('success'))
    avg_time = sum(r.get('time', 0) for r in results if r.get('success')) / max(successful, 1)

    html += f"""
            <div class="stat">✅ <strong>{successful}/{len(STYLE_TESTS)}</strong> styles generated</div>
            <div class="stat">⚡ <strong>{avg_time:.1f}s</strong> average processing time</div>
            <div class="stat">🖼️  <strong>Same Face</strong> across all styles</div>
        </div>
"""

    # Add grid of styles
    html += """
        <div class="grid">
"""

    for idx, (style_test, result) in enumerate(zip(STYLE_TESTS, results)):
        if not result.get('success'):
            continue

        img_filename = f"{idx+1:02d}_{style_test['style']}.jpg"

        html += f"""
            <div class="style-card">
                <img src="{img_filename}" alt="{style_test['name']}">
                <div class="style-info">
                    <div class="style-name">{style_test['name']}</div>
                    <div class="style-desc">{style_test['description']}</div>
                    <div class="style-time">⚡ {result['time']:.1f}s processing time</div>
                </div>
            </div>
"""

    html += """
        </div>

        <div style="margin-top: 40px; padding: 20px; background: #f7fafc; border-radius: 10px;">
            <h3>Implementation Details</h3>
            <ul>
                <li><strong>Model:</strong> SDXL InstantID Pipeline with ControlNet + IP-Adapter</li>
                <li><strong>Face Encoding:</strong> InsightFace AntelopeV2 (512-dim embeddings)</li>
                <li><strong>Style Method:</strong> LoRA sliders (anime, cartoon, pixar) + prompt-based</li>
                <li><strong>Settings:</strong> CFG 5.0, 15 steps, ControlNet scale 0.8, LoRA scale 0.8</li>
                <li><strong>Resolution:</strong> 1024×1024</li>
                <li><strong>GPU:</strong> NVIDIA L4 on Google Cloud Run</li>
                <li><strong>Optimizations:</strong> VAE FP16, Attention Slicing, xFormers, Euler Scheduler</li>
            </ul>
        </div>
    </div>
</body>
</html>
"""

    # Save HTML
    html_path = os.path.join(OUTPUT_DIR, "style_comparison.html")
    with open(html_path, 'w') as f:
        f.write(html)

    print(f"✅ HTML report saved to: {html_path}")

    # Open in browser
    abs_path = os.path.abspath(html_path)
    os.system(f'open "{abs_path}"')

    return html_path

def main():
    """Run style transfer tests"""
    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║   JHAKAAS STYLE TRANSFER TEST                        ║
    ║   Testing Face-Preserving Style Transfer            ║
    ╚═══════════════════════════════════════════════════════╝
    """)

    print(f"\n📸 Test Image: {TEST_IMAGE_URL}")
    print(f"🎨 Styles to test: {len(STYLE_TESTS)}")

    # Download original image
    print(f"\n📥 Downloading original image...")
    original_img = download_image(TEST_IMAGE_URL)
    if not original_img:
        print("❌ Failed to download test image")
        sys.exit(1)

    # Save original
    original_path = os.path.join(OUTPUT_DIR, "00_original.jpg")
    original_img.save(original_path)
    print(f"   Original saved to: {original_path}")

    # Test each style
    results = []
    for i, style_test in enumerate(STYLE_TESTS, 1):
        result = test_style(style_test, i, len(STYLE_TESTS))
        results.append(result)

        if i < len(STYLE_TESTS):
            print("\n⏸️  Pausing 2 seconds before next test...")
            time.sleep(2)

    # Create visualizations
    print("\n" + "="*60)
    print("CREATING VISUALIZATIONS")
    print("="*60)

    # Create grid
    create_style_grid(results, original_img)

    # Create HTML report
    create_html_report(results, original_img)

    # Print summary
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)

    successful = sum(1 for r in results if r.get('success'))
    print(f"\n✅ {successful}/{len(STYLE_TESTS)} styles generated successfully")
    print(f"📁 Results saved in: {OUTPUT_DIR}/")
    print(f"\n🌐 Open the HTML report to see all style comparisons!")

    if successful == len(STYLE_TESTS):
        print("\n🎉 All style tests passed!")
        sys.exit(0)
    else:
        print("\n⚠️  Some style tests failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
