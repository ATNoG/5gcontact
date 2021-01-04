#!/bin/bash
echo "Loggin into MAAS"
PROFILE=admin
API_KEY_FILE=/home/ubuntu/admin_key
API_SERVER=192.168.1.250:5240

MAAS_URL=http://$API_SERVER/MAAS/api/2.0

maas login $PROFILE $MAAS_URL - < $API_KEY_FILE >/dev/null
echo "Log in succes"
echo -en '\n'

echo "Listing Machines"
maas admin machines read | jq -r '(["HOSTNAME","SYSID","STATUS", "TAGS"] | (., map(length*"-"))), (.[] | (select(.status_name=="Ready") | [.hostname, .system_id, .status_name, .tag_names[0]])) | @tsv' | column -t | (sed$
echo -en '\n'

echo "Choose machine ID to deploy"
read machine_id

echo -en '\n'
echo "Choose Script:"
read script

echo -en '\n'
echo "Deploying machine $machine_id with the script $script"
maas admin machine deploy $machine_id user_data=$(base64 -w0 ./$script) >/dev/null
echo "Deployment started"

