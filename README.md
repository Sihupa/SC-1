# SC-1
SC-1 is a minimal virtual computer architecture and its own emulator.

## Usage

1. Install dependencies:
	python3 -m pip install -r requirements.txt

2. Run an example program:
	python3 run_sc1.py examples/counter.sc1

3. Run with custom options:
	python3 run_sc1.py examples/sum_1_to_10.sc1 --entry 0 --max-steps 1000000

4. Use disk syscalls (storage directory is created automatically if missing):
	python3 run_sc1.py examples/disk_mkdir_and_write.sc1

5. Render output in a pygame window:
	python3 run_sc1.py examples/interrupt_hello.sc1 --pygame

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
