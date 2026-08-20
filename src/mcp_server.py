# ================================================================================== #
# This is the main MCP Server module, the absolute backbone of Reconnator's muscles. #
# It exposes all our security engines as callable tools for the AI agent.            #
# I've also wired up the new subdomain recon pipeline here.                          #
# The flow goes: Subfinder -> OTX (fallback) -> dnsx (to kill the ghost subdomains). #
# Because feeding dead servers to Nuclei is a crime against compute resources.       #
# ================================================================================== #

import os
import json
import logging
import time
from fastmcp import FastMCP
from modules.nmap_engine import run_nmap
from modules.ffuf_engine import run_ffuf
from modules.nuclei_engine import run_nuclei
from modules.report_generator import generate_scan_report
from modules.subfinder_engine import run_subfinder
from modules.otx_fetcher import fetch_subdomains_otx
from modules.dnsx_engine import run_dnsx

logger = logging.getLogger(__name__)

mcp = FastMCP("ReconnatorCore")
scan_memory = {}

def mark_scan_start():
    if "_metadata" not in scan_memory:
        scan_memory["_metadata"] = {}
    if "start_time" not in scan_memory["_metadata"]:
        scan_memory["_metadata"]["start_time"] = time.time()

@mcp.tool()
async def execute_subdomain_recon(domain: str) -> str:
    """
    Perform subdomain enumeration on a target domain and filter for active ones.
    Uses Subfinder (and OTX as fallback) followed by dnsx to ensure targets are alive.
    """
    mark_scan_start()
    try:
        raw_subdomains = await run_subfinder(domain)
        if not raw_subdomains:
            logger.info("Subfinder returned empty, falling back to OTX...")
            raw_subdomains = fetch_subdomains_otx(domain)
            
        if not raw_subdomains:
            return f"[FAILED] Subdomain recon found absolutely nothing for {domain}."

        active_subdomains = await run_dnsx(raw_subdomains)
        
        if not active_subdomains:
            return f"[FAILED] Found {len(raw_subdomains)} subdomains, but dnsx says they are all DEAD (Ghost town)."

        scan_memory[f"recon_{domain}"] = active_subdomains
        
        return f"[SUCCESS] Recon completed on {domain}. Found {len(raw_subdomains)} total, {len(active_subdomains)} ACTIVE endpoints. Data saved to memory."
    except Exception as e:
        logger.error(f"Recon Error: {e}")
        return f"[ERROR] Subdomain recon failed: {str(e)}"

@mcp.tool()
async def execute_nmap(target: str, mode: str = "default") -> str:
    """
    Run Nmap port scanner on a specified target.
    Modes available: 'quick', 'default', 'deep'.
    """
    mark_scan_start()
    try:
        results = await run_nmap([target], mode)
        scan_memory[f"nmap_{target}"] = results
        return f"[SUCCESS] Nmap scan completed on {target}. Found {len(results)} active endpoints. Data saved to memory."
    except Exception as e:
        logger.error(f"Nmap Error: {e}")
        return f"[ERROR] Nmap execution failed: {str(e)}"

@mcp.tool()
async def execute_ffuf(target: str, mode: str = "deep") -> str:
    """
    Run Ffuf directory fuzzer on a specified target.
    Always prefer 'deep' mode for recursive fuzzing.
    """
    mark_scan_start()
    try:
        results = await run_ffuf([target], mode)
        scan_memory[f"ffuf_{target}"] = results
        return f"[SUCCESS] Ffuf scan completed on {target}. Data saved to memory."
    except Exception as e:
        logger.error(f"Ffuf Error: {e}")
        return f"[ERROR] Ffuf execution failed: {str(e)}"

@mcp.tool()
async def execute_nuclei(target: str) -> str:
    """
    Run Nuclei vulnerability scanner on a specified target.
    """
    mark_scan_start()
    try:
        results = await run_nuclei([target])
        scan_memory[f"nuclei_{target}"] = results
        return f"[SUCCESS] Nuclei scan completed on {target}. Found {len(results)} vulnerabilities. Data saved to memory."
    except Exception as e:
        logger.error(f"Nuclei Error: {e}")
        return f"[ERROR] Nuclei execution failed: {str(e)}"

@mcp.tool()
async def create_pdf_report() -> str:
    """
    Generate a formal PDF report based on all currently saved scan memory.
    Must be called after scanning tools have been executed.
    """
    if not scan_memory:
        return "[FAILED] No scan data in memory. Run a scan first."
    
    try:
        start_time = scan_memory.get("_metadata", {}).get("start_time", time.time())
        end_time = time.time()
        
        duration_seconds = int(end_time - start_time)
        minutes, seconds = divmod(duration_seconds, 60)
        formatted_duration = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"
        
        if "_metadata" not in scan_memory:
            scan_memory["_metadata"] = {}
            
        scan_memory["_metadata"]["duration"] = formatted_duration

        filepath = await generate_scan_report(scan_memory, "pdf")
        
        if filepath:
            scan_memory.clear()
            return f"[SUCCESS] PDF Report successfully generated at: {filepath}"
            
        return "[ERROR] Report generation returned no file."
        
    except Exception as e:
        logger.error(f"Report Error: {e}")
        return f"[ERROR] Failed to generate PDF report: {str(e)}"

if __name__ == "__main__":
    mcp.run()