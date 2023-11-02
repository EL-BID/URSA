FROM condaforge/mambaforge

USER root

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y git build-essential

USER $MAMBA_USER

COPY --chown=$MAMBA_USER:$MAMBA_USER env.yaml /tmp/env.yaml

RUN mamba env create -n ursa -f /tmp/env.yaml && mamba clean --all --yes

RUN mkdir app
WORKDIR app
COPY . .

RUN mamba run -n ursa pip install --no-dependencies -e .

EXPOSE 8050

CMD ["mamba", "run", "--no-capture-output", "-n", "ursa", "python", "-u", "app.py"]