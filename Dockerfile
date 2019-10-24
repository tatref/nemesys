FROM debian:buster

WORKDIR /root

RUN apt update && \
  DEBIAN_FRONTEND=noninteractive apt upgrade -yq && \
  DEBIAN_FRONTEND=noninteractive apt install -yq python3 python3-setuptools python3-dev python-virtualenv build-essential git libpcap-dev tshark && \
  useradd --create-home user

WORKDIR /home/user
USER user

RUN git clone --single-branch -b fix-layer-build https://github.com/skleber/netzob.git

COPY --chown=user:user requirements_0.txt requirements.txt /home/user/nemesys/

RUN virtualenv -p python3 ~/virtualenv && \
  . ~/virtualenv/bin/activate && \
  pip install -r ~/nemesys/requirements_0.txt && \
  pip install -r ~/nemesys/requirements.txt && \
  echo '. ~/virtualenv/bin/activate' >> ~/.bashrc

RUN . ~/virtualenv/bin/activate && \
  cd netzob/netzob && \
  python setup.py build && \
  python setup.py develop && \
  python setup.py install

COPY --chown=user:user . nemesys/

#RUN . ~/virtualenv/bin/activate && \
#  cd nemesys && \
#  pip install -r requirements.txt

CMD ~/virtualenv/bin/ipython
