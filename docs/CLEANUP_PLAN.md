# WebSpark Cleanup Plan

## Summary
WebSpark has evolved significantly and contains several legacy files that are no longer used. This cleanup plan identifies files that can be safely archived or removed to streamline the project.

## Active Core Files (Keep)
- **`app.py`** - Main FastAPI server (434 lines, 8 endpoints)
- **`test_agent.py`** - AI browser automation engine
- **`gemini_analyzer.py`** - Core Tealium analysis engine
- **`agent_gemini_analyzer.py`** - Enhanced analyzer using agent-discovered selectors
- **`selectors_config.py`** - Manual selector configuration
- **`templates/`** - All HTML templates (index.html, agent.html)
- **`static/`** - All CSS/JS/image assets
- **`requirements.txt`** - Python dependencies
- **`package.json`** - Node.js frontend dependencies

## Legacy Files (Can Remove)

### Alternative Implementations
- **`main.py`** (84 lines) - Alternative FastAPI setup, superseded by `app.py`
- **`run_agent.py`** (90 lines) - CSV-based automation, replaced by AI agent system
- **`init_db.py`** - Database initialization, not used (no database in current architecture)

### Test Directory
- **`tests/`** directory - Contains legacy test scripts:
  - `test_agent.py` - Old agent tests
  - `test_cookie_banner.py` - Cookie banner tests  
  - `test_scraper.py` - Scraper tests
  - `test_script.py` - General script tests
  - `test_script_gemini.py` - Gemini tests
  - `test_sqlalchemy.py` - Database tests
  - `test_tealium_recorder.py` - Tealium tests
  - `multi_step_test*.py` - Multi-step tests
  - `links_product_page.csv` - CSV selector data

### Legacy Data Files
- **`links_product_page.csv`** (root) - Old CSV selector format, replaced by JSON

## Generated Data Files (Keep but Manage)
These files are auto-generated and should be kept but can be cleaned up periodically:
- **`agent_discovered_selectors.json`** - Current: 2 selectors
- **`out.json`** - Agent execution history (large file, 257 lines)
- **`agent_logs.txt`** - Real-time logs
- **`tealium_analysis_*.json`** - Analysis results (multiple timestamped files)
- **`browser-use/dom_state_data/*.png`** - Browser screenshots

## Cleanup Actions

### Immediate Actions (Safe to Remove)
```bash
# Create backup directory
mkdir -p archive/legacy-files

# Move legacy implementations
mv main.py archive/legacy-files/
mv run_agent.py archive/legacy-files/
mv init_db.py archive/legacy-files/

# Move legacy CSV data
mv links_product_page.csv archive/legacy-files/

# Move test directory
mv tests/ archive/legacy-files/
```

### Data File Management (Optional)
```bash
# Create data archive directory
mkdir -p archive/old-data

# Archive old analysis files (keep recent ones)
mv tealium_analysis_*2025041*.json archive/old-data/
mv agent_tealium_analysis_*2025041*.json archive/old-data/

# Clean up old screenshots (keep recent ones)
find browser-use/dom_state_data/ -name "*.png" -mtime +7 -exec mv {} archive/old-data/ \;
```

## Documentation Files (Keep)
- **`integration-plan.md`** - Historical planning document
- **`project-schema.md`** - Schema documentation  
- **`project-specs.md`** - Project specifications
- **`PROJECT_STRUCTURE.md`** - Current structure analysis
- **`CLAUDE.md`** - Project documentation
- **`README.md`** - Main project readme

## Benefits of Cleanup
1. **Reduced confusion** - Clear separation of active vs legacy code
2. **Smaller repository** - Easier navigation and understanding
3. **Cleaner development** - Focus on current implementation only
4. **Preserved history** - Legacy files archived, not deleted

## Risk Assessment
- **Low Risk**: Legacy implementation files (main.py, run_agent.py, init_db.py)
- **Low Risk**: Test directory (not part of production system)
- **Medium Risk**: Old data files (can be regenerated but contain historical data)
- **No Risk**: Generated files are automatically recreated

## Next Steps
1. Review this cleanup plan
2. Create archive directory structure
3. Move legacy files to archive
4. Test that application still works correctly
5. Update .gitignore to exclude archive directory
6. Document the cleanup in project history