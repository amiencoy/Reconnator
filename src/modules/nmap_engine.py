# ==================================================================================== #
# This is the Nmap engine module. The aggressive port knocker of our pipeline.         #
# It runs asynchronously inside an ephemeral Docker container to map exposed services. #
# Thanks to our dnsx filter, Nmap will only knock on doors that actually exist,        #
# saving us hours of waiting for TCP connection timeouts from ghost servers.           #
# ==================================================================================== #

import asyncio
import logging
import urllib.parse
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

async def run_nmap(targets: list, scan_mode: str = "default") -> str:
    """
    Executes Nmap network scanner inside a Docker container.
    Accepts a list of targets and returns a formatted string of discovered open ports and services.
    Modes: "quick" (top 100 ports), "default", "deep" (all ports + default scripts).
    """
    clean_targets = set()
    for t in targets:
        if "://" in t:
            parsed = urllib.parse.urlparse(t)
            clean_targets.add(parsed.hostname)
        else:
            clean_targets.add(t.split(':')[0])
            
    target_string = " ".join(clean_targets)
    logger.info(f"Initiating Nmap scan on {target_string} with mode: {scan_mode.upper()}")

    nmap_flags = ["-sV", "-Pn", "-oX", "-"]

    if scan_mode == "quick":
        nmap_flags.insert(0, "-F")
    elif scan_mode == "deep":
        nmap_flags.insert(0, "-p-")
        nmap_flags.insert(1, "-sC")
        
    cmd = [
        "docker", "run", "--rm", 
        "reconnator-nmap:latest"
    ] + nmap_flags + list(clean_targets)
    
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0 and not stdout:
            logger.warning(f"Nmap stderr: {stderr.decode().strip()}")
            return ""

        results = {}
        try:
            root = ET.fromstring(stdout.decode())
            for host in root.findall('host'):
                address = "Unknown"
                hostnames = host.find('hostnames')
                if hostnames is not None and hostnames.find('hostname') is not None:
                    address = hostnames.find('hostname').get('name')
                elif host.find('address') is not None:
                    address = host.find('address').get('addr')

                open_ports = []
                ports = host.find('ports')
                if ports is not None:
                    for port in ports.findall('port'):
                        state = port.find('state').get('state')
                        if state == 'open':
                            portid = port.get('portid')
                            service = port.find('service')
                            service_name = service.get('name') if service is not None else 'unknown'
                            product = service.get('product') if service is not None else ''
                            open_ports.append(f"{portid} ({service_name} {product})".strip())
                
                if open_ports:
                    results[address] = open_ports
                    
        except ET.ParseError:
            logger.error("Failed to parse XML output from Nmap.")
            
        logger.info(f"Nmap scan complete. Found open ports on {len(results)} hosts.")

        if not results:
            return ""
            
        formatted_output = "NMAP Open Ports Discovery:\n"
        for host, ports in results.items():
            formatted_output += f"Host: {host}\n"
            for port in ports:
                formatted_output += f"  > Port {port}\n"
            formatted_output += "\n"
            
        return formatted_output.strip()

    except Exception as e:
        logger.error(f"Failed to execute containerized Nmap: {e}")
        return ""