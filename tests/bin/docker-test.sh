#!/usr/bin/env sh
set -eu
unset CDPATH
cd "$( dirname "$0" )/../.."

USAGE="
Usage:
    $0 [OPTION...] [[--] TEST_ARGS...]
Run tests in a docker container.
Options:
    -h, --help      Print this help and exit
    -- TEST_ARGS    Arguments passed to tests.sh
"

main() {
    BUILD_IMAGE=1
    DOCKERFILE="tests/Dockerfile"
    DOCKER_TAG="testing"
    ENTRY_POINT="--entrypoint=/src/tests/bin/tests.sh"
    while [ $# -gt 0 ]; do
        case "$1" in
            -h|--help)
                printf "$USAGE" >&2
                exit 0
                ;;
            -B|--no-build)
                BUILD_IMAGE=
                ;;
            -s|--shell)
                ENTRY_POINT="--entrypoint=/bin/bash"
                ;;
            --)
                shift
                break
                ;;
            *)
                break
                ;;
        esac
        shift
    done

    DOCKER_IMAGE="flywheel/bids-app-template:${DOCKER_TAG}"

    VER=$(cat manifest.json | jq -r '.version')
    DOCKER_IMAGE_NAME=$(cat manifest.json | jq '.custom."gear-builder".image')
    DOCKER_IMAGE_NAME=$( echo $DOCKER_IMAGE_NAME | tr -d '"' )
    echo "DOCKER_IMAGE_NAME is" $DOCKER_IMAGE_NAME 

    if [ "${BUILD_IMAGE}" == "1" ]; then

        echo docker build -f "${DOCKERFILE}" \
          --build-arg DOCKER_IMAGE_NAME=${DOCKER_IMAGE_NAME} \
          -t "${DOCKER_IMAGE}" .

        docker build -f "${DOCKERFILE}" \
          --build-arg DOCKER_IMAGE_NAME=${DOCKER_IMAGE_NAME} \
          -t "${DOCKER_IMAGE}" .

    fi

    echo docker run -it --rm \
        --volume "$(pwd):/src" \
        --volume "$HOME/.config/flywheel:/root/.config/flywheel" \
        "${ENTRY_POINT}" \
        "${DOCKER_IMAGE}" \
        "$@"

    docker run -it --rm \
        --volume "$(pwd):/src" \
        --volume "$HOME/.config/flywheel:/root/.config/flywheel" \
        "${ENTRY_POINT}" \
        "${DOCKER_IMAGE}" \
        "$@"

}

main "$@"