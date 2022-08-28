#!/usr/bin/env python3
"""
Simple git webhook server that pulls a repo's branch when a push is made
Usage: see commandline usage via `./webhook-server.py -h`
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
import argparse
import logging
import json
import subprocess
import os

# default in case commandline overrides are not specified
DEFAULT_GIT_DIR = "./"
DEFAULT_BRANCH = "master"

path_to_git = DEFAULT_GIT_DIR
branch_to_monitor = DEFAULT_BRANCH

# performs a headless `git pull` command within the repo
#
# Note: If repo requires git authentication, then this method assumes
# that you have ssh-keys with no passphrase setup. Since ssh keys will
# have no passphrase, it's recommended that you mark the keys with
# "read only" permissions. You can do this via deploy keys in github.
def git_pull(branch,remote='origin'):
    cwd = os.getcwd()
    os.chdir(path_to_git)
    try:
        ret_code = subprocess.call(['git','pull',remote,branch])
        logging.info('git pull returned %d' % ret_code)
    except Exception as e:
        logging.error('git pull operation threw exception: %s' % e)
    os.chdir(cwd)

# called when a push was made to the git branch of interest
def handle_push(push):
    ref = push.get('ref',None)
    commits = push.get('commits',[])

    logging.info("handling push\n ref: %s;\n # of commits: %d" % (ref,len(commits)))

    # pull new code when a push to 
    ref_to_monitor = "refs/heads/" + branch_to_monitor
    if ref == ref_to_monitor:
        git_pull(branch_to_monitor)

class S(BaseHTTPRequestHandler):
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length) # <--- Gets the data itself

        post_body = post_data.decode('utf-8')
        logging.debug("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                str(self.path), str(self.headers), post_body)
        payload = json.loads(post_body)

        if 'pusher' in payload:
            handle_push(payload)
        elif 'hook' in payload:
            # ping request
            logging.info("git webhook 'PING' request")
        else:
            logging.warn("unhandled payload: %s" % payload)

        self._set_response()
        self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))

def run(server_class=HTTPServer, handler_class=S, port=8080):
    logging.basicConfig(level=logging.INFO)
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logging.info('Starting httpd @ port %d\n' % port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('Stopping httpd...\n')

def dir_path(string):
    if os.path.isdir(string):
        return string
    else:
        raise NotADirectoryError(string)

if __name__ == '__main__':
    # command line arg parsing
    parser = argparse.ArgumentParser(
        usage='%(prog)s [options]',
        description="github webhook server that pulls a branch when a remote push is made.")
    parser.add_argument(
        '--repo-dir',
        type=dir_path,default=DEFAULT_GIT_DIR)
    parser.add_argument(
        '--branch',
        help="git branch to monitor 'push' updates on",
        type=str,default=DEFAULT_BRANCH)
    parser.add_argument(
        '--port',
        help="port to listen to HTTP requests on",
        type=int,default=8080)
    args = parser.parse_args()

    # setup and start the server
    path_to_git = args.repo_dir
    branch_to_monitor = args.branch
    run(port=args.port)
