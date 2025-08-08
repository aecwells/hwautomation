#!/usr/bin/env python3

import sys

sys.path.insert(0, "/home/ubuntu/HWAutomation/src")

from hwautomation.utils.config import load_config


def test_config():
    try:
        print("Testing config loading...")
        config = load_config("/home/ubuntu/HWAutomation/config.yaml")
        print(f"Config loaded: {type(config)}")
        print(f"Config keys: {list(config.keys())}")
        print("Config loading successful!")

    except Exception as e:
        print(f"Error loading config: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_config()
