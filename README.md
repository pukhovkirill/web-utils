# **Web-utils**

**Utilities for working on the network.**

## Table of Contents

* [Features](#features)
* [Installation](#installation)
* [Examples](#examples)
* [Modules](#modules)
* [License](#license)


## Features

`web-utils` offers the following capabilities:

* **Website parsing**: extract data from HTML and export it as JSON, CSV, or YAML.
* **Network diagnostics**: `ping`, `traceroute`, `speedtest`, `dns-lookup`
* **Format conversion**: JSON ↔ CSV ↔ YAML ↔ XML
* **QR codes**: generation and reading
* **Email utilities**: address validation, sending and receiving mail


## Installation

Requires Python ≥ 3.11

1. **Install from git**

   ```bash
   pip install git+https://github.com/pukhovkirill/web-utils.git
   ```
2. **Local development install**

   ```bash
   git clone https://github.com/pukhovkirill/web-utils.git
   cd web-utils
   pip install -e .
   ```


## Examples

A demonstration notebook with examples for all main modules is included in the repository:

```bash
jupyter notebook docs/examples.ipynb
```
[Open the examples notebook](docs/example.ipynb)


## Modules

```
web-utils
├── docs
│   ├── example.ipynb
│   └── requirements.txt
├── webutils
│   ├── converter
│   │   ├── csv
│   │   │   └── csv_converter.py
│   │   ├── json
│   │   │   └── json_converter.py
│   │   ├── xml
│   │   │   └── xml_converter.py
│   │   ├── yaml
│   │   │   └── csv_converter.py
│   │   ├── abc_converter.py
│   │   └── ast.py
│   ├── email_utils
│   │   ├── email_validator.py
│   │   └── simple_mailer.py
│   ├── network
│   │   ├── dns
│   │   │   └── dns_lookup.py
│   │   ├── icmp
│   │   │   ├── icmp_proto.py
│   │   │   ├── icmp_utils.py
│   │   │   ├── ping.py
│   │   │   └── traceroute.py
│   │   └── speedtest
│   │       └── speed_test.py
│   ├── parser
│   │   ├── save_strategies.py
│   │   └── scraper.py
│   ├── qr
│   │   ├── qr_generator.py
│   │   └── qr_reader.py
├── tests
│   ├── converter
│   │   ├── csv_converter_test.py
│   │   ├── json_converter_test.py
│   │   ├── xml_converter_test.py
│   │   └── yaml_converter_test.py
│   ├── email_utils
│   │   ├── email_validator_test.py
│   │   └── simple_mailer_test.py
│   ├── network
│   │   ├── dns_lookup_test.py
│   │   ├── icmp_utils_test.py
│   │   ├── ping_test.py
│   │   ├── speedtest_test.py
│   │   └── traceroute_test.py
│   ├── parser
│   │   └── scraper_test.py
│   └── qr
│       ├── qr_generator_test.py
│       └── qr_reader_test.py
├── pyproject.toml
├── README.md
└── LICENSE
```


## License

Copyright (c) 2025 Pukhov Kirill \
Distributed under the MIT License. See the LICENSE file for details.
