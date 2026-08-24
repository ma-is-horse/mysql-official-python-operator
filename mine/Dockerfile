FROM mysql-operator-python-deps:3.10.8-amd64

RUN rpm -U http://repo.mysql.com/mysql80-community-release-el8.rpm \
&& microdnf update && echo "[main]" > /etc/dnf/dnf.conf \
&& microdnf install --enablerepo=mysql-tools-community -y glibc-langpack-en mysql-shell-8.3.0 \
&& microdnf remove mysql80-community-release \
&& microdnf clean all

RUN groupadd -g27 mysql && useradd -u27 -g27 mysql
RUN mkdir /mysqlsh && chown 2 /mysqlsh

COPY mysqloperator/ /usr/lib/mysqlsh/python-packages/mysqloperator

# Workaround for BC issue with newest Python library for Kubernetes
RUN sed -i "s/available_replicas=None,/available_replicas=0,/" /usr/lib/mysqlsh/python-packages/kubernetes/client/models/v1_stateful_set_status.py

USER 2
ENV HOME=/mysqlsh