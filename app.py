"""
Vercel Serverless WSGI Web Adapter for Hill Hold Assist Simulator.
Serves the web application and static assets seamlessly on Vercel cloud runtime.
"""

import os
import mimetypes

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def app(environ, start_response):
    path_info = environ.get("PATH_INFO", "/").lstrip("/")
    
    # Default route or index
    if not path_info or path_info == "index.html":
        target = os.path.join(BASE_DIR, "index.html")
    else:
        # Sanitize path to prevent traversal
        safe_path = os.path.normpath(path_info).replace("\\", "/")
        if safe_path.startswith(".."):
            target = os.path.join(BASE_DIR, "index.html")
        else:
            target = os.path.join(BASE_DIR, safe_path)

    if os.path.isfile(target):
        mime, _ = mimetypes.guess_type(target)
        if not mime:
            if target.endswith(".js"):
                mime = "application/javascript"
            elif target.endswith(".css"):
                mime = "text/css"
            elif target.endswith(".wav"):
                mime = "audio/wav"
            elif target.endswith(".png"):
                mime = "image/png"
            else:
                mime = "application/octet-stream"

        if "text" in mime or mime == "application/javascript":
            mime += "; charset=utf-8"

        try:
            with open(target, "rb") as f:
                content = f.read()

            status = "200 OK"
            headers = [
                ("Content-Type", mime),
                ("Content-Length", str(len(content))),
                ("Cache-Control", "public, max-age=3600"),
                ("Access-Control-Allow-Origin", "*"),
            ]
            start_response(status, headers)
            return [content]
        except Exception as e:
            pass

    # Fallback to index.html for any unmapped route
    index_path = os.path.join(BASE_DIR, "index.html")
    try:
        with open(index_path, "rb") as f:
            content = f.read()
        status = "200 OK"
        headers = [
            ("Content-Type", "text/html; charset=utf-8"),
            ("Content-Length", str(len(content))),
        ]
        start_response(status, headers)
        return [content]
    except Exception:
        status = "404 Not Found"
        headers = [("Content-Type", "text/plain")]
        start_response(status, headers)
        return [b"Hill Hold Assist Simulator"]

handler = app
application = app

if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    port = 8080
    print(f"Serving HTTP on port {port}...")
    server = make_server("0.0.0.0", port, app)
    server.serve_forever()
