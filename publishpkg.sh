 # publishpkg.sh
 # script to help build and deploy packages on Pypi

 python3 -m pip install --upgrade build
 python3 -m build 
 twine upload dist/*  