#!/usr/bin/env python3
"""
Test MCP Server Transport Connectivity

This script tests the MCP server's stdio transport by:
1. Starting the server as a subprocess
2. Sending an initialize request
3. Verifying the response
4. Testing tool listing
"""

import subprocess
import json
import sys
import time
from pathlib import Path

def test_mcp_server():
    """Test MCP server connectivity via stdio transport."""
    
    print("🧪 Testing MCP Server Transport Connectivity")
    print("=" * 60)
    
    # Find the server script
    repo_root = Path(__file__).resolve().parent.parent
    server_script = repo_root / "backend" / "mcp_document_server" / "document_mcp_server.py"
    
    if not server_script.exists():
        print(f"❌ Server script not found: {server_script}")
        return False
    
    print(f"\n1. Server Script: {server_script}")
    
    # Check if uv is available
    import shutil
    uv_path = shutil.which("uv")
    if uv_path:
        print(f"   Using uv: {uv_path}")
        cmd = [
            uv_path, "run", "--project",
            str(repo_root / "backend" / "mcp_document_server"),
            "python", str(server_script)
        ]
    else:
        print("   ⚠️  uv not found, trying direct python")
        cmd = [sys.executable, str(server_script)]
    
    print(f"\n2. Starting server: {' '.join(cmd)}")
    
    try:
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            cwd=str(repo_root / "backend" / "mcp_document_server"),
        )
        
        # Give server a moment to start
        time.sleep(0.5)
        
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
        
        print("\n3. Sending initialize request...")
        request_json = json.dumps(init_request) + "\n"
        process.stdin.write(request_json)
        process.stdin.flush()
        
        # Read response with timeout
        print("4. Waiting for response...")
        response_line = None
        for _ in range(10):  # Try for up to 5 seconds
            if process.stdout.readable():
                try:
                    response_line = process.stdout.readline()
                    if response_line.strip():
                        break
                except:
                    pass
            time.sleep(0.5)
        
        if not response_line or not response_line.strip():
            # Check stderr for errors
            stderr_output = ""
            try:
                process.stderr.readable()
                stderr_output = process.stderr.read()
            except:
                pass
            
            if stderr_output:
                print(f"\n❌ Server error output:")
                print(stderr_output[:500])
            
            process.terminate()
            print("\n❌ No response from server")
            return False
        
        print(f"\n✅ Server responded!")
        print(f"   Response length: {len(response_line)} bytes")
        
        # Parse response
        try:
            resp_data = json.loads(response_line.strip())
            
            if "result" in resp_data:
                server_info = resp_data["result"].get("serverInfo", {})
                print(f"\n✅ Server initialized successfully!")
                print(f"   Server name: {server_info.get('name', 'unknown')}")
                print(f"   Server version: {server_info.get('version', 'unknown')}")
                print(f"   Protocol version: {resp_data['result'].get('protocolVersion', 'unknown')}")
                
                # Check capabilities
                capabilities = resp_data["result"].get("capabilities", {})
                if "tools" in capabilities:
                    print(f"   Tools available: {capabilities['tools'].get('listChanged', False)}")
                
                # Test tools/list
                print("\n5. Testing tools/list...")
                tools_request = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                }
                
                process.stdin.write(json.dumps(tools_request) + "\n")
                process.stdin.flush()
                
                time.sleep(0.5)
                tools_response = process.stdout.readline()
                
                if tools_response:
                    tools_data = json.loads(tools_response.strip())
                    if "result" in tools_data:
                        tools = tools_data["result"].get("tools", [])
                        print(f"   ✅ Found {len(tools)} tools")
                        for tool in tools[:5]:  # Show first 5
                            print(f"      - {tool.get('name', 'unknown')}")
                        if len(tools) > 5:
                            print(f"      ... and {len(tools) - 5} more")
                    else:
                        print(f"   ⚠️  Unexpected response: {tools_data}")
                else:
                    print("   ⚠️  No response to tools/list")
                
                process.terminate()
                return True
            else:
                print(f"\n❌ Unexpected response structure: {resp_data}")
                process.terminate()
                return False
                
        except json.JSONDecodeError as e:
            print(f"\n❌ Invalid JSON response: {e}")
            print(f"   Response: {response_line[:200]}")
            process.terminate()
            return False
            
    except Exception as e:
        print(f"\n❌ Error testing server: {e}")
        import traceback
        traceback.print_exc()
        try:
            process.terminate()
        except:
            pass
        return False

if __name__ == "__main__":
    success = test_mcp_server()
    print("\n" + "=" * 60)
    if success:
        print("✅ MCP Server Transport Test: PASSED")
    else:
        print("❌ MCP Server Transport Test: FAILED")
    print("=" * 60)
    sys.exit(0 if success else 1)


