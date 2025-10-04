#!/usr/bin/env python3
import json
import requests
import sys

def call_api(input_file: str, output_file: str = "result.json", api_url: str = "http://localhost:8000/api/v1/articles/analyze"):
    """
    Call the trust API with the input JSON and save the output.

    Args:
        input_file: Path to the input JSON file
        output_file: Path to save the output JSON file
        api_url: URL of the API endpoint
    """
    # Load input data
    with open(input_file, 'r') as f:
        input_data = json.load(f)

    print(f"Calling API at {api_url}...")
    print(f"Input data: {json.dumps(input_data, indent=2)}")

    try:
        # Call the API
        response = requests.post(api_url, json=input_data)
        response.raise_for_status()

        # Get the result
        result = response.json()

        # Save to output file
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=4)

        print(f"\nSuccess! Output saved to {output_file}")
        print(f"Result: {json.dumps(result, indent=2)}")

    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to {api_url}")
        print("Make sure the API server is running.")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"Error: API returned status {response.status_code}")
        print(f"Response: {response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Call the trust API with input data")
    parser.add_argument("-i", "--input", default="test/input.json",
                        help="Path to input JSON file (default: test/input.json)")
    parser.add_argument("-o", "--output", default="result.json",
                        help="Path to output JSON file (default: result.json)")
    parser.add_argument("-u", "--url", default="http://localhost:8000/api/v1/articles/analyze",
                        help="API endpoint URL (default: http://localhost:8000/api/v1/articles/analyze)")

    args = parser.parse_args()

    call_api(args.input, args.output, args.url)
