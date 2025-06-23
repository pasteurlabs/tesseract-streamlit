# Copyright 2025 Pasteur Labs. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel, Field
from tesseract_core.runtime import Array, Float32


class Hobby(BaseModel):
    name: str = Field(description="Name of the activity.")
    active: bool = Field(description="Does the person actively engage with it?")
    experience: int = Field(description="Experience practising it in years.")


class InputSchema(BaseModel):
    name: str = Field(
        description="Name of the person you want to greet.", default="John Doe"
    )
    age: int = Field(description="Age of person in years.", default=30)
    height: float = Field(description="Height of person in cm.", default=175.0)
    alive: bool = Field(
        description="Whether the person is (currently) alive.", default=True
    )
    weight: Float32 = Field(description="The person's weight in kg.")
    leg_lengths: Array[(2,), Float32] = Field(
        description="The length of the person's left and right legs in cm."
    )
    hobby: Hobby = Field(description="The person's only hobby.")


class OutputSchema(BaseModel):
    greeting: str = Field(description="A greeting!")


def apply(inputs: InputSchema) -> OutputSchema:
    """Greet a person whose name is given as input."""
    return OutputSchema(
        greeting=(
            f"Hello {inputs.name}! You are {inputs.age} years old. "
            f"That's pretty good. Oh, so tall? {inputs.height} cm! Wow. You "
            f"must be very successful. "
            f"You are {inputs.weight} kg? That's much larger than an atom, "
            "and much smaller than the Sun, so pretty middling all things "
            f"considered. Your left leg is {inputs.leg_lengths[0]} and your "
            f"right leg is {inputs.leg_lengths[1]} - is that normal? "
            f"Ah, I see you do {inputs.hobby.name} as a hobby! That's great. "
            f"You've got {inputs.hobby.experience} years of experience, and "
            f"you're {'' if inputs.hobby.active else 'not'} actively doing "
            "it. I guess that's somewhat interesting. Anyway, pretty "
            + ("cool you're alive." if inputs.alive else "sad you're dead.")
        ),
        dummy=list(range(100)),
    )
