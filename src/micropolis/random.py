"""
random.py - Random number generation for Micropolis Python port

This module contains the random number generation functions ported from rand.c and random.c,
maintaining exact algorithmic compatibility with the original C implementation.
"""
from micropolis.constants import SIM_RAND_MAX, TYPE_0, MAX_TYPES, BREAK_0, BREAK_1, DEG_0, SEP_0, BREAK_2, TYPE_1, \
    DEG_1, SEP_1, BREAK_3, TYPE_2, DEG_2, SEP_2, BREAK_4, TYPE_3, DEG_3, SEP_3, TYPE_4, DEG_4, SEP_4
from micropolis.context import AppContext


# ============================================================================
# Constants from rand.c
# ============================================================================



# ============================================================================
# Simple Random Number Generator (from rand.c)
# ============================================================================



def sim_rand(context: AppContext) -> int:
    """
    Simple linear congruential random number generator.

    Returns a random integer between 0 and SIM_RAND_MAX (0xffff).
    Uses the same algorithm as the original C implementation.
    :param context:
    """
    # global _next
    context.next = context.next * 1103515245 + 12345
    return (context.next % ((SIM_RAND_MAX + 1) << 8)) >> 8

def sim_srand(context: AppContext, seed: int) -> None:
    """
    Seed the simple random number generator.

    Args:
        seed: The seed value to initialize the generator
    """
    # global _next
    context.next = seed

# ============================================================================
# Advanced Random Number Generator (from random.c)
# ============================================================================





def sim_srandom(context: AppContext, x: int) -> None:
    """
    Initialize the advanced random number generator with a seed.

    Args:
        x: The seed value
        :param context:
    """
    # global fptr_idx, rptr_idx, state, rand_type, rand_deg, rand_sep

    if context.rand_type == TYPE_0:
        context.state[0] = x
    else:
        # Initialize state using LCG
        context.state[0] = x
        for i in range(1, context.rand_deg):
            context.state[i] = (1103515245 * context.state[i - 1] + 12345) & 0xffffffff

        context.fptr_idx = context.rand_sep
        context.rptr_idx = 0

        # Advance the generator 10 * rand_deg times to eliminate dependencies
        for _ in range(10 * context.rand_deg):
            sim_random(context)

def sim_initstate(context: AppContext, seed: int, arg_state: list[int], n: int) -> list[int] | None:
    """
    Initialize state information for the advanced random number generator.

    Args:
        seed: Seed for the generator
        arg_state: State array to initialize (as list of ints)
        n: Number of bytes of state information

    Returns:
        Pointer to old state, or None if error
        :param context:
    """
    # global state, rand_type, rand_deg, rand_sep, end_ptr_idx, fptr_idx, rptr_idx

    # Save current state
    if context.rand_type == TYPE_0:
        old_state = [context.rand_type] + context.state[:1]
    else:
        old_state = [MAX_TYPES * context.rptr_idx + context.rand_type] + context.state

    if n < BREAK_0:
        print(f"random: not enough state ({n} bytes); ignored.", file=__import__('sys').stderr)
        return None

    # Choose appropriate generator type based on state size
    if n < BREAK_1:
        context.rand_type = TYPE_0
        context.rand_deg = DEG_0
        context.rand_sep = SEP_0
    elif n < BREAK_2:
        context.rand_type = TYPE_1
        context.rand_deg = DEG_1
        context.rand_sep = SEP_1
    elif n < BREAK_3:
        context.rand_type = TYPE_2
        context.rand_deg = DEG_2
        context.rand_sep = SEP_2
    elif n < BREAK_4:
        context.rand_type = TYPE_3
        context.rand_deg = DEG_3
        context.rand_sep = SEP_3
    else:
        context.rand_type = TYPE_4
        context.rand_deg = DEG_4
        context.rand_sep = SEP_4

    # Set up new state
    context.state = arg_state[1:]  # Skip the type byte
    context.end_ptr_idx = context.rand_deg

    # Initialize with seed
    sim_srandom(context, seed)

    # Store type information
    if context.rand_type == TYPE_0:
        arg_state[0] = context.rand_type
    else:
        arg_state[0] = MAX_TYPES * context.rptr_idx + context.rand_type

    return old_state

def sim_setstate(context: AppContext, arg_state: list[int]) -> list[int] | None:
    """
    Restore state from a state array.

    Args:
        arg_state: State array to restore from

    Returns:
        Pointer to old state
        :param context:
    """
    # global state, rand_type, rand_deg, rand_sep, end_ptr_idx, fptr_idx, rptr_idx

    new_state = arg_state
    type_val = new_state[0] % MAX_TYPES
    rear = new_state[0] // MAX_TYPES

    # Save current state
    if context.rand_type == TYPE_0:
        old_state = [context.rand_type] + context.state[:1]
    else:
        old_state = [MAX_TYPES * context.rptr_idx + context.rand_type] + context.state

    # Validate and set type
    if type_val in (TYPE_0, TYPE_1, TYPE_2, TYPE_3, TYPE_4):
        context.rand_type = type_val
        context.rand_deg = context.degrees[type_val]
        context.rand_sep = context.seps[type_val]
    else:
        print("random: state info corrupted; not changed.", file=__import__('sys').stderr)
        return old_state

    # Set new state
    context.state = new_state[1:]

    if context.rand_type != TYPE_0:
        context.rptr_idx = rear
        context.fptr_idx = (rear + context.rand_sep) % context.rand_deg

    context.end_ptr_idx = context.rand_deg

    return old_state

def sim_random(context: AppContext) -> int:
    """
    Generate a random number using the advanced generator.

    Returns:
        A 31-bit random number
        :param context:
    """
    # global fptr_idx, rptr_idx, state

    if context.rand_type == TYPE_0:
        # Simple LCG for TYPE_0
        context.state[0] = (context.state[0] * 1103515245 + 12345) & 0x7fffffff
        return context.state[0]
    else:
        # Advanced generator using trinomial feedback
        context.state[context.fptr_idx] = (context.state[context.fptr_idx] + context.state[context.rptr_idx]) & 0xffffffff
        result = (context.state[context.fptr_idx] >> 1) & 0x7fffffff  # Discard least random bit

        # Advance pointers
        context.fptr_idx += 1
        if context.fptr_idx >= context.end_ptr_idx:
            context.fptr_idx = 0
            context.rptr_idx += 1
        else:
            context.rptr_idx += 1

        if context.rptr_idx >= context.end_ptr_idx:
            context.rptr_idx = 0

        return result

# ============================================================================
# Compatibility Functions
# ============================================================================

def Rand(context: AppContext, range_val: int) -> int:
    """
    Generate random number in range [0, range_val).

    This is a compatibility function that mimics the Rand() function
    used elsewhere in the Micropolis codebase.

    Args:
        range_val: Upper bound (exclusive)

    Returns:
        Random integer in range [0, range_val)
        :param context:
    """
    if range_val <= 0:
        return 0
    return sim_rand(context) % range_val

def RandInt(context: AppContext) -> int:
    """
    Generate a random integer.

    Returns:
        Random integer (compatibility function)
        :param context:
    """
    return sim_rand(context)

def Rand16(context: AppContext) -> int:
    """
    Generate a 16-bit random number.

    Returns:
        Random 16-bit integer (0-65535)
        :param context:
    """
    return sim_rand(context) & 0xffff