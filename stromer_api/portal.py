import requests
from urllib.parse import urlencode, parse_qs, splitquery


class Portal:
    __url = "https://stromer-portal.ch/mobile/v4/login/"
    __token_url = "https://stromer-portal.ch/mobile/v4/o/token/"
    __api_url = "https://api3.stromer-portal.ch/rapi/mobile/v4.1/"

    def __init__(self, username: str, password: str, client_id: str) -> None:
        self.__username = username
        self.__password = password
        self.__client_id = client_id
        self.__session = requests.session()
        self.__session.get(self.__url)
        self.__access_token = None

        try:
            qs = urlencode(
                {
                    "client_id": self.__client_id,
                    "response_type": "code",
                    "redirect_url": "stromerauth://auth",
                    "scope": "bikeposition bikestatus bikeconfiguration bikelock biketheft "
                             "bikedata bikepin bikeblink userprofile"
                }
            )

            data = {
                "password": self.__password,
                "username": self.__username,
                "csrfmiddlewaretoken": self.__session.cookies.get("csrftoken"),
                "next": "/mobile/v4/o/authorize/?" + qs
            }

            res = self.__session.post(self.__url, data=data, headers={"Referer": self.__url}, allow_redirects=False)
            res = self.__session.send(res.next, allow_redirects=False)

            _, qs = splitquery(res.headers["Location"])
            query = parse_qs(qs)
            code = query["code"][0]
            params = {
                "grant_type": "authorization_code",
                "client_id": self.__client_id,
                "code": code,
                "redirect_uri": "stromer://auth"
            }

            res = requests.post(self.__token_url, params=params)
            self.__access_token = res.json()["access_token"]
            self.__bike = self.get("bike")

        except:
            raise Exception("Authentication failed")

    def delete(self, endpoint: str) -> bool:
        try:
            res = self.__session.delete(self.__api_url + endpoint + "/",
                                        headers={"Authorization": "Bearer %s" % self.__access_token})
            if res.status_code == 204:
                return True
            else:
                return False
        except:
            raise Exception("Error setting parameters")

    def post(self, endpoint: str, data: dict):
        try:
            res = self.__session.post(self.__api_url + endpoint + "/",
                                      headers={"Authorization": "Bearer %s" % self.__access_token},
                                      json=data)
            if "data" in res.json():
                return res.json()["data"]
            else:
                return None
        except:
            raise Exception("Error setting parameters")

    def get(self, endpoint: str, params=None, full_list: bool = False):
        try:
            if params is None:
                params = {}

            res = self.__session.get(self.__api_url + endpoint,
                                     headers={"Authorization": "Bearer %s" % self.__access_token},
                                     params=params)
            if "data" not in res.json():
                return None
            elif isinstance(res.json()["data"], list):
                if full_list:
                    return res.json()["data"]
                else:
                    if len(res.json()["data"]) > 0:
                        return res.json()["data"][0]
                    else:
                        return None
            else:
                return res.json()["data"]

        except:
            raise Exception("Error getting parameters")
