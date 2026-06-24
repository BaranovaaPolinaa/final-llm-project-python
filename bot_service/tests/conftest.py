import pytest
import fakeredis.aioredis as fakeredis_aioredis


@pytest.fixture
def fake_redis():
    return fakeredis_aioredis.FakeRedis(decode_responses=True)
