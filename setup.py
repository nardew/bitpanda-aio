import setuptools

with open("README.md", "r") as fh:
	long_description = fh.read()

setuptools.setup(
	name="bitpanda-aio",
	version="0.0.1",
	author="nardew",
	author_email="bitpanda.aio@gmail.com",
	description="Bitpanda Global Exchange API asynchronous python client",
	long_description=long_description,
	long_description_content_type="text/markdown",
	url="https://github.com/nardew/bitpanda-aio",
	packages=setuptools.find_packages(),
	classifiers=[
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
	],
	install_requires=[
		'aiohttp==3.5.4',
		'websockets==8.0.2',
		'pytz==2019.2'
	]
)
