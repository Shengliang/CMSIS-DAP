"""
CMSIS-DAP Interface Firmware
Copyright (c) 2009-2013 ARM Limited

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


This script takes in output a .bin file associated to a flash algo:
   fromelf --bin flash_algo.FLM -o out

Then in the folder out, there is a file called PrgCode. This file is the binary which contains the flash algo

Then it generates a new file containing an array which can then be used by the interface firmware
"""
from struct import unpack
from utils import run_cmd
from settings import *


ALGO_ELF_PATH = "./out/flash_algo.axf"
ALGO_BIN_PATH = "./out/PrgCode"
ALGO_TXT_PATH = "./out/flash_algo.txt"

ALGO_START  = 0x10000000
ALGO_OFFSET = 0x20


def gen_flash_algo():
    run_cmd(['fromelf', '--bin', ALGO_ELF_PATH, '-o', 'out'])
    with open(ALGO_BIN_PATH, "rb") as f, open(ALGO_TXT_PATH, mode="w+") as res:
        # Flash Algorithm
        res.write("""
const uint32_t flash_algo_blob[] = {
    0xE00ABE00, 0x062D780D, 0x24084068, 0xD3000040, 0x1E644058, 0x1C49D1FA, 0x2A001E52, 0x4770D1F2,\n
    /*0x020*/ """);
        
        nb_bytes = 0x20
        
        bytes_read = f.read(1024)
        while bytes_read:
            bytes_read = unpack(str(len(bytes_read)/4) + 'I', bytes_read)
            for i in range(len(bytes_read)):
                res.write(hex(bytes_read[i]) + ", ")
                nb_bytes += 4
                if (nb_bytes % 0x20) == 0:
                    res.write("\n    /*0x%03X*/ " % nb_bytes)
            bytes_read = f.read(1024)
        
        res.write("\n};\n")
        
        # Address of the functions within the flash algorithm
        stdout, _, _ = run_cmd(['fromelf', '-s', ALGO_ELF_PATH])
        res.write("""
static const TARGET_FLASH flash = {
""")
        for line in stdout.splitlines():
            t = line.strip().split()
            if len(t) != 8: continue
            name, loc = t[1], t[2]
            
            if name in ['Init', 'UnInit', 'EraseChip', 'EraseSector', 'ProgramPage']:
                addr = ALGO_START + ALGO_OFFSET + int(loc, 16)
                res.write("    0x%X, // %s\n" % (addr,  name))


if __name__ == '__main__':
    gen_flash_algo()

