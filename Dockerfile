FROM debian:latest

ENV DEBIAN_FRONTEND=noninteractive
ENV CARGO_NET_GIT_FETCH_WITH_CLI=true
ENV CARGO_HTTP_MULTIPLEXING=false
ARG BUILD_OPTIONS=""

# Update image and install additional packages
# -----------------------------------------------------------------------------
RUN \
  # install packages py cryptography dep and strongswan dep
  apt-get -y update && \
  apt-get -y install \
    git \
    python3 \
    python3-pip \
    build-essential \
    curl \
    libssl-dev \
    libffi-dev \
    python3-dev \
    cargo \
    pkg-config \
    iptables \
    supervisor \
    bind9 \
    libcurl4 libgmp10 \
    kmod \
    strongswan \
    strongswan-swanctl

# Copy prepared files into the image
# -----------------------------------------------------------------------------
COPY target /

# Install python packages
# -----------------------------------------------------------------------------
RUN pip install -r /docker-startup/10-initial.startup/gp_startup/requirements.txt

# Clean up
# -----------------------------------------------------------------------------
RUN apt-get -y autoremove && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/* && \
  rm -Rf /root/.cache/pip

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
EXPOSE 500/udp 4500/udp

ENTRYPOINT ["/entrypoint.sh"]
CMD ["run"]
