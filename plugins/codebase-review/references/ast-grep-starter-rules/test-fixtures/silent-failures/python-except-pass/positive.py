# Fixture for python-except-pass — positive cases
# All cases should be flagged by the rule.


def case_1_bare():
    try:
        risky_call()
    except:
        pass


def case_2_exception():
    try:
        risky_call()
    except Exception:
        pass


def case_3_exception_as():
    try:
        risky_call()
    except Exception as e:
        pass


def case_4_multiple_lines():
    try:
        x = fetch_data()
        y = process(x)
        save(y)
    except Exception:
        pass


def risky_call():
    raise ValueError("test")


def fetch_data():
    return None


def process(x):
    return x


def save(y):
    pass
