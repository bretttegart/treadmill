setenforce 0
sed -i -e 's/SELINUX=enforcing/SELINUX=permissive/g' /etc/selinux/config

echo Installing Node packages

yum-config-manager --enable rhui-REGION-rhel-server-extras
yum -y install conntrack-tools iproute libcgroup libcgroup-tools bridge-utils openldap-clients lvm2* ipset iptables rrdtool bc docker-latest

source /etc/profile.d/treadmill_profile.sh

mkdir /var/spool/keytabs-proids && chmod 755 /var/spool/keytabs-proids
mkdir /var/spool/keytabs-services && chmod 755 /var/spool/keytabs-services
mkdir /var/spool/tickets && chmod 755 /var/spool/tickets

# force default back to FILE: from KEYRING:
cat <<%E%O%T | sudo su - root -c 'cat - >/etc/krb5.conf.d/default_ccache_name'
[libdefaults]
  default_ccache_name = FILE:/var/spool/tickets/%{username}
%E%O%T

kinit -kt /etc/krb5.keytab

# Retrieving ${PROID} keytab
ipa-getkeytab -r -p "${PROID}" -D "cn=Directory Manager" -w "{{ IPA_ADMIN_PASSWORD }}" -k /var/spool/keytabs-proids/"${PROID}".keytab
chown "${PROID}":"${PROID}" /var/spool/keytabs-proids/"${PROID}".keytab


(
cat <<EOF
kinit -k -t /var/spool/keytabs-proids/${PROID}.keytab -c /var/spool/tickets/${PROID}.tmp ${PROID}
chown ${PROID}:${PROID} /var/spool/tickets/${PROID}.tmp
mv /var/spool/tickets/${PROID}.tmp /var/spool/tickets/${PROID}
EOF
) > /etc/cron.hourly/"${PROID}"-kinit


chmod 755 /etc/cron.hourly/"${PROID}"-kinit
/etc/cron.hourly/"${PROID}"-kinit

# Docker configuration
(
cat <<EOF
DOCKER_NETWORK_OPTIONS=\
  --bridge=none\
  --ip-forward=false\
  --ip-masq=false\
  --iptables=false
EOF
) > /etc/sysconfig/docker-latest-network

systemctl enable docker-latest --now


(
TIMEOUT=30
retry_count=0
until ( ldapsearch -c -H $TREADMILL_LDAP "ou=cells" ) || [ $retry_count -eq $TIMEOUT ]
do
    retry_count=$(($retry_count+1))
    sleep 30
done
)

{{ TREADMILL }} --outfmt yaml admin ldap cell configure "{{ SUBNET_ID }}" > /var/tmp/cell_conf.yml

(
cat <<EOF
{"treadmill_runtime": "docker2", "localdisk_default_read_iops": 100000, "localdisk_default_write_bps": "1G", "localdisk_default_read_bps": "1G"}
EOF
) > /var/tmp/server.json

su -c 'treadmill admin ldap server configure "$(hostname -f)" --data /var/tmp/server.json' "${PROID}"

touch /etc/ld.so.preload
touch /etc/treadmill_bind_preload.so

(
cat <<EOF 
[Unit]
Description=Treadmill node services
After=network.target

[Service]
User=root
Group=root
SyslogIdentifier=treadmill
ExecStart={{ APP_ROOT }}/bin/run.sh
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
) > /etc/systemd/system/treadmill-node.service

su -c '{{ TREADMILL }} admin install \
       --install-dir {{ APP_ROOT }} \
       --config /var/tmp/cell_conf.yml \
       --override "network_device=eth0 rrdtool=/usr/bin/rrdtool rrdcached=/usr/bin/rrdcached" \
       node' treadmld

su -c "mkdir -p {{ APP_ROOT }}/var/tmp {{ APP_ROOT }}/var/run" "${PROID}"
ln -s /var/spool/tickets/"${PROID}" {{ APP_ROOT }}/spool/krb5cc_host

s6-setuidgid "${PROID}" {{ TREADMILL }} admin ldap server configure "$(hostname -f)" --cell "{{ SUBNET_ID }}"

# Configure cgroups for docker2 runtime
echo 1 > /sys/fs/cgroup/cpuset/cgroup.clone_children


/bin/systemctl daemon-reload
/bin/systemctl enable treadmill-node.service --now

