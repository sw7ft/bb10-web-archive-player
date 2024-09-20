import http.server
import urllib.parse
import json
import internetarchive
import requests
import socket
from urllib.parse import unquote

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            with open("index.html", "rb") as f:
                self.wfile.write(f.read())

        # Serve list of episodes
        elif self.path.startswith("/episodes"):
            identifier = "canadian_lara_Croft"
            item = internetarchive.get_item(identifier)
            files = item.files

            video_files = [file['name'] for file in files if file.get('format') in ['MPEG4', 'h.264', 'Ogg Video', 'WebM']]
            
            # Send list of video files as JSON
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()

            response_data = {
                "identifier": identifier,
                "videos": video_files
            }
            self.wfile.write(json.dumps(response_data).encode())

        # Stream video content with range request support
        elif self.path.startswith("/stream"):
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            video_name = params.get("video", [""])[0]

            if video_name:
                identifier = "canadian_lara_Croft"
                video_url = f"https://archive.org/download/{identifier}/{unquote(video_name)}"

                # Stream video with range support
                headers = {}
                if "Range" in self.headers:
                    headers["Range"] = self.headers["Range"]

                response = requests.get(video_url, headers=headers, stream=True)

                # Handle partial content for range requests
                if response.status_code == 206:
                    self.send_response(206)
                    self.send_header("Content-Type", "video/mp4")
                    self.send_header("Content-Range", response.headers.get("Content-Range"))
                else:
                    self.send_response(200)
                    self.send_header("Content-Type", "video/mp4")
                self.end_headers()

                try:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            self.wfile.write(chunk)
                except BrokenPipeError:
                    print(f"Client disconnected while streaming {video_name}")
                except Exception as e:
                    print(f"Error while streaming video: {e}")

if __name__ == "__main__":
    try:
        server_address = ('', 8014)  # Running on port 8014
        httpd = http.server.HTTPServer(server_address, MyHandler)
        print("Serving on port 8014...")
        httpd.serve_forever()
    except socket.error as e:
        print(f"Socket error: {e}")
