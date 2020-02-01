import setuptools

with open("README.md", "r") as fh:
	long_description = fh.read()

setuptools.setup(
	name="bitpanda-aio",
	version="1.0.1",
	author="nardew",
	author_email="bitpanda.aio@gmail.com",
	description="Bitpanda Global Exchange API asynchronous python client",
	long_description=long_description,
	long_description_content_type="text/markdown",
	url="https://github.com/nardew/bitpanda-aio",
	packages=setuptools.find_packages(),
	classifiers=[
		"Development Status :: 4 - Beta",
		"Framework :: AsyncIO",
		"Intended Audience :: Developers",
		"Programming Language :: Python :: 3",
		"Programming Language :: Python :: 3.6",
		"Programming Language :: Python :: 3.7",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
		"Topic :: Software Development :: Libraries",
		"Topic :: Software Development :: Libraries :: Python Modules",
		"Typing :: Typed",
	],
	install_requires=[
		'aiohttp==3.6.2',
		'websockets==8.1',
		'pytz==2019.3'
	],
	python_requires='>=3.6',
)
