import setuptools


def long_description():
    with open('README.md', 'r') as file:
        return file.read()

VERSION = "0.1.0"
setuptools.setup(
    name='singlebase',
    version=VERSION,
    author='Mardix/SinglebaseCloud.com',
    author_email='contact@singlebasecloud.com',
    description='Singlebase.cloud Python SDK',
    long_description=long_description(),
    long_description_content_type='text/markdown',
    url='https://github.com/singlebase/singlebase-py',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Topic :: Database',
    ],
    python_requires='>=3.10.0',
    install_requires = [
        "aiohttp",
        "arrow",
        "requests"
    ],
    packages=['singlebase'],
    package_dir={'':'src'}
)
