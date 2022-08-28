#!/usr/bin/sh
# script that automatically pulls a git branch when a push is made

# SSH deploy key (read only) used to pull from repo
# Note: needs to have no passphase so we can do headless `ssh-add`
SSH_DEPLOY_KEY_PATH=/home/user/.ssh/my-deploy-key
REPO_DIR=/home/user/git/my-repo/
GIT_BRANCH=master
PORT=4567

# setup ssh key so we can pull
eval $(ssh-agent)
ssh-add $SSH_DEPLOY_KEY_PATH

# start the pull bot
python3 webhook-server.py --port $PORT --branch $GIT_BRANCH --repo-dir $REPO_DIR 
