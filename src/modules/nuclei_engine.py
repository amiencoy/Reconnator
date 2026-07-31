# ===================================================================================== #
# This is the Nuclei engine module. The vulnerability sniper of our recon pipeline.     #
# It runs asynchronously inside an ephemeral Docker container to blast known CVEs.      #
# Because we've filtered the ghost targets using dnsx earlier, Nuclei can now focus     #
# its firepower solely on active servers without hanging on annoying network timeouts.  #
# ===================================================================================== #

import asyncio
import json
import logging

logger = logging.getLogger(__name__)

async def run_nuclei(targets: list) -> list:
    """
    Executes Nuclei via Ephemeral Docker Container asynchronously.
    Accepts a list of URLs (or dicts) and scans all of them in one run.
    """
    extracted_urls = []
    for t in targets:
        if isinstance(t, dict) and 'url' in t:
            extracted_urls.append(t['url'])
        elif isinstance(t, str):
            extracted_urls.append(t)
            
    target_string = ",".join(extracted_urls)
    
    logger.info(f"Initiating OPTIMIZED containerized Nuclei strike on {len(extracted_urls)} targets...")
    
    cmd = [
        "docker", "run", "--rm", 
        "reconnator-nuclei:latest",
        "-u", target_string, 
        "-silent", 
        "-jsonl",
        "-c", "50", 
    ]

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0 and stderr:
            logger.warning(f"Nuclei stderr: {stderr.decode().strip()}")
            
        results = []
        for line in stdout.decode().splitlines():
            if line.strip():
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
                    
        logger.info(f"Nuclei strike complete. Found {len(results)} issues.")
        return results

    except Exception as e:
        logger.error(f"Failed to execute containerized Nuclei: {e}")
        return []