import pytest
import asyncio
from fastapi import HTTPException
from backend.routes.users import request_admin, approve_admin_request, list_admin_requests


class FakeUserCollection:
    def __init__(self, user):
        self._user = user

    async def find_one(self, q):
        # Accept either {'email': email} or {'_id': oid}
        if 'email' in q:
            return self._user
        return self._user

    async def update_one(self, q, u):
        # mimic update
        self._user.update(u.get('$set', {}))
        return None


@pytest.mark.asyncio
async def test_request_admin_user_not_found(monkeypatch):
    # decodeJWT returns an email
    monkeypatch.setattr('backend.routes.users.decodeJWT', lambda token: {'email': 'noone@example.com'})
    # user_collection.find_one returns None
    class Empty:
        async def find_one(self, q):
            return None
    monkeypatch.setattr('backend.routes.users.user_collection', Empty())

    with pytest.raises(HTTPException) as exc:
        await request_admin(token="fake")
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_request_admin_already_admin(monkeypatch):
    monkeypatch.setattr('backend.routes.users.decodeJWT', lambda token: {'email': 'admin@example.com'})
    user = {"email": "admin@example.com", "is_admin": True}
    monkeypatch.setattr('backend.routes.users.user_collection', FakeUserCollection(user))

    res = await request_admin(token="fake")
    assert res["message"] == "User already has admin privileges"


@pytest.mark.asyncio
async def test_request_admin_pending(monkeypatch):
    monkeypatch.setattr('backend.routes.users.decodeJWT', lambda token: {'email': 'pend@example.com'})
    user = {"email": "pend@example.com", "is_admin": False, "admin_request_status": "pending"}
    monkeypatch.setattr('backend.routes.users.user_collection', FakeUserCollection(user))

    res = await request_admin(token="fake")
    assert res["message"] == "Admin request already pending"


@pytest.mark.asyncio
async def test_request_admin_success(monkeypatch):
    monkeypatch.setattr('backend.routes.users.decodeJWT', lambda token: {'email': 'user@example.com'})
    user = {"email": "user@example.com", "is_admin": False, "admin_request_status": "none", "username": "user"}
    monkeypatch.setattr('backend.routes.users.user_collection', FakeUserCollection(user))
    # Prevent actual email sending
    monkeypatch.setattr('backend.routes.users.send_admin_request_email', lambda e, u: None)

    res = await request_admin(token="fake")
    assert res["message"] == "Admin request submitted"


@pytest.mark.asyncio
async def test_approve_invalid_id(monkeypatch):
    # Providing invalid id string
    with pytest.raises(HTTPException) as exc:
        await approve_admin_request("notanid", token="fake")
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_approve_user_not_found(monkeypatch):
    from bson import ObjectId
    oid = str(ObjectId())
    monkeypatch.setattr('backend.routes.users.decodeJWT', lambda token: {'email': 'admin@example.com'})
    class Empty:
        async def find_one(self, q):
            return None
    monkeypatch.setattr('backend.routes.users.user_collection', Empty())

    with pytest.raises(HTTPException) as exc:
        await approve_admin_request(oid, token="fake")
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_approve_success(monkeypatch):
    from bson import ObjectId
    oid = ObjectId()
    oid_str = str(oid)
    user = {"_id": oid, "email": "u@example.com"}
    monkeypatch.setattr('backend.routes.users.decodeJWT', lambda token: {'email': 'admin@example.com'})
    monkeypatch.setattr('backend.routes.users.user_collection', FakeUserCollection(user))

    res = await approve_admin_request(oid_str, token="fake")
    assert res["message"] == "User approved as admin"
