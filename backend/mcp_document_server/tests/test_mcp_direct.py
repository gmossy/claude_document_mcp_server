#!/usr/bin/env python3
"""
Direct test of MCP server without inspector.
This tests if the server itself is working by spawning a subprocess that
runs the current Python interpreter against document_mcp_server.py in this repo.
"""

import subprocess
import json
import sys
from pathlib import Path

def test_server():
    """Test the MCP server directly via stdio."""

    print("🧪 Testing MCP Server Directly")
    print("=" * 50)

    # Start the server using the current interpreter from the mcp_document_server dir
    # __file__ is in backend/mcp_document_server/tests, so we go up one level
    repo_root = Path(__file__).resolve().parent.parent  # backend/mcp_document_server
    server_path = sys.executable
    script_path = str(repo_root / "document_mcp_server.py")

    print(f"\n1. Starting server: {server_path} {script_path}")

    success = False
    try:
        process = subprocess.Popen(
            [server_path, script_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(repo_root),
        )

        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0",
                },
            },
        }

        print("\n2. Sending initialize request...")
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()

        # Read response
        print("\n3. Reading response...")
        response = process.stdout.readline()

        if response:
            print("\n✅ Server responded!")
            print(f"Response: {response[:200]}...")

            # Parse and check
            try:
                resp_data = json.loads(response)
                if "result" in resp_data:
                    print("\n✅ Server initialized successfully!")
                    print(
                        f"Server name: {resp_data['result'].get('serverInfo', {}).get('name')}"
                    )
                    print(
                        f"Protocol version: {resp_data['result'].get('protocolVersion')}"
                    )
                    success = True
                else:
                    print(f"\n❌ Unexpected response: {resp_data}")
            except json.JSONDecodeError as e:
                print(f"\n❌ Invalid JSON response: {e}")
        else:
            print("\n❌ No response from server")
            stderr = process.stderr.read()
            if stderr:
                print(f"Error output: {stderr}")

        process.terminate()
        assert success, "Server did not respond correctly to initialize"

    except Exception as e:
        print(f"\n❌ Error testing server: {e}")
        import traceback
        traceback.print_exc()
        assert False, f"Error testing server: {e}"

if __name__ == "__main__":
    success = test_server()
    sys.exit(0 if success else 1)
