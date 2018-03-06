cat <<EOF >> /var/tmp/cellapi.yml
{% include 'manifests/cellapi.yml' %}
EOF

cat <<EOF >> /var/tmp/adminapi.yml
{% include 'manifests/adminapi.yml' %}
EOF

cat <<EOF >> /var/tmp/stateapi.yml
{% include 'manifests/stateapi.yml' %}
EOF

su -c "{{ TREADMILL }} admin master app schedule --env prod --proid ${PROID} --manifest /var/tmp/cellapi.yml ${PROID}.cellapi" "${PROID}"
su -c "{{ TREADMILL }} admin master app schedule --env prod --proid ${PROID} --manifest /var/tmp/adminapi.yml ${PROID}.adminapi" "${PROID}"
su -c "{{ TREADMILL }} admin master app schedule --env prod --proid ${PROID} --manifest /var/tmp/stateapi.yml ${PROID}.stateapi" "${PROID}"
