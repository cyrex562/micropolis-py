"""
random.py - Random number generation for Micropolis Python port

This module contains the random number generation functions ported from rand.c and random.c,
maintaining exact algorithmic compatibility with the original C implementation.
"""



# ============================================================================
# Constants from rand.c
# ============================================================================

SIM_RAND_MAX = 0xffff  # Maximum value returned by sim_rand()

# ============================================================================
# Simple Random Number Generator (from rand.c)
# ============================================================================

# Static variable from rand.c
_next = 1

def sim_rand() -> int:
    """
    Simple linear congruential random number generator.

    Returns a random integer between 0 and SIM_RAND_MAX (0xffff).
    Uses the same algorithm as the original C implementation.
    """
    global _next
    _next = _next * 1103515245 + 12345
    return ((_next % ((SIM_RAND_MAX + 1) << 8)) >> 8)

def sim_srand(seed: int) -> None:
    """
    Seed the simple random number generator.

    Args:
        seed: The seed value to initialize the generator
    """
    global _next
    _next = seed

# ============================================================================
# Advanced Random Number Generator (from random.c)
# ============================================================================

# Generator types
TYPE_0 = 0  # linear congruential
TYPE_1 = 1  # x**7 + x**3 + 1
TYPE_2 = 2  # x**15 + x + 1
TYPE_3 = 3  # x**31 + x**3 + 1
TYPE_4 = 4  # x**63 + x + 1

# Break values (minimum state size for each type)
BREAK_0 = 8
BREAK_1 = 32
BREAK_2 = 64
BREAK_3 = 128
BREAK_4 = 256

# Degrees for each polynomial
DEG_0 = 0
DEG_1 = 7
DEG_2 = 15
DEG_3 = 31
DEG_4 = 63

# Separations between coefficients
SEP_0 = 0
SEP_1 = 3
SEP_2 = 1
SEP_3 = 3
SEP_4 = 1

MAX_TYPES = 5

# Arrays of degrees and separations
degrees = [DEG_0, DEG_1, DEG_2, DEG_3, DEG_4]
seps = [SEP_0, SEP_1, SEP_2, SEP_3, SEP_4]

# Default state table (from random.c)
randtbl = [
    TYPE_3,
    0x9a319039, 0x32d9c024, 0x9b663182, 0x5da1f342, 0xde3b81e0, 0xdf0a6fb5,
    0xf103bc02, 0x48f340fb, 0x7449e56b, 0xbeb1dbb0, 0xab5c5918, 0x946554fd,
    0x8c2e680f, 0xeb3d799f, 0xb11ee0b7, 0x2d436b86, 0xda672e2a, 0x1588ca88,
    0xe369735d, 0x904f35f7, 0xd7158fd6, 0x6fa6f051, 0x616e6b96, 0xac94efdc,
    0x36413f93, 0xc622c298, 0xf5a42ab8, 0x8a88d77b, 0xf5ad9d0e, 0x8999220b,
    0x27fb47b9,
]

# Global state variables
fptr_idx = SEP_3 + 1  # Front pointer index
rptr_idx = 1          # Rear pointer index
state = randtbl[1:]   # State array (skip type byte)
rand_type = TYPE_3
rand_deg = DEG_3
rand_sep = SEP_3
end_ptr_idx = DEG_3  # Index of last element

def sim_srandom(x: int) -> None:
    """
    Initialize the advanced random number generator with a seed.

    Args:
        x: The seed value
    """
    global fptr_idx, rptr_idx, state, rand_type, rand_deg, rand_sep

    if rand_type == TYPE_0:
        state[0] = x
    else:
        # Initialize state using LCG
        state[0] = x
        for i in range(1, rand_deg):
            state[i] = (1103515245 * state[i - 1] + 12345) & 0xffffffff

        fptr_idx = rand_sep
        rptr_idx = 0

        # Advance the generator 10 * rand_deg times to eliminate dependencies
        for _ in range(10 * rand_deg):
            sim_random()

def sim_initstate(seed: int, arg_state: list[int], n: int) -> list[int] | None:
    """
    Initialize state information for the advanced random number generator.

    Args:
        seed: Seed for the generator
        arg_state: State array to initialize (as list of ints)
        n: Number of bytes of state information

    Returns:
        Pointer to old state, or None if error
    """
    global state, rand_type, rand_deg, rand_sep, end_ptr_idx, fptr_idx, rptr_idx

    # Save current state
    if rand_type == TYPE_0:
        old_state = [rand_type] + state[:1]
    else:
        old_state = [MAX_TYPES * rptr_idx + rand_type] + state

    if n < BREAK_0:
        print(f"random: not enough state ({n} bytes); ignored.", file=__import__('sys').stderr)
        return None

    # Choose appropriate generator type based on state size
    if n < BREAK_1:
        rand_type = TYPE_0
        rand_deg = DEG_0
        rand_sep = SEP_0
    elif n < BREAK_2:
        rand_type = TYPE_1
        rand_deg = DEG_1
        rand_sep = SEP_1
    elif n < BREAK_3:
        rand_type = TYPE_2
        rand_deg = DEG_2
        rand_sep = SEP_2
    elif n < BREAK_4:
        rand_type = TYPE_3
        rand_deg = DEG_3
        rand_sep = SEP_3
    else:
        rand_type = TYPE_4
        rand_deg = DEG_4
        rand_sep = SEP_4

    # Set up new state
    state = arg_state[1:]  # Skip the type byte
    end_ptr_idx = rand_deg

    # Initialize with seed
    sim_srandom(seed)

    # Store type information
    if rand_type == TYPE_0:
        arg_state[0] = rand_type
    else:
        arg_state[0] = MAX_TYPES * rptr_idx + rand_type

    return old_state

def sim_setstate(arg_state: list[int]) -> list[int] | None:
    """
    Restore state from a state array.

    Args:
        arg_state: State array to restore from

    Returns:
        Pointer to old state
    """
    global state, rand_type, rand_deg, rand_sep, end_ptr_idx, fptr_idx, rptr_idx

    new_state = arg_state
    type_val = new_state[0] % MAX_TYPES
    rear = new_state[0] // MAX_TYPES

    # Save current state
    if rand_type == TYPE_0:
        old_state = [rand_type] + state[:1]
    else:
        old_state = [MAX_TYPES * rptr_idx + rand_type] + state

    # Validate and set type
    if type_val in (TYPE_0, TYPE_1, TYPE_2, TYPE_3, TYPE_4):
        rand_type = type_val
        rand_deg = degrees[type_val]
        rand_sep = seps[type_val]
    else:
        print("random: state info corrupted; not changed.", file=__import__('sys').stderr)
        return old_state

    # Set new state
    state = new_state[1:]

    if rand_type != TYPE_0:
        rptr_idx = rear
        fptr_idx = (rear + rand_sep) % rand_deg

    end_ptr_idx = rand_deg

    return old_state

def sim_random() -> int:
    """
    Generate a random number using the advanced generator.

    Returns:
        A 31-bit random number
    """
    global fptr_idx, rptr_idx, state

    if rand_type == TYPE_0:
        # Simple LCG for TYPE_0
        state[0] = (state[0] * 1103515245 + 12345) & 0x7fffffff
        return state[0]
    else:
        # Advanced generator using trinomial feedback
        state[fptr_idx] = (state[fptr_idx] + state[rptr_idx]) & 0xffffffff
        result = (state[fptr_idx] >> 1) & 0x7fffffff  # Discard least random bit

        # Advance pointers
        fptr_idx += 1
        if fptr_idx >= end_ptr_idx:
            fptr_idx = 0
            rptr_idx += 1
        else:
            rptr_idx += 1

        if rptr_idx >= end_ptr_idx:
            rptr_idx = 0

        return result

# ============================================================================
# Compatibility Functions
# ============================================================================

def Rand(range_val: int) -> int:
    """
    Generate random number in range [0, range_val).

    This is a compatibility function that mimics the Rand() function
    used elsewhere in the Micropolis codebase.

    Args:
        range_val: Upper bound (exclusive)

    Returns:
        Random integer in range [0, range_val)
    """
    if range_val <= 0:
        return 0
    return sim_rand() % range_val

def RandInt() -> int:
    """
    Generate a random integer.

    Returns:
        Random integer (compatibility function)
    """
    return sim_rand()

def Rand16() -> int:
    """
    Generate a 16-bit random number.

    Returns:
        Random 16-bit integer (0-65535)
    """
    return sim_rand() & 0xffff