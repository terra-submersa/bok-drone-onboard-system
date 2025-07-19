# BOK Drone Onboard System
version=0.1.4


### Pypi package build and deploy
    # pip install build

    # commit changes
    bumpver update --patch # or --minor --major

    rm -rf dist/
    python -m build

    
    twine upload dist/*

#### Upgrade deployment on Raspbery PI

    pip install --upgrade bok-drone-onboard-system
