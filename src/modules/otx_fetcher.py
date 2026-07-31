# ==================================================================================== #
# This is the AlienVault OTX Fetcher module. The backup plan for our recon pipeline.   #
# It queries the OTX API for passive DNS data related to a given domain.               #
# We use this as a fallback when Subfinder fails or finds zero results.                #
# Note: OTX API has rate limits, so we handle it gracefully asynchronously.            #
# ==================================================================================== #

import logging
import httpx

logger = logging.getLogger(__name__)

async def fetch_subdomains_otx(domain: str) -> list:
    logger.info(f"Finding available subdomains for {domain} taken from AlienVault OTX...")
    url = f"https://otx.alienvault.com/api/v1/indicators/domain/{domain}/passive_dns"
    
    subdomains = set()
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            
            if 'passive_dns' in data:
                for entry in data['passive_dns']:
                    hostname = entry.get('hostname')
                    if hostname and hostname.endswith(domain):
                        clean_host = hostname.lstrip('*.')
                        subdomains.add(clean_host)
                        
        logger.info(f"Found {len(subdomains)} unique subdomains from OTX.")
        return list(subdomains)
        
    except Exception as e:
        logger.error(f"Failed to retrieve data from AlienVault OTX: {e}")
        return []