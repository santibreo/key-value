from uuid import uuid4
from datetime import datetime, timedelta
import pytest
from fakeredis import FakeRedis
from key_value import repositories
from typing import Callable


ALL_REPOS_BUT_DEFAULT: list[Callable[[], repositories.KeyValueRepository]] = [
    lambda: repositories.DictRepository(expire_seconds=60),
    lambda: repositories.DirectoryRepository(expire_seconds=60),
    lambda: repositories.DbFilenameRepository(expire_seconds=60),
    lambda: repositories.RedisRepository(FakeRedis(), expire_seconds=60),
]
ALL_REPOS = ALL_REPOS_BUT_DEFAULT + [
    lambda: repositories.DefaultRepository(default=uuid4)
]


@pytest.mark.parametrize('repository_factory',  ALL_REPOS_BUT_DEFAULT)
def test_get_not_found(repository_factory):
    repository = repository_factory()
    with pytest.raises(KeyError):
        repository['a']


@pytest.mark.parametrize('repository_factory',  ALL_REPOS_BUT_DEFAULT)
def test_get_not_found_by_method(repository_factory):
    repository = repository_factory()
    assert repository.get('a') is repository.default(), '`get` non existing key'


@pytest.mark.parametrize('repository_factory',  ALL_REPOS)
def test_get_existing(repository_factory):
    repository = repository_factory()
    repository['a'] = '1'
    assert repository['a'] == '1', '`__getitem__` existing key'


@pytest.mark.parametrize('repository_factory',  ALL_REPOS)
def test_get_existing_by_method(repository_factory):
    repository = repository_factory()
    repository['a'] = '1'
    assert repository.get('a') == '1', '`get` existing key'


@pytest.mark.parametrize('repository_factory',  ALL_REPOS_BUT_DEFAULT)
def test_del_not_found(repository_factory):
    repository = repository_factory()
    with pytest.raises(KeyError):
        del repository['a']


@pytest.mark.parametrize('repository_factory',  ALL_REPOS)
def test_del_not_found_by_method(repository_factory):
    repository = repository_factory()
    assert repository.delete('a') is None, '`delete` non existing key'


@pytest.mark.parametrize('repository_factory',  ALL_REPOS)
def test_del_existing(repository_factory):
    repository = repository_factory()
    repository['a'] = '1'
    del repository['a']


@pytest.mark.parametrize('repository_factory',  ALL_REPOS)
def test_del_existing_by_method(repository_factory):
    repository = repository_factory()
    repository['a'] = '1'
    assert repository.delete('a') is None, '`delete` existing key'


@pytest.mark.parametrize('repository_factory', ALL_REPOS)
def test_set_not_found(repository_factory):
    repository = repository_factory()
    repository['a'] = '1'


@pytest.mark.parametrize('repository_factory', ALL_REPOS)
def test_set_not_found_by_method(repository_factory):
    repository = repository_factory()
    assert repository.set('a', '1') is None, '`set` non existing key'


@pytest.mark.parametrize('repository_factory',  ALL_REPOS)
def test_set_existing(repository_factory):
    repository = repository_factory()
    repository['a'] = '1'
    with pytest.raises(KeyError):
        repository['a'] = 1


@pytest.mark.parametrize('repository_factory',  ALL_REPOS)
def test_set_existing_by_method(repository_factory):
    repository = repository_factory()
    repository['a'] = '1'
    assert repository.set('a', '1') is None, '`set` existing key'


@pytest.mark.parametrize('repository_factory',  ALL_REPOS_BUT_DEFAULT)
def test_get_expired_key(repository_factory, freezer):
    repository = repository_factory()
    repository['a'] = '1'
    freezer.move_to(timedelta(seconds=61))
    with pytest.raises(KeyError):
        repository['a']


@pytest.mark.parametrize('repository_factory',  ALL_REPOS_BUT_DEFAULT)
def test_get_expired_key_by_method(repository_factory, freezer):
    repository = repository_factory()
    repository['a'] = '1'
    freezer.move_to(timedelta(seconds=61))
    assert repository.get('a') == repository.default(), 'get expired key is not default'


@pytest.mark.parametrize('repository_factory',  ALL_REPOS_BUT_DEFAULT)
def test_get_key_refreshes_expiration(repository_factory, freezer):
    repository: repositories.KeyValueRepository = repository_factory()
    start = datetime.now()
    repository['a'] = '1'
    freezer.move_to(timedelta(seconds=40))
    _ = repository.get('a')
    freezer.move_to(timedelta(seconds=40))
    val = repository.get('a')
    assert (datetime.now() - start) > timedelta(seconds=repository.expire_seconds), (
        'Not enough time elapsed'
    )
    assert val == '1', 'get does not refreshes expiration'
