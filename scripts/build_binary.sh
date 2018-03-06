#!/bin/bash -e

SCRIPT_NAME=${0##*/}
SCRIPT_DIR=${0%/${SCRIPT_NAME}}

BASE_DIR=$(realpath "${SCRIPT_DIR}/../")

if [ "$1" = "help" ]; then
    echo "Usages:"
    echo "${SCRIPT_NAME}                                   -- builds binary and rpm in dist/"
    echo "${SCRIPT_NAME} <'release-message'> <release-tag> -- builds and release binary on Github"
else
    set -e
    set -x

    sudo yum install rpm-build rpmdevtools python-devel -y
    sudo yum groupinstall "Development Tools" -y

    rpmdev-setuptree

    mkdir -vp "${BASE_DIR}/rpmbuild/SOURCES/treadmill-0.1"

    pushd "${BASE_DIR}"

    echo $2 > lib/python/treadmill/VERSION.txt

    cp -v dist/treadmill "${BASE_DIR}/rpmbuild/SOURCES/treadmill-0.1/treadmill"
    cp -v etc/treadmill.spec "${BASE_DIR}/rpmbuild/SPECS/"

    (
        pushd "${BASE_DIR}/rpmbuild/SOURCES/"
        tar cvf treadmill-0.1.0.tar.gz treadmill-0.1
    )

    rpmbuild -ba "${BASE_DIR}/rpmbuild/SPECS/treadmill.spec"
    cp -v ${BASE_DIR}/rpmbuild/RPMS/noarch/treadmill*rpm ${BASE_DIR}/dist/

