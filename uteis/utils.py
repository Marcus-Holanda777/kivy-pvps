import requests
from requests.exceptions import ConnectionError, Timeout
import re


def is_data(texto: str):
    comp = re.compile(
        r'''^
           (0[1-9]|[12][0-9]|3[01])
           /
           (0[1-9]|1[012])
           /
           [12][0-9]{3}
           $
        ''',
        re.I | re.VERBOSE
    )

    if comp.search(texto):
        return True
    else:
        return False


def is_connect(timeout: float = 5.0) -> bool:
    url = "http://www.google.com"
    try:
        rst = requests.get(url, timeout=timeout)
        return True
    except ConnectionError or Timeout:
        return False
