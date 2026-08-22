#!/bin/bash
# OAPA CopyEditor AI - Ubuntu Server Setup

cd ~
git clone https://github.com/HN-678/copy-editor-ai.git
cd copy-editor-ai

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
echo "Fill in your API keys in .env before starting the service"

# Copy systemd service file
sudo cp oapa/copyeditor.service /etc/systemd/system/copyeditor.service
echo "Edit /etc/systemd/system/copyeditor.service and replace YOUR_USERNAME"

sudo systemctl daemon-reload
sudo systemctl enable copyeditor
sudo systemctl start copyeditor

echo "Done. Check status with: sudo systemctl status copyeditor"
