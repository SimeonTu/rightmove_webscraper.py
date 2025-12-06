#!/usr/bin/env python3
"""
Simple HTTP server to serve CSV files for the React UI
"""

import http.server
import socketserver
import os
import json
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import pandas as pd

class CSVHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/csv-files':
            # List available CSV files
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            results_dir = Path('../results')
            csv_files = []
            
            if results_dir.exists():
                for run_folder in results_dir.iterdir():
                    if run_folder.is_dir():
                        for file in run_folder.glob('*.csv'):
                            csv_files.append({
                                'name': file.name,
                                'path': str(file.relative_to(results_dir)),
                                'size': file.stat().st_size,
                                'modified': file.stat().st_mtime,
                                'run_folder': run_folder.name
                            })
            
            self.wfile.write(json.dumps(csv_files).encode())
            return
            
        elif parsed_path.path.startswith('/api/csv/'):
            # Serve specific CSV file
            csv_path = parsed_path.path.replace('/api/csv/', '')
            full_path = Path('../results') / csv_path
            
            if full_path.exists() and full_path.suffix == '.csv':
                self.send_response(200)
                self.send_header('Content-type', 'text/csv')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Disposition', f'attachment; filename="{full_path.name}"')
                self.end_headers()
                
                with open(full_path, 'rb') as f:
                    self.wfile.write(f.read())
                return
        
        # Default to serving static files
        super().do_GET()

def main():
    PORT = 3001
    
    # Change to the web directory
    os.chdir(Path(__file__).parent)
    
    with socketserver.TCPServer(("", PORT), CSVHandler) as httpd:
        print(f"Server running at http://localhost:{PORT}")
        print("Available endpoints:")
        print(f"  - http://localhost:{PORT}/api/csv-files (list CSV files)")
        print(f"  - http://localhost:{PORT}/api/csv/<path> (download CSV file)")
        print(f"  - http://localhost:{PORT}/ (serve React app)")
        print("\nPress Ctrl+C to stop the server")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

if __name__ == "__main__":
    main()


