"""CPU functionality."""

import sys

SP = 7
STACK_START = 0xF4

class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""
        self.ram = [0] * 256
        self.reg = [0] * 8
        self.reg[SP] = STACK_START # SP
        self.pc = 0
        self.fl = 0
        self.alu_dispatch = {
            0b0000: self.handle_add,
            0b0010: self.handle_mul
        }
        self.pc_dispatch = {
            0b0000: self.handle_call,
            0b0001: self.handle_ret
        }
        self.op_dispatch = {
            0b0010: self.handle_ldi,
            0b0111: self.handle_prn,
            0b0101: self.handle_push,
            0b0110: self.handle_pop,
            0b0001: self.handle_hlt
        }

    def handle_call(self, reg_value):
        # Hard coding 2nd operand - instruction directly after CALL
        self.handle_push()

        self.pc = self.reg[reg_value]

    def handle_ret(self):
        # Pops SP and makes self.reg[SP] = next instruction after subroutine
        popped_value = self.handle_pop()

        self.pc = popped_value

    def handle_hlt(self):
        raise Exception

    def handle_push(self, reg_value=None):
        # If at top of stack, stop CPU
        if self.reg[SP] == 0:
            print("Stack Overflow, stopping CPU.")
            self.handle_hlt()
            return

        # Decrement SP
        self.reg[SP] -= 1

        if reg_value is not None:
            # Get address pointed by SP, copy given reg value into address
            self.ram_write(self.reg[SP], self.reg[reg_value])
        else:
            self.ram_write(self.reg[SP], self.pc + 2)

    def handle_pop(self, reg_value=None):
        # Need to fix this
        # Get value from SP, save to given reg value
        if reg_value is not None:
            self.reg[reg_value] = self.ram_read(self.reg[SP])

            # Increment SP
            self.reg[SP] += 1

            # If at bottom of stack, resets stack back to start
            if self.reg[SP] > STACK_START:
                print("Stack underflow, resetting stack.")
                self.reg[SP] = STACK_START

            return self.reg[reg_value]
        else:
            popped_value = self.ram_read(self.reg[SP])

            return popped_value

    def handle_ldi(self, op1, op2):
        self.reg[op1] = op2

    def handle_prn(self, op1):
        print(self.reg[op1])

    def handle_add(self, reg_a, reg_b):
        self.reg[reg_a] += self.reg[reg_b]

    def handle_mul(self, reg_a, reg_b):
        self.reg[reg_a] *= self.reg[reg_b]

    def load(self):
        """Load a program into memory."""

        if len(sys.argv) != 2:
            print("Usage: comp.py filename")
            sys.exit(1)

        address = 0

        # Dynamically opens a .ls8 file, depending on the argv
        program = []

        rel_file = sys.argv[1]
        f = open(rel_file)
        f_lines = f.readlines()

        # Can have a better implementation of cleaning up lines
        for lines in f_lines:
            if len(lines) == 1:
                continue
            if lines[0] == '#':
                continue
            program.append(int('0b' + lines[:8], 2))

        for instruction in program:
            self.ram_write(address, instruction)
            address += 1

    def ram_read(self, MAR):
        MDR = self.ram[MAR]
        return MDR

    def ram_write(self, MAR, MDR):
        self.ram[MAR] = MDR

    def alu(self, op, reg_a, reg_b):
        """ALU operations."""

        num_of_operands = op >> 6
        instruction_identifier_alu = op & 0b00001111

        if self.alu_dispatch[instruction_identifier_alu]:
            if num_of_operands == 0b01:
                self.alu_dispatch[instruction_identifier_alu](reg_a)
            else:
                self.alu_dispatch[instruction_identifier_alu](reg_a, reg_b)
        else:
            raise Exception("Unsupported ALU operation")

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """

        print(f"TRACE: %02X | %02X %02X %02X |" % (
            self.pc,
            #self.fl,
            #self.ie,
            self.ram_read(self.pc),
            self.ram_read(self.pc + 1),
            self.ram_read(self.pc + 2)
        ), end='')

        for i in range(8):
            print(" %02X" % self.reg[i], end='')

        print()

    def run(self):
        """Run the CPU."""

        try:
            while True:
                # Instruction Register, and operand declaration
                IR = self.ram_read(self.pc)
                operand_a = self.ram_read(self.pc + 1)
                operand_b = self.ram_read(self.pc + 2)

                # --- Bitwise operators ---
                num_of_operands = IR >> 6 
                alu_op = (IR & 0b00100000) >> 5 # If '1' - there's an ALU operation
                set_pc = (IR & 0b00010000) >> 4 # If '1' - we are setting PC
                instruction_identifier = IR & 0b00001111

                # Accesses dispatch tables, passes in correct number of arguments in each
                if set_pc == 0b1:
                    if num_of_operands == 0b01:
                        self.pc_dispatch[instruction_identifier](operand_a)
                    else:
                        self.pc_dispatch[instruction_identifier]()
                else:
                    if alu_op == 0b1:
                        self.alu(IR, operand_a, operand_b)
                    else:
                        if num_of_operands == 0b01:
                            self.op_dispatch[instruction_identifier](operand_a)
                        elif num_of_operands == 0b10:
                            self.op_dispatch[instruction_identifier](operand_a, operand_b)
                        else:
                            self.op_dispatch[instruction_identifier]()

                    self.pc += num_of_operands + 1
                    # If pc == 256, reset pc
                    if self.pc >= 256:
                        self.pc = 0
        except Exception:
            pass
