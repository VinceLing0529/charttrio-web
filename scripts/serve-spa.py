#!/usr/bin/env python3
"""静态托管前端 build 并为 SPA 路由回退 index.html。

原先 run-local.sh 用 python -m http.server 直出 build 目录，
/results、/payment/success 这类前端路由直接访问会 404
（站内跳转靠 React Router 没事，但支付回跳是整页加载，必须回退）。
"""
import http.server
import os
import sys
from pathlib import Path


class SPAHandler(http.server.SimpleHTTPRequestHandler):
    def send_head(self):
        path = self.translate_path(self.path)
        if not os.path.exists(path.split("?")[0]) and not self.path.endswith("/"):
            self.path = "/index.html"
        return super().send_head()

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "frontend/build")
    port = int(sys.argv[2] if len(sys.argv) > 2 else "3000")
    os.chdir(root)
    http.server.ThreadingHTTPServer(("127.0.0.1", port), SPAHandler).serve_forever()
