FROM python:latest

ENV STRONGSWAN_VERSION="5.9.3"
ENV DEBIAN_FRONTEND=noninteractive
ARG BUILD_OPTIONS=""

# Update image and install additional packages
# -----------------------------------------------------------------------------
RUN \
  # install packages
  DEV_PACKAGES="bzip2 make gcc libcurl4-openssl-dev libgmp-dev libssl-dev" && \
  apt-get -y update && \
  apt-get -y install \
    supervisor\
    bind9 \
    libcurl4 libgmp10 \
    # libssl1.0.0 \
    # module-init-tools \
    $DEV_PACKAGES && \
  \
  # download and build strongswan source code
  mkdir /strongswan-build && \
  cd /strongswan-build && \
  wget https://download.strongswan.org/strongswan-$STRONGSWAN_VERSION.tar.bz2 && \
  tar -xjf strongswan-$STRONGSWAN_VERSION.tar.bz2 && \
  cd strongswan-$STRONGSWAN_VERSION && \
  ./configure --prefix=/usr --sysconfdir=/etc --enable-af-alg --enable-ccm --enable-curl --enable-eap-dynamic --enable-eap-identity --enable-eap-tls --enable-files --enable-gcm --enable-openssl $BUILD_OPTIONS && \
  make all && make install && \
  cd / && rm -R /strongswan-build && \
  \
  # clean up
  apt-get -y remove $DEV_PACKAGES && \
  apt-get -y autoremove && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*

# Copy prepared files into the image
# -----------------------------------------------------------------------------
COPY target /

# Adjust permissions of copied files
# -----------------------------------------------------------------------------
RUN chmod 750 /entrypoint.sh /docker-startup/run-startup.sh /etc/strongswan-updown.sh && \
  # add starting the application to .bashrc of root to support the 'run-and-enter' mode
  # and let it terminate before the opened shell exits
  echo 'if [[ "${RUN_DOCKER_APP}" -eq "1" ]]; then' >> /root/.bashrc && \
  echo '  /docker-startup/run-app.sh > /var/log/app-stdout.log 2> /var/log/app-stderr.log &' >> /root/.bashrc && \
  echo '  export DOCKER_APP_PID=$!' >> /root/.bashrc && \
  echo '  trap "kill ${DOCKER_APP_PID}" EXIT' >> /root/.bashrc && \
  echo '  echo "The application was started, its stdout/stderr is logged to /var/log/app-[stdout|stderr].log."' >> /root/.bashrc && \
  echo 'fi' >> /root/.bashrc

# Volumes
# -----------------------------------------------------------------------------
VOLUME [ "/data" ]

# Expose ports
# -----------------------------------------------------------------------------
# 500/udp  - Internet Key Exchange (IKE)
# 4500/udp - NAT Traversal
# -----------------------------------------------------------------------------
EXPOSE 500 4500

ENTRYPOINT ["/entrypoint.sh"]
CMD ["run"]
