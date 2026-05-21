"""Sample file with intentional issues for demo reviews."""
import os

password = "admin123"  # hardcoded credential

def process(user_input):
    eval(user_input)  # security risk
    try:
        result = 10 / 0
    except:  # bare except
        pass
    print("debug:", result)  # noqa
    return result

# TODO: refactor this module
