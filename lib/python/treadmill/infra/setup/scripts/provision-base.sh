# install
yum clean all
rpm -ivh https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
yum -y install python34 python-kerberos git python34-devel

# Configure
hostnamectl set-hostname "{{ HOSTNAME }}"

LDAP_DC=$(echo "{{ DOMAIN }}" | sed -E 's/([a-z]*)\.([a-z]*)/dc=\1,dc=\2/g')
LDAP_URL=ldap://{{ LDAP_HOSTNAME|lower }}:22389
ZK_URL={{ ZK_URL }}

grep -q -F 'preserve_hostname: true' /etc/cloud/cloud.cfg || echo 'preserve_hostname: true' >> /etc/cloud/cloud.cfg

# Setup environment vars for shell
(
cat <<EOF
export TREADMILL_ZOOKEEPER=$ZK_URL
export TREADMILL_LDAP=$LDAP_URL
export TREADMILL_LDAP_SUFFIX=${LDAP_DC}
export TREADMILL_CELL={{ SUBNET_ID }}
export TREADMILL_APPROOT={{ APP_ROOT }}
export TREADMILL_DNS_DOMAIN={{ DOMAIN }}
export TREADMILL=/opt/treadmill
export TREADMILL_ALIASES_PATH=node
export PEX_ROOT=/tmp/pex
export PATH=$PATH:/opt/s6/bin:/opt/treadmill/bin
export AWS_DEFAULT_REGION={{ REGION }}
export PROID={{ PROID }}
EOF
) >> /etc/profile.d/treadmill_profile.sh

# Setup environment vars for import
(
cat <<EOF
TREADMILL_ZOOKEEPER=$ZK_URL
TREADMILL_LDAP=$LDAP_URL
TREADMILL_LDAP_SUFFIX=${LDAP_DC}
TREADMILL_CELL={{ SUBNET_ID }}
TREADMILL_APPROOT={{ APP_ROOT }}
TREADMILL_DNS_DOMAIN={{ DOMAIN }}
TREADMILL=/opt/treadmill
TREADMILL_ALIASES_PATH=node
PEX_ROOT=/tmp/pex
PATH=$PATH:/opt/s6/bin:/opt/treadmill/bin
AWS_DEFAULT_REGION={{ REGION }}
PROID={{ PROID }}
EOF
) >> /etc/profile.d/treadmill_profile

source /etc/profile.d/treadmill_profile.sh >> ~/.bashrc
