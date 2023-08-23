
from . import lib
import requests 

class SinglebaseError(Exception):
    pass

class Result(object):
    def __init__(self, **kw):
        self.data = kw.get("data") or {}
        self.meta = kw.get("meta") or {}
        self.ok = kw.get("ok") or True
        self.error = kw.get("error") or None 
        self.status_code = kw.get("status_code") or 200

    def to_dict(self):
        return {
            "data": self.data,
            "meta": self.meta,
            "ok": self.ok,
            "error": self.error,
            "status_code": self.status_code
        }


class Client(object):

    def __init__(self, api_url:str, access_key:str) -> None:
        self._api_url = api_url
        self._access_key = access_key

        self.auth:Auth = Auth(client=self)
        self.storage:Storage = Storage(client=self)

    def collection(self, collection_name:str) -> "Collection":
        return Collection(client=self, collection_name=collection_name)

    def dispatch(self, payload:dict) -> Result:
        try:
            if "action" not in payload:
                raise SinglebaseError("Request missing @action")

            headers = {
                "X-SINGLEBASE-ACCESS-KEY": self._access_key
            }

            r = requests.post(self._api_url, json=payload, headers=headers)

            resp = lib.json_loads(r.text()) # so it can convert date
            if r.status_code == requests.codes.ok:
                return Result(data=resp.get("data"), meta=resp.get("meta"), status_code=200, ok=True)
            else:
                return Result(error=resp.get("error"), status_code=r.status_code, ok=False)
        except Exception as e:
            return Result(error="EXCEPTION: %s" % e, status_code=500, ok=False)


class _BaseService(object):
    def __init__(self, client:Client) -> None:
        self._client = client

    def dispatch(self, action:str, payload:dict={}) -> Result:
        return self._client.dispatch(payload=payload)


class Collection(_BaseService):
    def __init__(self, client:Client, collection_name:str, matches:dict=None) -> None:
        super().__init__(client=client)
        self.collection_name = collection_name
        self._default_matches = matches or {}

    def _make_matches(self, payload:dict={}) -> dict: 
        _payload = {**payload}
        if (self._default_matches):
            if "matches" in _payload:
                _payload["matches"] = {
                    **self._default_matches
                    **_payload["matches"]
                }
            else:
                _payload["matches"] = {**self._default_matches }
        return _payload

    def matches(self, matches:dict={}):
        return Collection(client=self._client, collection_name=self.collection_name, matches=matches)

    def get_doc(self, _key:str, **kw):
        pass

    def fetch(self, **kw):
        res = self.dispatch()

    def fetch_one(self, **kw) -> Result:
        res = self.fetch(**kw)
        if res.ok and res.data:
            return Result(data=res.data[0])
        return res

    def insert(self, **kw):
        pass

    def set_doc(self, **kw):
        pass

    def delete_doc(self, **kw):
        pass

    def update(self, **kw):
        pass

    def update_many(self, **kw):
        pass

    def upsert(self, **kw):
        pass

    def delete(self, **kw):
        pass

    def archive(self, **kw):
        pass

    def restore(self, **kw):
        pass

    def count(self, **kw):
        pass

class Auth(_BaseService):

    def signup(self, **kw):
        pass

    def signin(self, **kw):
        pass

    def create_user_with_password(self, **kw):
        pass

    def signin_with_password(self, **kw):
        pass

    def sigin_with_otp(self, **kw):
        pass

    def signout(self, **kw):
        pass

    def change_email(self, **kw):
        pass

    def change_password(self, **kw):
        pass

    def update_profile(self, **kw):
        pass

    def update_account(self, **kw):
        pass

    def send_otp(self, **kw):
        pass

    def get_nonce(self, **kw) -> None:
        res = self.dispatch("auth.nonce", {"action": "auth.nonce"})
        return res.data.get('nonce') if res.ok else None


class Storage(_BaseService):
    def upload(self):
        pass
    
    def update(self):
        pass

    def delete(self):
        pass

    def get_download_url(self):
        pass


