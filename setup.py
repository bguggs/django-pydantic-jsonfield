from setuptools import setup, find_packages

setup(
    name='pydantic-jsonfield',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    license='MIT',
    description='A Django JSONField extension using Pydantic for data validation.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Brian Guggenheimer',
    author_email='bguggs@gmail.com',
    url='https://github.com/bguggs/pydantic-jsonfield',
    install_requires=[
        'Django>=5.0',
        'pydantic>=2.0'
    ],
    classifiers=[
        'Framework :: Django',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
)