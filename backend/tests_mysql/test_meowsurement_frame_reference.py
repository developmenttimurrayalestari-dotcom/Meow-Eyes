import asyncio
from copy import deepcopy

from tests_mysql.test_meowsurement import client_fixture, started, revise, local_capture


def test_frame_reference_length_and_dimension_must_match_immutable_session():
    async def run():
        async with client_fixture() as (client, auth, d):
            detail, _ = await started(client, auth, d)
            data = deepcopy(detail['revision']['data'])
            data['consents']['capture'] = True
            capture = local_capture(data)
            capture['calibrationSpec'] = {'method': 'frame', 'scaleSource': 'session_frame', 'frameDimension': 'a', 'lengthMm': data['frame']['a'], 'evidence': {}}
            data['captures'] = [capture]
            for patch in [{'lengthMm': data['frame']['a'] + 1}, {'frameDimension': 'b'}, {'method': 'marker'}]:
                bad = deepcopy(data)
                bad['captures'][0]['calibrationSpec'].update(patch)
                assert (await revise(client, detail, bad)).status_code == 422
            bad = deepcopy(data)
            bad['captures'][0]['calibration'] = {'valid': True, 'method': 'frame', 'geometry': {'lengthMm': data['frame']['a'] + 1}}
            assert (await revise(client, detail, bad)).status_code == 422
            good = await revise(client, detail, data)
            assert good.status_code == 200, good.text
            latest = (await client.get('/api/meowsurement/sessions/' + detail['session']['id'])).json()
            side = local_capture(data, capture_id='cap_side', photo_id='local_side', view='lateral_right')
            side['calibrationSpec'] = {'method': 'frame', 'scaleSource': 'session_frame', 'frameDimension': 'b', 'lengthMm': data['frame']['b'], 'evidence': {}}
            data['captures'].append(side)
            good = await revise(client, latest, data)
            assert good.status_code == 200, good.text
    asyncio.run(run())
