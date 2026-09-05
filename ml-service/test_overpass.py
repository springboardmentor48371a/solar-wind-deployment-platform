import asyncio, httpx

async def test():
    query = """
    [out:json][timeout:25];
    (
      way["highway"~"primary|secondary"](around:10000,9.3639,78.8395);
    );
    out geom;
    """
    async with httpx.AsyncClient(timeout=30) as client:
        res = await client.post('https://overpass-api.de/api/interpreter', data={'data': query})
        data = res.json()
        elements = data.get('elements', [])
        print('count:', len(elements))
        if elements:
            e = elements[0]
            print('keys:', list(e.keys()))
            print('type:', e.get('type'))
            print('has geometry:', 'geometry' in e)
            if 'geometry' in e:
                print('geometry sample:', e['geometry'][:2])
            print('sample:', str(e)[:400])

asyncio.run(test())
