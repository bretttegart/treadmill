# install
yum install -y ipa-client 

ipa-client-install --unattended --no-ntp \
    --mkhomedir --no-krb5-offline-password \
    --password '{{ OTP }}' --enable-dns-updates

# /etc/krb5.conf
# 
# comment this out:
#
#   [libdefaults]
#       default_ccache_name = KEYRING:persistent:%{uid}
#
# why:
# * do not want sshd to use same credentials file across for all ssh sessions
#   by the same user
# * sshd will use mktemp to create cred cache, location is now
#   /tmp/krb5cc_${uid}_XXXXXXXXXX
# * allows us to cleanup cred cache at end of ssh session by setting
#   /etc/ssh/sshd_config:GSSAPICleanupCredentials to yes
#sed --in-place -e s/default_ccache_name/#default_ccache_name/ /etc/krb5.conf

# /etc/ssh/ssh_config
#
# * enable ticket forwarding (GSSAPIDelegateCredentials)
# * enable gssapi key exchange (GSSAPIKeyExchange) 
#   [arguably not needed with freeipa]
#(
#cat <<EOF
#Host *
#    GSSAPIAuthentication yes
#    GSSAPIDelegateCredentials yes
#    GSSAPIKeyExchange yes
#EOF
#) >> /etc/ssh/ssh_config

# /etc/ssh/sshd_config
# 
# change these GSSAPI settings from:
#
#   # GSSAPI options
#   GSSAPIAuthentication yes
#   GSSAPICleanupCredentials no
#   #GSSAPIStrictAcceptorCheck yes
#   #GSSAPIKeyExchange no
#   #GSSAPIEnablek5users no
#
# to:
#
#   # GSSAPI options
#   GSSAPIAuthentication yes
#   GSSAPICleanupCredentials yes
#   GSSAPIStrictAcceptorCheck no
#   GSSAPIKeyExchange yes
#   GSSAPIEnablek5users no
#
# why:
# * clean up credentials so that tickets don't hang around after ssh session
#   has terminated
# * enable GSSAPIKeyExchange avoids noise in ssh known_hosts file
# * make other configs explicit
#sed --in-place -e 's/GSSAPICleanupCredentials no/GSSAPICleanupCredentials yes/' /etc/ssh/sshd_config
#sed --in-place -e 's/#GSSAPIStrictAcceptorCheck yes/GSSAPIStrictAcceptorCheck no/' /etc/ssh/sshd_config
#sed --in-place -e 's/#GSSAPIKeyExchange no/GSSAPIKeyExchange yes/' /etc/ssh/sshd_config
#sed --in-place -e 's/#GSSAPIEnablek5users/GSSAPIEnablek5users/' /etc/ssh/sshd_config
#sed --in-place -e 's/^PubkeyAuthentication yes/PubkeyAuthentication no/' /etc/ssh/sshd_config
#kill -HUP $(cat /var/run/sshd.pid)

########################################################################
# BEGIN: STUFF THAT SHOULD REMOVED BY THE AMI USED FOR TREADMILL NODES #
########################################################################

# passwd/shadow maps - remove ec2-user user and group
#userdel ec2-user # this removes user and group

# /etc/sudoers - remove ec2-user sudoers rule
#sed --in-place -e '/ec2-user/d' /etc/sudoers
#rm -f /etc/sudoers.d/90-cloud-init-users

# where: ~ec2-user/*
# what: remove ~ec2-user home directory and .ssh /authorized_keys
#rm -rf /home/ec2-user

########################################################################
# BEGIN: STUFF THAT SHOULD REMOVED BY THE AMI USED FOR TREADMILL NODES #
########################################################################


