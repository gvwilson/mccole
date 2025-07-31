"""Serve site."""

import argparse
import http.server
import socketserver
import os
from pathlib import Path


def serve(opt):
    """Main driver."""
    os.chdir(opt.root)
    print(f"serving {Path(opt.root).resolve()} on port {opt.port}...")
    with socketserver.TCPServer(("", opt.port), http.server.SimpleHTTPRequestHandler) as httpd:
        httpd.serve_forever()


def parse_args(parser):
    """Parse command-line arguments."""
    parser.add_argument("--port", type=int, default=8000, help="port")
    parser.add_argument("--root", type=str, default="docs", help="root directory")
    return parser


if __name__ == "__main__":
    opt = parse_args(argparse.ArgumentParser()).parse_args()
    serve(opt)
