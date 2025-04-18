# Dockerfile for Odoo 16
FROM odoo:16.0 as odoo16_enterprise

USER root

RUN python3 -m pip install -U pip && pip3 install pyOpenSSL

USER odoo

