"""Envelope-encryption key providers (DECISIONS G9, D80): AWS KMS wraps data keys bound to their
scope, and the keyring calls the KMS only for a scope it has never seen."""

from __future__ import annotations

import uuid
from typing import Any

import boto3
import pytest
from moto import mock_aws

from app.core.crypto import AwsKms, LocalKms, build_kms, new_data_key
from app.core.state import Keyring


@pytest.fixture
def aws_kms():  # type: ignore[no-untyped-def]
    with mock_aws():
        client = boto3.client(
            "kms", region_name="af-south-1", aws_access_key_id="test", aws_secret_access_key="test"
        )
        key_id = client.create_key(KeySpec="SYMMETRIC_DEFAULT")["KeyMetadata"]["Arn"]
        yield AwsKms(key_id, "af-south-1", client=client)


def test_aws_wraps_and_unwraps_a_data_key(aws_kms: AwsKms):
    key = new_data_key()
    wrapped = aws_kms.wrap(key, "platform")
    assert key not in wrapped and wrapped[:1] == b"\x02"
    assert aws_kms.unwrap(wrapped, "platform") == key


def test_a_wrapped_key_only_opens_for_its_own_scope(aws_kms: AwsKms):
    wrapped = aws_kms.wrap(new_data_key(), "hotel-a")
    with pytest.raises(Exception):  # noqa: B017 - KMS refuses with InvalidCiphertextException
        aws_kms.unwrap(wrapped, "hotel-b")


def test_providers_never_open_each_others_keys(aws_kms: AwsKms):
    local = LocalKms("A" * 43 + "=", "local")
    with pytest.raises(ValueError, match="format"):
        aws_kms.unwrap(local.wrap(new_data_key(), "s"), "s")
    with pytest.raises(ValueError, match="format"):
        local.unwrap(aws_kms.wrap(new_data_key(), "s"), "s")


def test_unknown_providers_are_refused():
    assert isinstance(build_kms("local", "k", "A" * 43 + "=", None), LocalKms)
    with pytest.raises(RuntimeError):
        build_kms("vault", "k", None, None)


class _Counting:
    def __init__(self, inner: Any) -> None:
        self.inner, self.key_id, self.wraps = inner, inner.key_id, 0

    def wrap(self, data_key: bytes, scope: str) -> bytes:
        self.wraps += 1
        return bytes(self.inner.wrap(data_key, scope))

    def unwrap(self, wrapped: bytes, scope: str) -> bytes:
        return bytes(self.inner.unwrap(wrapped, scope))


async def test_the_keyring_wraps_once_per_scope_across_processes(app_state, aws_kms: AwsKms):  # type: ignore[no-untyped-def]
    kms = _Counting(aws_kms)
    scope = f"kms-test-{uuid.uuid4()}"
    first = Keyring(kms=kms, db=app_state.db)
    secret = await first.encrypt(scope, b"guest id 8001015009087", "ctx")
    # A second process (fresh cache) finds the stored key and only unwraps it.
    second = Keyring(kms=kms, db=app_state.db)
    assert await second.decrypt(scope, secret, "ctx") == b"guest id 8001015009087"
    assert kms.wraps == 1
