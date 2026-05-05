FROM python:3.10-slim

# Bullseye's OpenSSL defaults to SECLEVEL=2 which causes TLS handshake failures
# with MongoDB Atlas. Lowering to SECLEVEL=1 fixes the SSL internal error.
RUN sed -i 's/DEFAULT@SECLEVEL=2/DEFAULT@SECLEVEL=1/' /etc/ssl/openssl.cnf

WORKDIR /app
CMD bash -c "pip install -r requirements.txt && python app.py"
