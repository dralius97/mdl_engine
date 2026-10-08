from src.ports.mcp.servers import mcp


if __name__ == "__main__":
    print("Menjalankan FastMCP Semantic Layer Server (SSE mode)...")
    # Menjalankan server FastMCP menggunakan transport SSE
    mcp.run(transport="sse", host="0.0.0.0", port=38000)