# ======================================================================================== #
# This is the tool_schemas.py module, the vocabulary book for the AI.                      #
# It defines the exact JSON structure of the tools available in our MCP server.            #
# I have completely revamped this from the old monolithic 'run_recon_scan' to modular,     #
# parallel-friendly tools: Subdomain Recon, Nmap, Ffuf, Nuclei, and PDF Generation.        #
# ======================================================================================== #

reconnator_tools = [
    {
        "type": "function",
        "function": {
            "name": "execute_subdomain_recon",
            "description": "Perform subdomain enumeration on a target domain and filter for active ones using Subfinder and dnsx.",
            "parameters": {
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "The root domain to scan (e.g., example.com)"
                    }
                },
                "required": ["domain"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_nmap",
            "description": "Run Nmap port scanner on a specified target.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "The IP address, domain, or subdomain to scan."
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["quick", "default", "deep"],
                        "description": "The intensity of the scan. Deep mode scans all ports."
                    }
                },
                "required": ["target"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_ffuf",
            "description": "Run Ffuf directory fuzzer on a specified target to find hidden endpoints.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "The target URL or domain to fuzz."
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["quick", "default", "deep"],
                        "description": "The intensity of the fuzzing. Deep mode uses a larger wordlist."
                    }
                },
                "required": ["target"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_nuclei",
            "description": "Run Nuclei vulnerability scanner on a specified target.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "The target URL or domain to scan for vulnerabilities."
                    }
                },
                "required": ["target"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_pdf_report",
            "description": "Generate a formal PDF report based on all currently saved scan memory. Must be called AFTER scanning tools have been executed.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]