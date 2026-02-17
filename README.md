# enocean-async
This is a light-weight, asynchronous, fully typed Python implementation of the [EnOcean Serial Protocol Version 3 (ESP3)](https://www.enocean.com/wp-content/uploads/Knowledge-Base/EnOceanSerialProtocol3-1.pdf) based on [pyserial-asyncio-fast](https://pypi.org/project/pyserial-asyncio-fast/). 

**It is currently still a proof of concept (PoC) implementation loosely based on my previous [Node.js implementation](https://www.npmjs.com/package/enocean-core), so anything may change at anytime!**

What works:
- Receiving ESP3 packets and parsing them into ERP1 telegrams
- Sending ESP3 packets (only tested with Common Command telegrams so far) incl. waiting for response (or time-out) and reacting to the response
- Retrieving EURID, Base ID and version info from the EnOcean module
- Changing the Base ID
- Sending ERP1 telegrams
- Parsing EEPs (with F6-02-01 as tested/implemented example)
- Parse Universal Teach-In (UTE) Queries
- logging (partially)

What is missing/untested:
- create and send Universal Teach-In (UTE) responses
- handle Teach-in (UTE, 4BS, 1BS)



## Contributing
See [CONTRIBUTING](https://github.com/henningkerstan/enocean-async/blob/main/CONTRIBUTING.md).


## Dependencies
This library only has one dependency, namely

- [pyserial-asyncio-fast](https://pypi.org/project/pyserial-asyncio-fast/) in version 0.16, which is BSD-3 licensed.


## Copyright & license
Copyright 2026 Henning Kerstan

Licensed under the Apache License, Version 2.0 (the "License"). See [LICENSE](./LICENSE) file for details.