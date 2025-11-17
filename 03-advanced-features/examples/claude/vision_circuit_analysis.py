#!/usr/bin/env python3
"""
Claude Vision API - Circuit Analysis

This script demonstrates using Claude's vision capabilities to analyze
circuit diagrams and schematics.

Features:
- Image encoding and upload
- Circuit component identification
- Value calculation and verification
- Design recommendations
- Troubleshooting suggestions

Usage:
    python vision_circuit_analysis.py
    python vision_circuit_analysis.py --image path/to/circuit.png
"""

import os
import base64
import argparse
from pathlib import Path
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def encode_image(image_path: str) -> tuple[str, str]:
    """
    Encode an image file to base64.

    Args:
        image_path: Path to image file

    Returns:
        Tuple of (base64_data, media_type)
    """
    # Determine media type from extension
    ext = Path(image_path).suffix.lower()
    media_types = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.webp': 'image/webp'
    }

    media_type = media_types.get(ext, 'image/png')

    # Read and encode image
    with open(image_path, 'rb') as f:
        image_data = base64.standard_b64encode(f.read()).decode('utf-8')

    return image_data, media_type


def analyze_circuit_image(image_path: str, question: str = None) -> dict:
    """
    Analyze a circuit diagram image with Claude's vision API.

    Args:
        image_path: Path to circuit image
        question: Optional specific question about the circuit

    Returns:
        Dictionary with analysis results
    """
    # Encode image
    image_data, media_type = encode_image(image_path)

    # Default question if none provided
    if question is None:
        question = """Analyze this circuit diagram in detail:

1. Identify all components (resistors, capacitors, ICs, etc.)
2. Describe the circuit topology and purpose
3. Calculate any component values if specifications are visible
4. Identify potential issues or improvements
5. Provide design recommendations

Be specific and technical."""

    # Create message with image
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",  # Vision-enabled model
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data
                        }
                    },
                    {
                        "type": "text",
                        "text": question
                    }
                ]
            }
        ]
    )

    # Extract response
    response_text = message.content[0].text

    return {
        "analysis": response_text,
        "usage": {
            "input_tokens": message.usage.input_tokens,
            "output_tokens": message.usage.output_tokens,
            "total_tokens": message.usage.input_tokens + message.usage.output_tokens
        },
        "cost": (message.usage.input_tokens / 1_000_000) * 3.00 +
                (message.usage.output_tokens / 1_000_000) * 15.00
    }


def analyze_circuit_text(circuit_description: str) -> dict:
    """
    Analyze a text-based circuit description.

    Args:
        circuit_description: Text description or ASCII schematic

    Returns:
        Dictionary with analysis results
    """
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": f"""Analyze this circuit description and provide:

1. Circuit topology and purpose
2. Component value verification
3. Design calculations review
4. Potential improvements
5. Troubleshooting tips

Circuit Description:
{circuit_description}"""
            }
        ]
    )

    response_text = message.content[0].text

    return {
        "analysis": response_text,
        "usage": {
            "input_tokens": message.usage.input_tokens,
            "output_tokens": message.usage.output_tokens,
            "total_tokens": message.usage.input_tokens + message.usage.output_tokens
        },
        "cost": (message.usage.input_tokens / 1_000_000) * 3.00 +
                (message.usage.output_tokens / 1_000_000) * 15.00
    }


def demo_text_analysis():
    """Demo analyzing text-based circuit descriptions."""
    print("\n" + "=" * 80)
    print("📋 TEXT-BASED CIRCUIT ANALYSIS")
    print("=" * 80)

    # Get LED circuit description
    circuit_dir = Path(__file__).parent.parent / "circuit-diagrams"
    led_circuit_path = circuit_dir / "led_circuit.txt"

    if not led_circuit_path.exists():
        print(f"⚠️  Circuit file not found: {led_circuit_path}")
        return

    with open(led_circuit_path, 'r') as f:
        circuit_text = f.read()

    print("\n📄 Analyzing LED Circuit Description...")
    print("-" * 80)

    result = analyze_circuit_text(circuit_text)

    print(f"\n🤖 Claude's Analysis:\n")
    print(result["analysis"])
    print("\n" + "-" * 80)
    print(f"📊 Tokens: {result['usage']['total_tokens']} | Cost: ${result['cost']:.6f}")


def demo_buck_converter_analysis():
    """Demo analyzing buck converter circuit."""
    print("\n" + "=" * 80)
    print("📋 BUCK CONVERTER ANALYSIS")
    print("=" * 80)

    circuit_dir = Path(__file__).parent.parent / "circuit-diagrams"
    buck_path = circuit_dir / "buck_converter.txt"

    if not buck_path.exists():
        print(f"⚠️  Circuit file not found: {buck_path}")
        return

    with open(buck_path, 'r') as f:
        circuit_text = f.read()

    # Ask specific question
    question = f"""Based on this buck converter design:

{circuit_text}

1. Verify the inductor and capacitor calculations are correct
2. Check if component ratings have adequate safety margins
3. Evaluate the efficiency estimate
4. Suggest any optimizations
5. Identify potential failure modes"""

    print("\n🔍 Asking specific questions about buck converter...")
    print("-" * 80)

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2048,
        messages=[{"role": "user", "content": question}]
    )

    print(f"\n🤖 Claude's Analysis:\n")
    print(message.content[0].text)
    print("\n" + "-" * 80)

    cost = (message.usage.input_tokens / 1_000_000) * 3.00 + \
           (message.usage.output_tokens / 1_000_000) * 15.00
    print(f"📊 Tokens: {message.usage.input_tokens + message.usage.output_tokens} | Cost: ${cost:.6f}")


def demo_design_verification():
    """Demo using Claude to verify circuit design."""
    print("\n" + "=" * 80)
    print("✅ DESIGN VERIFICATION")
    print("=" * 80)

    design_spec = """I need to design an LED circuit with these requirements:
- Supply voltage: 9V
- LED: Blue LED, Vf=3.2V, If=20mA
- Want maximum brightness without damaging LED

Please:
1. Calculate the required resistor value
2. Calculate power dissipation
3. Recommend resistor rating
4. Verify the design is safe
5. Suggest any improvements"""

    print("\n📝 Design Specification:")
    print(design_spec)
    print("\n" + "-" * 80)
    print("🔍 Sending to Claude for verification...")

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[{"role": "user", "content": design_spec}]
    )

    print(f"\n🤖 Claude's Design Verification:\n")
    print(message.content[0].text)
    print("\n" + "-" * 80)

    cost = (message.usage.input_tokens / 1_000_000) * 3.00 + \
           (message.usage.output_tokens / 1_000_000) * 15.00
    print(f"📊 Tokens: {message.usage.input_tokens + message.usage.output_tokens} | Cost: ${cost:.6f}")


def main():
    """Main demonstration."""
    parser = argparse.ArgumentParser(
        description="Claude Vision API - Circuit Analysis"
    )
    parser.add_argument(
        "--image",
        type=str,
        help="Path to circuit image to analyze"
    )
    parser.add_argument(
        "--question",
        type=str,
        help="Specific question about the circuit"
    )

    args = parser.parse_args()

    print("\n" + "👁️  " + "=" * 76 + " 👁️")
    print("    CLAUDE VISION API - CIRCUIT ANALYSIS DEMO")
    print("👁️  " + "=" * 76 + " 👁️")

    try:
        if args.image:
            # Analyze user-provided image
            print(f"\n📸 Analyzing image: {args.image}")
            print("-" * 80)

            result = analyze_circuit_image(args.image, args.question)

            print(f"\n🤖 Claude's Analysis:\n")
            print(result["analysis"])
            print("\n" + "-" * 80)
            print(f"📊 Tokens: {result['usage']['total_tokens']} | Cost: ${result['cost']:.6f}")

        else:
            # Run demo analyses
            demo_text_analysis()
            demo_buck_converter_analysis()
            demo_design_verification()

            # Show summary
            print("\n" + "=" * 80)
            print("💡 KEY FEATURES")
            print("=" * 80)
            print("""
Claude's vision API can:
  ✅ Analyze circuit schematics and PCB layouts
  ✅ Identify components and read values
  ✅ Verify calculations and design choices
  ✅ Provide troubleshooting suggestions
  ✅ Recommend improvements and optimizations

Supported formats:
  • PNG, JPEG, GIF, WebP images
  • Text descriptions and ASCII schematics
  • Mixed image + text queries
  • Multi-turn conversations with images

Use cases:
  • Design review and verification
  • Component identification
  • Troubleshooting and debugging
  • Educational explanations
  • Documentation generation
            """)
            print("=" * 80)

            print("\n📝 To analyze your own circuit image:")
            print("  python vision_circuit_analysis.py --image path/to/circuit.png")
            print("  python vision_circuit_analysis.py --image circuit.jpg --question 'What is wrong with this design?'")
            print()

    except FileNotFoundError as e:
        print(f"\n❌ Error: File not found - {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have set ANTHROPIC_API_KEY in .env")


if __name__ == "__main__":
    main()
