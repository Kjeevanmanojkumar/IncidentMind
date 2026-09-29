"""Start the real Streamlit process and probe HTTP from the same local runtime."""
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request


def test_streamlit_http_startup():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0))
        port=sock.getsockname()[1]
    root=Path(__file__).resolve().parents[1]
    proc=subprocess.Popen([sys.executable,'-m','streamlit','run','app.py',
        '--server.address','127.0.0.1','--server.port',str(port)],cwd=root,
        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        for _ in range(100):
            try:
                with opener.open(f'http://127.0.0.1:{port}/_stcore/health',timeout=1) as r:
                    assert r.status == 200
                    assert r.read() == b'ok'
                break
            except (OSError,TimeoutError):
                assert proc.poll() is None, 'Streamlit exited before startup'
                time.sleep(0.1)
        else:
            raise AssertionError('Streamlit did not become healthy within 10 seconds')
        with opener.open(f'http://127.0.0.1:{port}/',timeout=3) as r:
            assert r.status == 200
            assert b'<html' in r.read()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
