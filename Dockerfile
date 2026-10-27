FROM alpine:3.24 AS base
RUN apk update && apk upgrade && apk add python3 gcc g++ python3-dev

FROM base AS rust-builder
RUN apk update && apk upgrade && apk add rustup
RUN rustup-init -y
COPY toolchain/ /build/toolchain
WORKDIR /build/toolchain
RUN ~/.cargo/bin/cargo build --release

FROM base
ARG UID=1000
RUN apk add texlive texmf-dist-latexextra texmf-dist-fontsrecommended
RUN adduser -u $UID -h /build -D user
USER user
COPY --from=rust-builder --chown=user /build/toolchain/target/release/toolchain /build/toolchain
COPY --chown=user scripts/ /build/scripts
WORKDIR /build/scripts
RUN python3 -m venv env && env/bin/pip install -r requirements.txt
WORKDIR /build
