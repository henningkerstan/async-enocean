# (python-)enocean-core
This is a light-weight, asynchronous Python implementation of the EnOcean Serial Protocol Version 3 (ESP3) based on 'pyserial-asyncio-fast'. 

It is currently still a proof of concept (PoC) implementation loosely based on my previous [Node.js implementation](https://www.npmjs.com/package/enocean-core), so anything may change at anytime.

What works:
- Receiving ESP3 packets and parsing them into ERP1 telegrams
- Sending ESP3 packets (only tested with Common Command telegrams so far) incl. waiting for response (or time-out) and reacting to the response
- Retrieving EURID, Base ID and version info from the EnOcean module

What is missing/untested:
- Sending ERP1 telegrams
- Universal Teach-In (UTE) telegrams


## Development
After cloning this repository, execute the provided [scripts/setup.sh](scripts/setup.sh) to set up the development environment.

## Dependencies
This library only has one dependency, namely

- [pyserial-asyncio-fast](https://pypi.org/project/pyserial-asyncio-fast/) in version 0.16, which is BSD-3 licensed.


## Copyright & license
Copyright 2026 Henning Kerstan

Licensed under the Apache License, Version 2.0 (the "License"). See [LICENSE](./LICENSE) file for details.