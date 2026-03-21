# Troubleshooting Guide - Vision Context MCP

## Common Issues and Solutions

### Installation Issues

#### Error: "Module not found: vision_context_mcp"
```bash
# Solution
cd /home/gdrick/vision-context-mcp
pip install -e .
```

#### Error: "mcp package not found"
```bash
# Solution
pip install mcp>=1.0.0
```

#### Error: "cv2 not found" or "opencv not found"
```bash
# Solution
pip install opencv-python>=4.8.0
```

### MCP Configuration Issues

#### MCP server not appearing in list
1. Check configuration file location:
   - Cline: `~/.cline/mcp_settings.json`
   - VS Code: `.vscode/mcp.json`
   
2. Verify JSON syntax:
```json
{
  "mcpServers": {
    "vision-context": {
      "command": "python",
      "args": ["-m", "vision_context_mcp.server"],
      "cwd": "/home/gdrick/vision-context-mcp"
    }
  }
}
```

3. Restart VS Code / Cline after configuration changes

#### Error: "Command not found" when using uvx
```bash
# Install uvx
pip install uv
# Or use python directly in config
```

### Runtime Issues

#### Error: "Model download failed"
```bash
# Models download on first use
# Check internet connection and disk space
export HF_HOME=/tmp/hf-cache
```

#### Error: "Out of memory"
- Use lighter methods: `canny` instead of `hed`
- Use `midas` instead of `zoedepth` for depth
- Close other applications

#### Error: "Timeout"
- Increase timeout in MCP client config
- Use faster methods (OpenCV fallbacks)

#### Error: "JSON serialization error"
- Check logs for non-serializable objects
- Ensure all return values are dict/list/primitives

### Testing Issues

#### Test image not found
```bash
python scripts/validation/create_test_image.py
```

#### Tests fail with import errors
```bash
pip install -e ".[dev]"
pytest tests/
```

---

## Validation Checklist

Before deployment, run:
```bash
python scripts/validation/validate_deployment.py
```

Manual checklist:
- [ ] Python 3.10+ installed
- [ ] Core dependencies installed (mcp, opencv, pillow, numpy)
- [ ] Package installs successfully
- [ ] Import works without errors
- [ ] All 8 image tools pass tests
- [ ] MCP server starts without errors
- [ ] Configuration file is valid JSON
- [ ] Tools appear in MCP client

---

## Getting Help

1. Check logs in terminal output
2. Run validation script for detailed diagnostics
3. Review MEMORY BANK for project context
4. Open issue on GitHub with error details

---

**Last Updated**: 21 March 2026