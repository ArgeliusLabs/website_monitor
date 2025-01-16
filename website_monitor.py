import requests
import time
from datetime import datetime
import json
import socks
import socket
from urllib3.exceptions import InsecureRequestWarning
from requests.exceptions import RequestException

# Suppress only the single warning from urllib3 needed.
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

class WebsiteMonitor:
    def __init__(self, slack_webhook_url):
        self.slack_webhook_url = slack_webhook_url
        self.sites = {}  # Dictionary to store sites and their failure counts
        self.last_status_report = datetime.now()
        
        # Create two sessions - one normal, one for Tor
        self.regular_session = requests.Session()
        self.tor_session = requests.Session()
        
        # Configure SOCKS proxy only for Tor session
        self.tor_session.proxies = {
            'http': 'socks5h://127.0.0.1:9050',
            'https': 'socks5h://127.0.0.1:9050'
        }

    def add_site(self, url):
        """Add a site to monitor"""
        self.sites[url] = {
            'failures': 0,
            'last_check': None,
            'alerted': False
        }

    def check_site(self, url):
        """Check if a site is accessible"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # Choose appropriate session based on URL
            session = self.tor_session if '.onion' in url else self.regular_session
            
            response = session.get(
                url,
                headers=headers,
                verify=False,  # Disable SSL verification
                timeout=30     # 30 second timeout
            )
            return response.status_code == 200
        except RequestException:
            return False

    def send_slack_alert(self, url):
        """Send alert to Slack"""
        # Find the comment for this URL
        comment = next((site['comment'] for site in config['sites'] if site['url'] == url), '')
        site_desc = f"{url} ({comment})" if comment else url
        
        message = {
            "text": f"🚨 Alert: {site_desc} has been down for 3 consecutive checks!\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        }
        
        try:
            requests.post(
                self.slack_webhook_url,
                data=json.dumps(message),
                headers={'Content-Type': 'application/json'}
            )
        except Exception as e:
            print(f"Failed to send Slack alert: {e}")

    def send_daily_report(self):
        """Send a daily status report to Slack"""
        status_lines = ["📊 Daily Status Report:"]
        
        for url in self.sites:
            # Find the comment for this URL
            comment = next((site['comment'] for site in config['sites'] if site['url'] == url), '')
            site_desc = f"{url} ({comment})" if comment else url
            
            failures = self.sites[url]['failures']
            status = "❌ Down" if failures > 0 else "✅ Up"
            status_lines.append(f"{status}: {site_desc}")
        
        message = {
            "text": "\n".join(status_lines)
        }
        
        try:
            requests.post(
                self.slack_webhook_url,
                data=json.dumps(message),
                headers={'Content-Type': 'application/json'}
            )
        except Exception as e:
            print(f"Failed to send daily report: {e}")

    def monitor(self):
        """Main monitoring loop"""
        while True:
            current_time = datetime.now()
            print(f"\nChecking sites at {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Check if 24 hours have passed since last status report
            if (current_time - self.last_status_report).total_seconds() >= 86400:  # 86400 seconds = 24 hours
                self.send_daily_report()
                self.last_status_report = current_time
            
            for url in self.sites:
                site_status = self.check_site(url)
                
                if not site_status:
                    self.sites[url]['failures'] += 1
                    print(f"❌ {url} is down (Failure #{self.sites[url]['failures']})")
                    
                    # Send alert every 3 failures
                    if self.sites[url]['failures'] % 3 == 0:
                        self.send_slack_alert(url)
                else:
                    # Reset counters if site is back up
                    if self.sites[url]['failures'] > 0:
                        print(f"✅ {url} is back up!")
                    self.sites[url]['failures'] = 0
                
                self.sites[url]['last_check'] = current_time
            
            # Wait for 1 hour before next check
            time.sleep(3600)

# Example usage
if __name__ == "__main__":
    import sys
    import json
    
    try:
        # Load configuration from config.json
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        SLACK_WEBHOOK_URL = config['slack_webhook_url']
        sites_to_monitor = config['sites']
        
        # Validate configuration
        if SLACK_WEBHOOK_URL == "YOUR_SLACK_WEBHOOK_URL":
            print("Error: Please set your Slack webhook URL in config.json")
            sys.exit(1)
            
        if not sites_to_monitor:
            print("Error: No sites configured in config.json")
            sys.exit(1)
            
        # Initialize and start monitor
        monitor = WebsiteMonitor(SLACK_WEBHOOK_URL)
        
        print("Starting monitoring for the following sites:")
        for site in sites_to_monitor:
            url = site['url']
            comment = site.get('comment', '')
            print(f"- {url} ({comment})")
            monitor.add_site(url)
        
        # Start monitoring
        monitor.monitor()
        
    except FileNotFoundError:
        print("Error: config.json not found. Please create it with your configuration.")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Error: config.json is not valid JSON. Please check the format.")
        sys.exit(1)
    except KeyError as e:
        print(f"Error: Missing required configuration key: {e}")
        sys.exit(1) 
