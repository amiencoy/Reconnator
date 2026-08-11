# ==================================================================================== #
# This is the Ffuf engine module. The aggressive directory fuzzer of the pipeline.     #
# It blindly brute-forces web servers to find hidden endpoints and secret files.       #
# Running it inside a disposable Docker container keeps our host machine sterile.      #
# Good thing we have dnsx now, so this engine won't waste time fuzzing dead servers.   #
# ==================================================================================== #

import asyncio
import json
import logging

logger = logging.getLogger(__name__)

async def run_ffuf(targets: list, scan_mode: str = "default") -> str:
    """
    Running FFUF (Fuzz Faster U Fool) inside the Docker Container to find the hidden directories.
    """
    wordlist = "/wordlists/deep.txt" if scan_mode == "deep" else "/wordlists/quick.txt"
    
    all_findings = {}
    
    for target in targets:
        if not target.startswith("http"):
            target_url = f"http://{target}"
        else:
            target_url = target

        fuzz_url = f"{target_url.rstrip('/')}/FUZZ"
        logger.info(f"Initiating FFUF scan on {fuzz_url} with mode: {scan_mode.upper()}")
        
        cmd = [
            "docker", "run", "--rm", 
            "reconnator-ffuf:latest",
            "-w", wordlist,
            "-u", fuzz_url,
            "-t", "50",
            "-mc", "200,204,301,302,307,401,403,500",
            "-ac",
            "-of", "json",
            "-o", "/dev/stdout",
            "-s"
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            findings = []
            if stdout:
                raw_output = stdout.decode().strip()
                try:
                    json_start_idx = raw_output.find('{')
                    
                    if json_start_idx != -1:
                        clean_json = raw_output[json_start_idx:]
                        output_data = json.loads(clean_json)
                        
                        for result in output_data.get('results', []):
                            findings.append({
                                'endpoint': result.get('input', {}).get('FUZZ', ''),
                                'status': result.get('status', 0),
                                'length': result.get('length', 0)
                            })
                    else:
                        logger.warning("Couldn't find JSON output on FFUF.")
                        
                except json.JSONDecodeError:
                    logger.error(f"Couldn't parse the JSON output. Raw output: {raw_output[:100]}")
                    
            if findings:
                all_findings[target] = findings
                
        except Exception as e:
            logger.error(f"Failed to execute containerized FFUF on {target}: {e}")
    if not all_findings:
        return ""
        
    formatted_output = "FFUF Discovered Endpoints:\n"
    for t_url, endpoints in all_findings.items():
        formatted_output += f"Target: {t_url}\n"
        for ep in endpoints:
            formatted_output += f"  > /{ep['endpoint']}  [Status: {ep['status']} | Size: {ep['length']} bytes]\n"
        formatted_output += "\n"
        
    return formatted_output.strip()