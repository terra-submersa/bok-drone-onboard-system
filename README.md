# BOK Drone Onboard System
version=0.1.11


### Pypi package build and deploy
    # pip install build

    # commit changes
    bumpver update --patch # or --minor --major

    python -m build

    # Only upload the latest version
    twine upload $(ls -rt dist/* | grep .tar.gz | sed s/.tar.gz// | tail -1)*


### Drone side
#### Upgrade deployment on Raspbery PI

    pip install --upgrade bok-drone-onboard-system

