"""Generate and display the tool's ASCII banner."""

import random

import pyfiglet  # type: ignore
from termcolor import colored  # type: ignore

COLORS = ["red", "green", "yellow", "blue", "magenta", "cyan", "white"]


def show_banner() -> None:
    """Print Myesve's Banner: Just Myesve in diff fonts as well as as diff colors"""
    fonts = ["slant", "banner3", "standard", "big"]
    font = random.choice(fonts)
    ascii_banner = pyfiglet.figlet_format("myesve", font=font)
    color = random.choice(COLORS)
    print(colored(ascii_banner, color))
    print(
        colored(
            "CVE-2024-38475 Exploitation Framework",
            "yellow",
            attrs=["bold"],
        )
    )
    print(
        colored(
            "Author: Nyakki Labs 0x420 | Original Discovery by Orange Tsai.\n",
            "cyan",
        )
    )
