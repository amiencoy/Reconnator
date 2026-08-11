# ==================================================================================================================================================================== #
# This is the Subfinder engine module. The first scout in our reconnaissance pipeline.                                                                                 #
# It runs asynchronously inside an ephemeral Docker container to harvest subdomains.                                                                                   #
# The function run_subfinder will be called from the mcp_server.py module.                                                                                             #
# Note: If Subfinder fails (e.g., crt.sh timeout), the MCP server will automatically fallback to the AlienVault OTX fetcher to ensure we don't walk away empty-handed. #
# ==================================================================================================================================================================== #

import asyncio
import logging

logger = logging.getLogger(__name__)

async def run_subfinder(domain: str) -> list:
    """
    Executes Subfinder via Ephemeral Docker Container asynchronously.
    Accepts a domain string and returns a list of discovered subdomains.
    """
    logger.info(f"Initiating recon on {domain}...")
    
    cmd = [
        "docker", "run", "--rm", 
        "projectdiscovery/subfinder:latest", 
        "-d", domain, 
        "-silent"
    ]
    
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0 and stderr:
            logger.warning(f"Subfinder stderr: {stderr.decode().strip()}")
            
        subdomains = [line for line in stdout.decode().splitlines() if line.strip()]
                    
        logger.info(f"Recon complete. Found {len(subdomains)} subdomains.")
        return subdomains

    except Exception as e:
        logger.error(f"Failed to execute containerized Subfinder: {e}")
        return []