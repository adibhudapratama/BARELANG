FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /opt/cargo_hold_v6
COPY install_dependencies.sh /tmp/install_dependencies.sh
RUN bash /tmp/install_dependencies.sh && rm -rf /var/lib/apt/lists/*
COPY . .
RUN cmake -S . -B /tmp/cargo_build -DCMAKE_BUILD_TYPE=Release && cmake --build /tmp/cargo_build -j2
ENV CARGO_PROJECT_ROOT=/opt/cargo_hold_v6
ENV GZ_SIM_RESOURCE_PATH=/opt/cargo_hold_v6/models
ENV GZ_SIM_SYSTEM_PLUGIN_PATH=/tmp/cargo_build
ENV CARGO_REPLAY_SPEED=10
CMD ["gz", "sim", "-s", "-r", "-v", "3", "worlds/cargo_hold_cutaway.sdf"]
