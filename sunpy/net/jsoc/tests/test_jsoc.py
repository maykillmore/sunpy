# -*- coding: utf-8 -*-
"""
Created on Wed Mar 26 20:17:06 2014

@author: stuart
"""
import os
import tempfile
import datetime
import pandas as pd
import astropy.table
import astropy.time
import astropy.units as u
import pytest

from sunpy.time import parse_time
from sunpy.net.jsoc import JSOCClient, JSOCResponse
from sunpy.net.download import Results
import sunpy.net.jsoc.attrs as attrs
import sunpy.net.vso.attrs as vso_attrs

client = JSOCClient()


def test_jsocresponse_double():
    j1 = JSOCResponse(table=astropy.table.Table(data=[[1, 2, 3, 4]]))
    j1.append(astropy.table.Table(data=[[1, 2, 3, 4]]))
    assert isinstance(j1, JSOCResponse)
    assert all(j1.table == astropy.table.vstack([astropy.table.Table(
        data=[[1, 2, 3, 4]]), astropy.table.Table(data=[[1, 2, 3, 4]])]))


def test_jsocresponse_single():
    j1 = JSOCResponse(table=None)
    assert len(j1) == 0
    j1.append(astropy.table.Table(data=[[1, 2, 3, 4]]))
    assert all(j1.table == astropy.table.Table(data=[[1, 2, 3, 4]]))
    assert len(j1) == 4


def test_empty_jsoc_response():
    Jresp = JSOCResponse()
    assert Jresp.table is None
    assert Jresp.query_args is None
    assert Jresp.requestIDs is None
    assert str(Jresp) == 'None'
    assert repr(Jresp) == 'None'
    assert len(Jresp) == 0


@pytest.mark.online
def test_query():
    Jresp = client.search(
        attrs.Time('2012/1/1T00:00:00', '2012/1/1T00:01:30'),
        attrs.Series('hmi.M_45s'), vso_attrs.Sample(90 * u.second))
    assert isinstance(Jresp, JSOCResponse)
    assert len(Jresp) == 2


@pytest.mark.flaky(reruns=5)
@pytest.mark.online
def test_post_pass():
    responses = client.search(
        attrs.Time('2012/1/1T00:00:00', '2012/1/1T00:00:45'),
        attrs.Series('hmi.M_45s'), attrs.Notify('jsoc@cadair.com'))
    aa = client.request_data(responses)
    tmpresp = aa._d
    assert tmpresp['protocol'] == 'fits'
    assert tmpresp['method'] == 'url'


@pytest.mark.online
def test_post_wavelength():
    responses = client.search(
        attrs.Time('2010/07/30T13:30:00', '2010/07/30T14:00:00'),
        attrs.Series('aia.lev1_euv_12s'), attrs.Wavelength(193 * u.AA) |
        attrs.Wavelength(335 * u.AA), attrs.Notify('jsoc@cadair.com'))
    aa = client.request_data(responses)
    tmpresp = aa[0]._d
    assert tmpresp['protocol'] == 'fits'
    assert tmpresp['method'] == 'url'
    assert tmpresp['count'] == '302'
    tmpresp = aa[1]._d
    assert tmpresp['protocol'] == 'fits'
    assert tmpresp['method'] == 'url'
    assert tmpresp['count'] == '302'


@pytest.mark.online
def test_post_notify_fail():
    responses = client.search(
        attrs.Time('2012/1/1T00:00:00', '2012/1/1T00:00:45'),
        attrs.Series('hmi.M_45s'))
    with pytest.raises(ValueError):
        client.request_data(responses)


@pytest.mark.online
def test_post_wave_series():
    with pytest.raises(TypeError):
        client.search(
            attrs.Time('2012/1/1T00:00:00', '2012/1/1T00:00:45'),
            attrs.Series('hmi.M_45s') | attrs.Series('aia.lev1_euv_12s'),
            attrs.Wavelength(193 * u.AA) | attrs.Wavelength(335 * u.AA))


@pytest.mark.online
def test_wait_get():
    responses = client.search(
        attrs.Time('2012/1/1T1:00:36', '2012/1/1T01:00:38'),
        attrs.Series('hmi.M_45s'), attrs.Notify('jsoc@cadair.com'))
    path = tempfile.mkdtemp()
    res = client.fetch(responses, path=path)
    assert isinstance(res, Results)
    assert res.total == 1


@pytest.mark.online
def test_get_request():
    responses = client.search(
        attrs.Time('2012/1/1T1:00:36', '2012/1/1T01:00:38'),
        attrs.Series('hmi.M_45s'), attrs.Notify('jsoc@cadair.com'))

    bb = client.request_data(responses)
    path = tempfile.mkdtemp()
    aa = client.get_request(bb, path=path)
    assert isinstance(aa, Results)


@pytest.mark.online         # passed
def test_invalid_query():
    with pytest.raises(ValueError):
        client.search(attrs.Time('2012/1/1T01:00:00', '2012/1/1T01:00:45'))


@pytest.mark.online          # PASSED
def test_lookup_records_errors():
    d1 = {'end_time': datetime.datetime(2014, 1, 1, 1, 0, 35),
          'start_time': datetime.datetime(2014, 1, 1, 0, 0, 35)
         }
    with pytest.raises(ValueError):
        client._lookup_records(d1)

    d1.update({'series': 'aia.lev1_euv_12s'})
    d1.update({'keys' : 123})
    with pytest.raises(TypeError):
        client._lookup_records(d1)

    d1['keys'] = 'T_OBS'
    d1.update({'primekey': {'foo': 'bar'}})
    with pytest.raises(ValueError):
        client._lookup_records(d1)

    del d1['primekey']
    d1.update({'segment': 123})
    with pytest.raises(TypeError):
        client._lookup_records(d1)
    
    d1.update({'segment': 'foo'})
    with pytest.raises(ValueError):
        client._lookup_records(d1)

    del d1['segment']
    d1.update({'series': 'hmi.m_45s'})
    with pytest.raises(TypeError):
        client._lookup_records(d1)


@pytest.mark.online
def test_make_recordset_errors():
    d1 = {'series': 'aia.lev1_euv_12s'}
    with pytest.raises(ValueError):
        client._make_recordset(**d1)

    d1.update({
        'end_time': datetime.datetime(2014, 1, 1, 1, 0, 35),
        'start_time': datetime.datetime(2014, 1, 1, 0, 0, 35),
        'primekey': {'T_REC' : '2014.01.01_00:00:35_TAI-2014.01.01_01:00:35_TAI'}
        })

    with pytest.raises(ValueError):
        client._make_recordset(**d1)

    d1.update({
        'end_time': datetime.datetime(2014, 1, 1, 1, 0, 35),
        'start_time': datetime.datetime(2014, 1, 1, 0, 0, 35),
        'wavelength' : 604*u.AA,
        'primekey': {'WAVELNTH' : '604'}
        })

    with pytest.raises(ValueError):
        client._make_recordset(**d1)

@pytest.mark.online
def test_make_recordset():
    d1 = {'series': 'aia.lev1_euv_12s',
          'end_time': datetime.datetime(2014, 1, 1, 1, 0, 35),
          'start_time': datetime.datetime(2014, 1, 1, 0, 0, 35)
          }
    exp = 'aia.lev1_euv_12s[2014.01.01_00:00:35_TAI-2014.01.01_01:00:35_TAI]'
    assert client._make_recordset(**d1) == exp

    d1.update({'wavelength' : 604*u.AA})
    exp = 'aia.lev1_euv_12s[2014.01.01_00:00:35_TAI-2014.01.01_01:00:35_TAI][604]'
    assert client._make_recordset(**d1) == exp

    del d1['wavelength']
    d1.update({'primekey': {'WAVELNTH': '604'}})
    assert client._make_recordset(**d1) == exp

    del d1['start_time'], d1['end_time']
    d1['primekey'].update({'T_REC': '2014.01.01_00:00:35_TAI-2014.01.01_01:00:35_TAI'})
    exp = 'aia.lev1_euv_12s[2014.01.01_00:00:35_TAI-2014.01.01_01:00:35_TAI]'
    assert client._make_recordset(**d1) == exp

    d1 = {'series': 'hmi.v_45s',
          'end_time': datetime.datetime(2014, 1, 1, 1, 0, 35),
          'start_time': datetime.datetime(2014, 1, 1, 0, 0, 35),
          'segment': 'foo,bar'
          }
    exp = 'hmi.v_45s[2014.01.01_00:00:35_TAI-2014.01.01_01:00:35_TAI]{foo,bar}'
    assert client._make_recordset(**d1) == exp

    d1['segment'] = ['foo', 'bar']
    assert client._make_recordset(**d1) == exp

    d1 = {'series': 'hmi.sharp_720s',
          'end_time': datetime.datetime(2014, 1, 1, 1, 0, 35),
          'start_time': datetime.datetime(2014, 1, 1, 0, 0, 35),
          'segment': ['continuum', 'magnetogram']
          'primekey': {'HARPNUM': '4864'}
          }


@pytest.mark.online
def test_search_metadata():
    metadata = client.search_metadata(attrs.Time('2014-01-01T00:00:00', '2014-01-01T00:02:00'),
                                      attrs.Series('aia.lev1_euv_12s'), attrs.Wavelength(304*u.AA))
    assert isinstance(metadata, pd.DataFrame)
    assert metadata.shape == (11, 176)
    for i in metadata.index.values:
        assert (i.startswith('aia.lev1_euv_12s') and i.endswith('[304]'))

@pytest.mark.online
def test_request_data_error():
    responses = client.query(
        attrs.Time('2012/1/1T1:00:36', '2012/1/1T01:00:38'),
        attrs.Series('hmi.M_45s'), attrs.Notify('jsoc@cadair.com'),
        attrs.Protocol('foo'))
    with pytest.raises(TypeError):
        req = client.request_data(responses)


@pytest.mark.online
def test_request_data_protocol():
    responses = client.query(
        attrs.Time('2012/1/1T1:00:36', '2012/1/1T01:00:38'),
        attrs.Series('hmi.M_45s'), attrs.Notify('jsoc@cadair.com'))
    req = client.request_data(responses)
    assert req._d['method'] == 'url'
    assert req._d['protcol'] == 'fits'

    responses = client.query(
        attrs.Time('2012/1/1T1:00:36', '2012/1/1T01:00:38'),
        attrs.Series('hmi.M_45s'), attrs.Notify('jsoc@cadair.com'),
        attrs.Protocol('fits'))
    req = client.request_data(responses)
    assert req._d['method'] == 'url'
    assert req._d['protcol'] == 'fits'

    responses = client.query(
        attrs.Time('2012/1/1T1:00:36', '2012/1/1T01:00:38'),
        attrs.Series('hmi.M_45s'), attrs.Notify('jsoc@cadair.com'),
        attrs.Protocol('as-is'))
    req = client.request_data(responses)
    assert req._d['method'] == 'url_quick'
    assert req._d['protcol'] == 'as-is'


@pytest.mark.online
def test_check_request():
    responses = client.query(
        attrs.Time('2012/1/1T1:00:36', '2012/1/1T01:00:38'),
        attrs.Series('hmi.M_45s'), attrs.Notify('jsoc@cadair.com'))
    req = client.request_data(responses)
    assert client.check_request(req) == 0
