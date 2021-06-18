from setuptools import setup

setup(
	name="bl4p_server",
	version="0.0.1",
	packages=["bl4p_server", "bl4p_server.api"],
	include_package_data=True,
	entry_points={"console_scripts": ["bl4p_server = bl4p_server.__main__:main"]},
	install_requires=[
		"websockets>=8.1",
		"protobuf>=3.6.1",
		"secp256k1>=0.13.2",
	],
	extras_require={"testing": ["coverage>=4.5.2", "websocket-client>=0.53.0", "black"]},
)
