# ================================================================================== #
# This is the dnsx engine module. It acts as the bouncer for our recon pipeline.     #
# Subfinder and OTX are great, but they often give us a lot of ghost subdomains.     #
# Feeding dead targets to Nuclei is a huge waste of time and server resources.       #
# So, dnsx will knock on their doors and only let the alive ones pass through.       #
# Gotta keep the pipeline lean, fast, and also a little bit mean, I guess.           #
# ================================================================================== #

import asyncio
import logging

logger = logging.getLogger(__name__)

async def run_dnsx(subdomains: list) -> list:
    """
    Running dnsx via Ephemeral Docker Container asynchronously.
    Accepts a list of subdomains, pipes them to dnsx via stdin, and returns active ones.
    """
    if not subdomains:
        logger.warning("No subdomains provided to dnsx. Skipping resolution.")
        return []

    logger.info(f"Filtering {len(subdomains)} subdomains through dnsx...")

    cmd = [
        "docker", "run", "--rm", "-i",
        "projectdiscovery/dnsx:latest",
        "-silent"
    ]

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        input_data = "\n".join(subdomains).encode()
        stdout, stderr = await process.communicate(input=input_data)

        if process.returncode != 0 and stderr:
            logger.warning(f"dnsx stderr: {stderr.decode().strip()}")

        active_subdomains = [line for line in stdout.decode().splitlines() if line.strip()]
        
        logger.info(f"dnsx filtering complete: {len(active_subdomains)} alive out of {len(subdomains)}.")
        return active_subdomains

    except Exception as e:
        logger.error(f"Failed to run dnsx container: {e}")
        return []