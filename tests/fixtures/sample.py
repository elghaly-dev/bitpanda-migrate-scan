import requests

BASE = "https://api.bitpanda.com/v1"
api_key = "Zq8Lm2Vx9Rt4Yp7Nc1Bd6Hs3Kw5Jf0Ga"

def tx():
    return requests.get("https://api.bitpanda.com/v1/wallets/transactions", headers={"x-api-key": api_key})

def other():
    return requests.get("https://api.bitpanda.com/v1/something-else")
