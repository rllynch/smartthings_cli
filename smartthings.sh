#!/bin/bash

### Wrapper script to run smartthings_cli from a Docker container

docker run -it --rm smartthings smartthings_cli ${1} ${2} ${3}
