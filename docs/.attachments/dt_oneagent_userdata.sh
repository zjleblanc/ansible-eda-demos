#!/bin/bash
dnf update -y

# use tag as hostname
TOKEN=`curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 900"`
NAME=`curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/tags/instance/Name`
hostnamectl set-hostname $NAME

dnf install -y wget
# install dynatrace agent
wget  -O Dynatrace-OneAgent-Linux-1.285.113.20240227-120645.sh "https://{{ DT_HOST }}/api/v1/deployment/installer/agent/unix/default/latest?arch=x86" --header="Authorization: Api-Token {{ DT_API_TOKEN }}"
wget https://ca.dynatrace.com/dt-root.cert.pem ; ( echo 'Content-Type: multipart/signed; protocol="application/x-pkcs7-signature"; micalg="sha-256"; boundary="--SIGNED-INSTALLER"'; echo ; echo ; echo '----SIGNED-INSTALLER' ; cat Dynatrace-OneAgent-Linux-1.285.113.20240227-120645.sh ) | openssl cms -verify -CAfile dt-root.cert.pem > /dev/null
/bin/sh Dynatrace-OneAgent-Linux-1.285.113.20240227-120645.sh --set-monitoring-mode=fullstack --set-app-log-content-access=true

reboot
