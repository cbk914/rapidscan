#!/usr/bin/python
# -*- coding: utf-8 -*-
#                               __         __
#                              /__)_   '_/(  _ _
#                             / ( (//)/(/__)( (//)
#                                  /
#
# Author:      Shankar Damodaran
# Tool:        RapidScan
# Usage:       ./rapidscan.py example.com (or) python rapidsan.py example.com
# Description: This scanner automates the process of security scanning by using a 
#              multitude of available linux security tools and some custom scripts. 
#

# Importing the libraries
import sys
import socket
import subprocess
import os
import time
import threading
import collections
import signal
import random



# Initializing the color module class
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    BADFAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    CRIT_BG = '\033[41m'
    SAFE_BG = '\033[42m'
    MEDIUM_BG = '\033[43m'
    LOW_BG = '\033[44m'
    

# Legends  
proc_high = bcolors.BADFAIL + "●" + bcolors.ENDC
proc_med  = bcolors.WARNING + "●" + bcolors.ENDC
proc_low  = bcolors.OKGREEN + "●" + bcolors.ENDC


# RapidScan Help Context
def helper():
        print "\nInformation:"
        print "-------------"
        print "./rapidscan.py example.com: Scans the domain example.com"
        print "./rapidscan.py --update   : Updates the scanner to the latest version."
        print "./rapidscan.py --help     : Displays this help context."
        print "\nInteractive:"
        print "------------"
        print "Ctrl+C: Skips current test."
        print "Ctrl+Z: Quits RapidScan."
        print "\nLegends:"
        print "--------"
        print "["+proc_high+"]    : Scan process may take longer times (not predictable)."
        print "["+proc_med+"]    : Scan process may take less than 10 minutes."
        print "["+proc_low+"]    : Scan process may take less than a minute or two.\n"
        

# Clears Line
def clear():
        sys.stdout.write("\033[F")
        sys.stdout.write("\033[K") 
 

# Initiliazing the idle loader/spinner class
class Spinner:
    busy = False
    delay = 0.05

    @staticmethod
    def spinning_cursor():
        while 1: 
            for cursor in '|/\\': yield cursor

    def __init__(self, delay=None):
        self.spinner_generator = self.spinning_cursor()
        if delay and float(delay): self.delay = delay

    def spinner_task(self):
        try:
            while self.busy:
                sys.stdout.write(next(self.spinner_generator))
                sys.stdout.flush()
                time.sleep(self.delay)
                sys.stdout.write('\b')
                sys.stdout.flush()
        except (KeyboardInterrupt, SystemExit):
            clear()
            print "\t"+ bcolors.CRIT_BG+"RapidScan received a series of Ctrl+C hits. Quitting..." +bcolors.ENDC
            sys.exit(1)

    def start(self):
        self.busy = True
        threading.Thread(target=self.spinner_task).start()

    def stop(self):
        try:
            self.busy = False
            time.sleep(self.delay)
        except (KeyboardInterrupt, SystemExit):
            clear()
            print "\t"+ bcolors.CRIT_BG+"RapidScan received a series of Ctrl+C hits. Quitting..." +bcolors.ENDC
            sys.exit(1)
# End ofloader/spinner class        

# Instantiating the spinner/loader class
spinner = Spinner()

# Scanners that will be used and filename rotation 
tool_names = [
                ["host","Host - Checks for existence of IPV6 address."],
                ["aspnet_config_err","ASP.Net Misconfiguration - Checks for ASP.Net Misconfiguration."],
                ["wp_check","WordPress Checker - Checks for WordPress Installation."],
                ["drp_check", "Drupal Checker - Checks for Drupal Installation."],
                ["joom_check", "Joomla Checker - Checks for Joomla Installation."],
                ["uniscan","Uniscan - Checks for robots.txt & sitemap.xml"],
                ["wafw00f","Wafw00f - Checks for Application Firewalls."],
                ["nmap","Nmap - Fast Scan [Only Few Port Checks]"],
                ["theharvester","The Harvester - Scans for emails using Google's passive search."],
                ["dnsrecon","DNSRecon - Attempts Multiple Zone Transfers on Nameservers."],
                ["fierce","Fierce - Attempts Zone Transfer [No Brute Forcing]"],
                ["dnswalk","DNSWalk - Attempts Zone Transfer."],
                ["whois","WHOis - Checks for Administrator's Contact Information."],
                ["nmap_header","Nmap [XSS Filter Check] - Checks if XSS Protection Header is present."],
                ["nmap_sloris","Nmap [Slowloris DoS] - Checks for Slowloris Denial of Service Vulnerability."],
                ["sslyze_hbleed","SSLyze - Checks only for Heartbleed Vulnerability."],
                ["nmap_hbleed","Nmap [Heartbleed] - Checks only for Heartbleed Vulnerability."],
                ["nmap_poodle","Nmap [POODLE] - Checks only for Poodle Vulnerability."],
                ["nmap_ccs","Nmap [OpenSSL CCS Injection] - Checks only for CCS Injection."],
                ["nmap_freak","Nmap [FREAK] - Checks only for FREAK Vulnerability."],
                ["nmap_logjam","Nmap [LOGJAM] - Checks for LOGJAM Vulnerability."],
                ["sslyze_ocsp","SSLyze - Checks for OCSP Stapling."],
                ["sslyze_zlib","SSLyze - Checks for ZLib Deflate Compression."],
                ["sslyze_reneg","SSLyze - Checks for Secure Renegotiation Support and Client Renegotiation."],
                ["sslyze_resum","SSLyze - Checks for Session Resumption Support with [Session IDs/TLS Tickets]."],
                ["lbd","LBD - Checks for DNS/HTTP Load Balancers."],
                ["golismero_dns_malware","Golismero - Checks if the domain is spoofed or hijacked."],
                ["golismero_heartbleed","Golismero - Checks only for Heartbleed Vulnerability."],
                ["golismero_brute_url_predictables","Golismero - BruteForces for certain files on the Domain."],
                ["golismero_brute_directories","Golismero - BruteForces for certain directories on the Domain."],
                ["golismero_sqlmap","Golismero - SQLMap [Retrieves only the DB Banner]"],
                ["dirb","DirB - Brutes the target for Open Directories."],
                ["xsser","XSSer - Checks for Cross-Site Scripting [XSS] Attacks."],
                ["golismero_ssl_scan","Golismero SSL Scans - Performs SSL related Scans."],
                ["golismero_zone_transfer","Golismero Zone Transfer - Attempts Zone Transfer."],
                ["golismero_nikto","Golismero Nikto Scans - Uses Nikto Plugin to detect vulnerabilities."],
                ["golismero_brute_subdomains","Golismero Subdomains Bruter - Brute Forces Subdomain Discovery."],
                ["dnsenum_zone_transfer","DNSEnum - Attempts Zone Transfer."],
                ["fierce_brute_subdomains","Fierce Subdomains Bruter - Brute Forces Subdomain Discovery."],
                ["dmitry_email","DMitry - Passively Harvests Emails from the Domain."],
                ["dmitry_subdomains","DMitry - Passively Harvests Subdomains from the Domain."]
            ]




# Command that is used to initiate the tool (with parameters and extra params)
tool_cmd   = [
                ["host ",""],
                ["wget -O temp_aspnet_config_err ","/%7C~.aspx"],
                ["wget -O temp_wp_check ","/wp-admin"],
                ["wget -O temp_drp_check ","/user"],
                ["wget -O temp_joom_check ","/administrator"],
                ["uniscan -e -u ",""],
                ["wafw00f ",""],
                ["nmap -F --open ",""],
                ["theharvester -l 50 -b google -d ",""],
                ["dnsrecon -d ",""],
                ["fierce -wordlist xxx -dns ",""],
                ["dnswalk -d ","."],
                ["whois ",""],
                ["nmap -p80 --script http-security-headers ",""],
                ["nmap -p80,443 --script http-slowloris --max-parallelism 500 ",""],
                ["sslyze --heartbleed ",""],
                ["nmap -p 443 --script ssl-heartbleed ",""],
                ["nmap -p 443 --script ssl-poodle ",""],
                ["nmap -p 443 --script ssl-ccs-injection ",""],
                ["nmap -p 443 --script ssl-enum-ciphers ",""],
                ["nmap -p 443 --script ssl-dh-params ",""],
                ["sslyze --certinfo=basic ",""],
                ["sslyze --compression ",""],
                ["sslyze --reneg ",""],
                ["sslyze --resum ",""],
                ["lbd ",""],
                ["golismero -e dns_malware scan ",""],
                ["golismero -e heartbleed scan ",""],
                ["golismero -e brute_url_predictables scan ",""],
                ["golismero -e brute_directories scan ",""],
                ["golismero -e sqlmap scan ",""],
                ["dirb http://"," -fi"],
                ["xsser --all=http://",""],
                ["golismero -e sslscan scan ",""],
                ["golismero -e zone_transfer scan ",""],
                ["golismero -e nikto scan ",""],
                ["golismero -e brute_dns scan ",""],
                ["dnsenum ",""],
                ["fierce -dns ",""],
                ["dmitry -e ",""],
                ["dmitry -s ",""]
            ]


# Tool Responses (Begins)
tool_resp   = [
                ["[+] Has an IPv6 Address.",
                    "[-] Does not have an IPv6 Address. It is good to have one."],
                ["[+] No Misconfiguration Found.",
                    "[-] ASP.Net is misconfigured to throw server stack errors on screen."],
                ["[+] No WordPress Installation Found.",
                    "[-] WordPress Installation Found. Check for vulnerabilities corresponds to that version."],
                ["[+] No Drupal Installation Found.",
                    "[-] Drupal Installation Found. Check for vulnerabilities corresponds to that version."],
                ["[+] No Joomla Installation Found.",
                    "[-] Joomla Installation Found. Check for vulnerabilities corresponds to that version."],
                ["[+] robots.txt/sitemap.xml not Found.",
                    "[-] robots.txt/sitemap.xml found. Check those files for any information."],
                ["[+] Web Application Firewall Detected.",
                    "[-] No Web Application Firewall Detected"],
                ["[+] Common Ports are Closed.",
                    "[-] Some ports are open. Perform a full-scan manually."],
                ["[+] No Email Addresses Found.",
                    "[-] Email Addresses Found."],
                ["[+] Zone Transfer using DNSRecon Failed.",
                    "[-] Zone Transfer Successful using DNSRecon. Reconfigure DNS immediately."],
                ["[+] Zone Transfer using fierce Failed.",
                    "[-] Zone Transfer Successful using fierce. Reconfigure DNS immediately."],
                ["[+] Zone Transfer using dnswalk Failed.",
                    "[-] Zone Transfer Successful using dnswalk. Reconfigure DNS immediately."],
                ["[+] Whois Information Hidden.",
                    "[-] Whois Information Publicly Available."],
                ["[+] XSS Protection Filter is Enabled.",
                    "[-] XSS Protection Filter is Disabled."],
                ["[+] Not Vulnerable to Slowloris Denial of Service.",
                    "[-] Vulnerable to Slowloris Denial of Service."],
                ["[+] Not Prone to HEARTBLEED Vulnerability with SSLyze.",
                    "[-] HEARTBLEED Vulnerability Found with SSLyze."],
                ["[+] Not Prone to HEARTBLEED Vulnerability with Nmap.",
                    "[-] HEARTBLEED Vulnerability Found with Nmap."],
                ["[+] Not Prone to POODLE Vulnerability.",
                    "[-] POODLE Vulnerability Detected."],
                ["[+] Not Prone to OpenSSL CCS Injection.",
                    "[-] OpenSSL CCS Injection Detected."],
                ["[+] Not Prone to FREAK Vulnerability.",
                    "[-] FREAK Vulnerability Detected."],
                ["[+] Not Prone to LOGJAM Vulnerability.",
                    "[-] LOGJAM Vulnerability Found."],
                ["[+] OCSP Response was not sent by Server.",
                    "[-] Unsuccessful OCSP Response."],
                ["[+] Deflate Compression is Disabled.",
                    "[-] Server supports Deflate Compression."],
                ["[+] Secure Renegotiation is supported.",
                    "[-] Secure Renegotiation is unsupported."],
                ["[+] Session Resumption is supported.",
                    "[-] Secure Resumption unsupported with [Sessions IDs/TLS Tickets]."],
                ["[+] Load Balancer(s) Detected.",
                    "[-] No DNS/HTTP based Load Balancers Found."],
                ["[+] Domain is not spoofed/hijacked.",
                    "[-] Domain is spoofed/hijacked."],
                ["[+] Not Prone to HEARTBLEED Vulnerability with Golismero.",
                    "[-] HEARTBLEED Vulnerability Found with Golismero."],
                ["[+] No Files Found with Golismero BruteForce.",
                    "[-] Files Found with Golismero BruteForce."],
                ["[+] No Directories Found with Golismero BruteForce.",
                    "[-] Directories Found with Golismero BruteForce."],
                ["[+] Could not retrieve the DB Banner with SQLMap.",
                    "[-] DB Banner retrieved with SQLMap."],
                ["[+] Could not find Open Directories with DirB.",
                    "[-] Open Directories Found with DirB."],
                ["[+] Found XSS vulnerabilities with XSSer.",
                    "[-] XSSer did not find any XSS vulnerabilities."],
                ["[+] Golismero could not find any SSL related vulnerabilities.",
                    "[-] Found SSL related vulnerabilities with Golismero."],
                ["[+] Zone Transfer Failed with Golismero.",
                    "[-] Zone Transfer Successful with Golismero."],
                ["[+] Golismero Nikto Plugin coud not find any vulnerabilities.",
                    "[-] Golismero Nikto Plugin found vulnerabilities."],
                ["[+] Found Subdomains with Golismero.",
                    "[-] No Subdomains were discovered with Golismero."],
                ["[+] Zone Transfer using DNSEnum Failed.",
                    "[-] Zone Transfer Successful using DNSEnum. Reconfigure DNS immediately."],
                ["[+] No Subdomains were discovered with Fierce.",
                    "[-] Found Subdomains with Fierce."],
                ["[+] DMitry could not find any Email Addresses.",
                    "[-] Email Addresses discovered with DMitry."],
                ["[+] DMitry could not find any Subdomains.",
                    "[-] Subdomains discovered with DMitry."],
                
            ]

# Tool Responses (Ends)



# Tool Status (Reponse Data + Response Code (if status check fails and you still got to push it + Legends)
tool_status = [
                ["has IPv6",1,proc_low],
                ["Server Error",0,proc_low],
                ["wp-login",0,proc_low],
                ["drupal",0,proc_low],
                ["joomla",0,proc_low],
                ["[+]",0,proc_low],
                ["No WAF",0,proc_low],
                ["tcp open",0,proc_med],
                ["No emails found",1,proc_med],
                ["[+] Zone Transfer was successful!!",0,proc_low],
                ["Whoah, it worked",0,proc_low],
                ["0 errors",0,proc_low],
                ["Admin Email:",0,proc_low],
                ["XSS filter is disabled",0,proc_low],
                ["vulnerable",0,proc_high],
                ["Server is vulnerable to Heartbleed",0,proc_low],
                ["vulnerable",0,proc_low],
                ["vulnerable",0,proc_low],
                ["vulnerable",0,proc_low],
                ["vulnerable",0,proc_low],
                ["vulnerable",0,proc_low],
                ["ERROR - OCSP response status is not successful",0,proc_low],
                ["VULNERABLE - Server supports Deflate compression",0,proc_low],
                ["vulnerable",0,proc_low],
                ["vulnerable",0,proc_low],
                ["does NOT use Load-balancing",0,proc_med],
                ["No vulnerabilities found",1,proc_low],
                ["No vulnerabilities found",1,proc_low],
                ["No vulnerabilities found",1,proc_low],
                ["No vulnerabilities found",1,proc_low],
                ["No vulnerabilities found",1,proc_low],
                ["FOUND: 0",1,proc_high],
                ["Could not find any vulnerability!",1,proc_med],
                ["Occurrence ID",0,proc_low],
                ["DNS zone transfer successful",0,proc_low],
                ["Nikto found 0 vulnerabilities",1,proc_med],
                ["Possible subdomain leak",0,proc_high],
                ["AXFR record query failed:",1,proc_low],
                ["Found 1 entries",1,proc_high],
                ["Found 0 E-Mail(s)",1,proc_low],
                ["Found 0 possible subdomain(s)",1,proc_low]
            ]


# Shuffling Scan Order (starts)

scan_shuffle = list(zip(tool_names, tool_cmd, tool_resp, tool_status))
random.shuffle(scan_shuffle)
tool_names, tool_cmd, tool_resp, tool_status = zip(*scan_shuffle)

# Shuffling Scan Order (ends)



# Tool Head Pointer: (can be increased but certain tools will be skipped) 
tool = 0

# Run Test
runTest = 1 

# For accessing list/dictionary elements
arg1 = 0
arg2 = 1
arg3 = 2

if len(sys.argv) == 1 :
    helper()
else:
    target = sys.argv[1].lower()
    
    
    if target == '--update' or target == '-u' or target == '--u':
        print "RapidScan is updating....Please wait.\n"
        spinner.start()
        cmd = 'sha1sum rapidscan.py | grep .... | cut -c 1-40'
        oldversion_hash = subprocess.check_output(cmd, shell=True)
        oldversion_hash = oldversion_hash.strip()
        os.system('wget -N https://raw.githubusercontent.com/skavngr/rapidscan/master/rapidscan.py -O rapidscan.py > /dev/null 2>&1')
        newversion_hash = subprocess.check_output(cmd, shell=True)
        newversion_hash = newversion_hash.strip()
        if oldversion_hash == newversion_hash :
            clear()
            print "\t"+ bcolors.OKBLUE +"You already have the latest version of RapidScan." + bcolors.ENDC
        else:
            clear()
            print "\t"+ bcolors.OKGREEN +"RapidScan successfully updated to the latest version." +bcolors.ENDC
        spinner.stop()
        sys.exit(1)
        
    elif target == '--help' or target == '-h' or target == '--h':
        helper()
        sys.exit(1)
    else:
    
        os.system('rm te*') # Clearing previous scan files
        os.system('clear')
        os.system('setterm -cursor off')
        
        print bcolors.BOLD + "RapidScan | Initiating tools and scanning procedures for " + target+ "...\n" 
        
        print("""\
                                  __         __
                                 /__)_   '_/(  _ _
                                / ( (//)/(/__)( (//)
                                     /
                                ====================
                            
                            """)

        print bcolors.ENDC
        
        while(tool < len(tool_names)):    
            print "["+tool_status[tool][arg3]+"] Deploying "+bcolors.OKBLUE+tool_names[tool][arg2]+"\n"+bcolors.ENDC
            spinner.start()
            temp_file = "temp_"+tool_names[tool][arg1]
            cmd = tool_cmd[tool][arg1]+target+tool_cmd[tool][arg2]+" > "+temp_file+" 2>&1"
           
            try:
                subprocess.check_output(cmd, shell=True)
            except KeyboardInterrupt:
                runTest = 0
            except:
                runTest = 1
                
            if runTest == 1:
                spinner.stop()
                
                if tool_status[tool][arg1] not in open(temp_file).read():
                    if tool_status[tool][arg2] == 0:
                        clear()
                        print "\t"+bcolors.OKGREEN + tool_resp[tool][arg1] + bcolors.ENDC
                    else:
                        clear()
                        print "\t"+bcolors.BADFAIL + tool_resp[tool][arg2] + bcolors.ENDC
                else:
                    if tool_status[tool][arg2] == 1:
                        clear()
                        print "\t"+bcolors.OKGREEN + tool_resp[tool][arg1] + bcolors.ENDC
                    else:
                        clear()
                        print "\t"+bcolors.BADFAIL + tool_resp[tool][arg2] + bcolors.ENDC
            else:
                clear()
                print "\t"+bcolors.WARNING + "Test Skipped. Performing Next. Press Ctrl+Z to Quit RapidScan." + bcolors.ENDC                
                runTest = 1
                spinner.stop()
            
            tool=tool+1
            
        os.system('setterm -cursor on')
        os.system('rm te*') # Clearing previous scan files

