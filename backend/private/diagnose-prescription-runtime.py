import asyncio
import json
import httpx

async def main():
    result = []
    async with httpx.AsyncClient(timeout=5) as client:
        for origin in ('http://127.0.0.1:8001', 'http://192.168.44.50:8001'):
            entry = {'origin': origin}
            try:
                response = await client.get(origin + '/api/health', headers={'Origin': 'http://localhost:3000'})
                entry.update(status=response.status_code, cors=response.headers.get('access-control-allow-origin'), health=response.json())
                schema = (await client.get(origin + '/openapi.json')).json()['paths']
                entry['lens_options_present'] = '/api/cart/{cart_item_id}/lens-options' in schema
                entry['duplicate_present'] = '/api/admin/products/{pid}/duplicate' in schema
                preflight = await client.options(origin + '/api/cart/diagnosis/prescription', headers={
                    'Origin': 'http://localhost:3000', 'Access-Control-Request-Method': 'PATCH', 'Access-Control-Request-Headers': 'authorization,content-type'})
                entry['patch_preflight'] = preflight.status_code
            except Exception as error:
                entry['error_type'] = type(error).__name__
            result.append(entry)
    print(json.dumps(result))

asyncio.run(main())
