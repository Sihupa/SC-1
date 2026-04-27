# SC-1
SC-1 is an experimental, minimal virtual computer architecture and its own emulator.

## Installation and Usage
For installing SC-1, clone this repository and run:

    pip install -r requirements.txt

Command format:

    python3 run_sc1.py [-h] [--mem-size BYTES] [--entry ADDR] [--max-steps N] [--mem-u16 ADDR] [--pygame] [--storage-dir DIR] program

Included example programs:
- examples/counter.sc1
- examples/disk_mkdir_and_write.sc1
- examples/disk_write_demo.sc1
- examples/interrupt_hello.sc1
- examples/interrupt_print_number.sc1
- examples/sum_1_to_10.sc1
- examples/x_pointer_increment.sc1


## Copyirght and License
Copyright (c) 2026 Erdem Ersoy (eersoy93)

Licensed with MIT license. See COPYING for license text.
