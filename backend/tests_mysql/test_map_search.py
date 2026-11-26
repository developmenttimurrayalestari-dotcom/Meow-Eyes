import asyncio
import httpx
import pytest
from fastapi import FastAPI, HTTPException
from auth import current_user
from models import User
from routes_integrations import router
from integrations import map_search as service


def feature(coords=(106.8272, -6.1754), country='ID', name='Monas'):
    return {'geometry': {'type': 'Point', 'coordinates': list(coords)}, 'properties': {'name': name, 'city': 'Jakarta', 'countrycode': country}}


@pytest.fixture(autouse=True)
def reset_search(monkeypatch):
    service._cache.clear()
    monkeypatch.setattr(service, '_last_request', -10)
    monkeypatch.setattr(service, '_lock', asyncio.Lock())
    monkeypatch.setenv('MAP_GEOCODING_URL', 'https://photon.komoot.io/api/')


def test_search_geojson_order_country_filter_cache_and_throttle(monkeypatch):
    calls = []
    def response(request):
        calls.append(request)
        return httpx.Response(200, json={'features': [feature(), feature(), feature((13, 52), 'DE'), feature((True, -6)), feature(('bad', -6))]})
    original = httpx.AsyncClient
    monkeypatch.setattr(service.httpx, 'AsyncClient', lambda **kwargs: original(transport=httpx.MockTransport(response), **kwargs))
    async def run():
        result = await service.search_address('Monas Jakarta')
        assert result == {'results': [{'label': 'Monas, Jakarta', 'latitude': -6.1754, 'longitude': 106.8272}]}
        assert (await service.search_address('  MONAS   Jakarta ')) == result
        assert len(calls) == 1
        assert calls[0].url.params['countrycode'] == 'ID'
        with pytest.raises(HTTPException) as error:
            await service.search_address('Bandung')
        assert error.value.status_code == 429
    asyncio.run(run())


@pytest.mark.parametrize('payload,status', [({'features': []}, 200), ({'features': 'invalid'}, 200), ({'secret': 'must not leak'}, 500)])
def test_empty_invalid_and_provider_failure(monkeypatch, payload, status):
    original = httpx.AsyncClient
    transport = httpx.MockTransport(lambda request: httpx.Response(status, json=payload))
    monkeypatch.setattr(service.httpx, 'AsyncClient', lambda **kwargs: original(transport=transport, **kwargs))
    async def run():
        if payload == {'features': []}:
            assert await service.search_address('Unknown Jakarta') == {'results': []}
        else:
            with pytest.raises(HTTPException) as error:
                await service.search_address('Monas Jakarta')
            assert error.value.status_code == 503
            assert 'secret' not in str(error.value.detail)
    asyncio.run(run())


def test_authenticated_route_validates_query_without_everpro_credentials(monkeypatch):
    async def search(query):
        assert query == 'Monas Jakarta'
        return {'results': []}
    monkeypatch.setattr(service, 'search_address', search)
    async def run():
        app = FastAPI(); app.include_router(router, prefix='/api')
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            assert (await client.post('/api/shipping/map-search', json={'query': 'Monas Jakarta'})).status_code == 401
            app.dependency_overrides[current_user] = lambda: User(user_id='customer', name='Customer', role='customer')
            for query in ['ab', 'a' * 201]:
                assert (await client.post('/api/shipping/map-search', json={'query': query})).status_code == 422
            assert (await client.post('/api/shipping/map-search', json={'query': 'Monas Jakarta'})).json() == {'results': []}
    asyncio.run(run())


def test_unconfigured_endpoint_and_whitespace_query(monkeypatch):
    async def run():
        with pytest.raises(HTTPException) as error:
            await service.search_address('   ')
        assert error.value.status_code == 422
        monkeypatch.setenv('MAP_GEOCODING_URL', 'http://untrusted.example/api/')
        with pytest.raises(HTTPException) as error:
            await service.search_address('Jakarta')
        assert error.value.status_code == 503
    asyncio.run(run())
