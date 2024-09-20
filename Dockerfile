FROM python:3.10-slim as build

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
COPY pipe/ requirements.txt LICENSE.txt pipe.yml /
# install requirements
RUN apt-get -y update && apt-get -y install --no-install-recommends curl=7.* \
    software-properties-common=0.* \
    unzip=6.* \
    gnupg=2.* && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --user --no-cache-dir -r /requirements.txt && \
    curl "https://releases.hashicorp.com/packer/1.11.2/packer_1.11.2_linux_amd64.zip" -o "packer.zip" && \
    echo 'ced13efc257d0255932d14b8ae8f38863265133739a007c430cae106afcfc45a packer.zip' | sha256sum -c - && \
    unzip -o packer.zip

# Final stage
FROM python:3.10-slim
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
WORKDIR /

COPY --from=build /packer /usr/bin
COPY --from=build /root/.local /root/.local
COPY --from=build pipe.py /
COPY --from=build LICENSE.txt pipe.yml /
ENV PATH=/root/.local/bin:$PATH

COPY pipe /
COPY LICENSE.txt pipe.yml /

ENTRYPOINT ["python", "/pipe.py"]