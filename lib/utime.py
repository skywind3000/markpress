#! /usr/bin/env python
# -*- coding: utf-8 -*-
#======================================================================
#
# utime.py - time related functions
#
# Created by skywind on 2018/08/02
# Last Modified: 2018/08/02 15:55:48
#
#======================================================================
from __future__ import print_function
import sys
import time
import datetime


#----------------------------------------------------------------------
# python 2/3 compatible
#----------------------------------------------------------------------
if sys.version_info[0] >= 3:
    long = int
    unicode = str
    xrange = range


#----------------------------------------------------------------------
# timezone
#----------------------------------------------------------------------
class timezone(datetime.tzinfo):
    """Backport of datetime.timezone.
    Notes
    -----
    Backport of datetime.timezone for Python 2.7, from Python 3.6
    documentation (https://tinyurl.com/z4cegu9), copyright Python Software
    Foundation (https://docs.python.org/3/license.html)
    """
    __slots__ = '_offset', '_name'

    # Sentinel value to disallow None
    _Omitted = object()

    def __new__(cls, offset, name=_Omitted):
        if not isinstance(offset, datetime.timedelta):
            raise TypeError("offset must be a timedelta")
        if name is cls._Omitted:
            if not offset:
                return cls.utc
            name = None
        elif not isinstance(name, str):
            raise TypeError("name must be a string")
        if not cls._minoffset <= offset <= cls._maxoffset:
            raise ValueError("offset must be a timedelta "
                             "strictly between -timedelta(hours=24) and "
                             "timedelta(hours=24).")
        if (offset.microseconds != 0 or offset.seconds % 60 != 0):
            raise ValueError("offset must be a timedelta "
                             "representing a whole number of minutes")
        return cls._create(offset, name)

    @classmethod
    def _create(cls, offset, name=None):
        self = datetime.tzinfo.__new__(cls)
        self._offset = offset
        self._name = name
        return self

    def __getinitargs__(self):
        """pickle support"""
        if self._name is None:
            return (self._offset,)
        return (self._offset, self._name)

    def __eq__(self, other):
        if not isinstance(other, timezone):
            return False
        return self._offset == other._offset

    def __lt__(self, other):
        raise TypeError("'<' not supported between instances of"
                        " 'datetime.timezone' and 'datetime.timezone'")

    def __hash__(self):
        return hash(self._offset)

    def __repr__(self):
        if self is self.utc:
            return '%s.%s.utc' % (self.__class__.__module__,
                                  self.__class__.__name__)
        if self._name is None:
            return "%s.%s(%r)" % (self.__class__.__module__,
                                  self.__class__.__name__,
                                  self._offset)
        return "%s.%s(%r, %r)" % (self.__class__.__module__,
                                  self.__class__.__name__,
                                  self._offset, self._name)

    def __str__(self):
        return self.tzname(None)

    def utcoffset(self, dt):
        if isinstance(dt, datetime.datetime) or dt is None:
            return self._offset
        raise TypeError("utcoffset() argument must be a datetime instance"
                        " or None")

    def tzname(self, dt):
        if isinstance(dt, datetime.datetime) or dt is None:
            if self._name is None:
                return self._name_from_offset(self._offset)
            return self._name
        raise TypeError("tzname() argument must be a datetime instance"
                        " or None")

    def dst(self, dt):
        if isinstance(dt, datetime.datetime) or dt is None:
            return None
        raise TypeError("dst() argument must be a datetime instance"
                        " or None")

    def fromutc(self, dt):
        if isinstance(dt, datetime.datetime):
            if dt.tzinfo is not self:
                raise ValueError("fromutc: dt.tzinfo "
                                 "is not self")
            return dt + self._offset
        raise TypeError("fromutc() argument must be a datetime instance"
                        " or None")

    _maxoffset = datetime.timedelta(hours=23, minutes=59)
    _minoffset = -_maxoffset

    @staticmethod
    def _name_from_offset(delta):
        if not delta:
            return 'UTC'
        if delta < datetime.timedelta(0):
            sign = '-'
            delta = -delta
        else:
            sign = '+'
        hours, rest = divmod(delta.total_seconds(), 3600)
        hours = int(hours)
        minutes = rest // datetime.timedelta(minutes=1).total_seconds()
        minutes = int(minutes)
        return 'UTC{}{:02d}:{:02d}'.format(sign, hours, minutes)


timezone.utc = timezone._create(datetime.timedelta(0))
timezone.min = timezone._create(timezone._minoffset)
timezone.max = timezone._create(timezone._maxoffset)
timezone.cst = timezone._create(datetime.timedelta(hours = 8))

_EPOCH = datetime.datetime(1970, 1, 1, tzinfo=timezone.utc)


if sys.version_info[0] < 3:
    datetime.timezone = timezone



#----------------------------------------------------------------------
# Tools
#----------------------------------------------------------------------
DATETIME_FMT = '%Y-%m-%d %H:%M:%S'


#----------------------------------------------------------------------
# 1551884065 to datetime.dateime(2019, 3, 6, 22, 54, 25)
#----------------------------------------------------------------------
def timestamp_to_datetime (ts, tz = None):
    return datetime.datetime.fromtimestamp(ts, tz)


#----------------------------------------------------------------------
# datetime.datetime(2019, 3, 6, 22, 54, 25) -> 1551884065
#----------------------------------------------------------------------
def datetime_to_timestamp (dt):
    if hasattr(dt, 'timestamp'):
        return dt.timestamp()
    epoch = datetime.datetime.fromtimestamp(0, dt.tzinfo)
    return (dt - epoch).total_seconds()


#----------------------------------------------------------------------
# datetime.datetime(2019, 3, 6, 22, 54, 25) -> '2019-03-06 22:54:25'
#----------------------------------------------------------------------
def datetime_to_string (dt, fmt = None):
    return dt.strftime(fmt and fmt or DATETIME_FMT)


#----------------------------------------------------------------------
# '2019-03-06 22:54:25' -> datetime.datetime(2019, 3, 6, 22, 54, 25) 
#----------------------------------------------------------------------
def string_to_datetime (text, tz = None, fmt = None):
    dt = datetime.datetime.strptime(text, fmt and fmt or DATETIME_FMT)
    if tz:
        if hasattr(tz, 'localize'):
            # in case, we have pytz
            dt = tz.localize(dt)
        else:
            dt = dt.replace(tzinfo = tz)
    return dt


#----------------------------------------------------------------------
# 1551884065 -> '2019-03-06 22:54:25'
#----------------------------------------------------------------------
def timestamp_to_string (ts, tz = None):
    return datetime_to_string(timestamp_to_datetime(ts, tz))


#----------------------------------------------------------------------
# '2019-03-06 22:54:25' -> 1551884065
#----------------------------------------------------------------------
def string_to_timestamp (text, tz = None):
    return datetime_to_timestamp(string_to_datetime(text, tz))


#----------------------------------------------------------------------
# 1551884065 -> '2019-03-06T22:54:25.000Z'
#----------------------------------------------------------------------
def timestamp_to_iso (ts):
    dt = timestamp_to_datetime(ts, timezone.utc)
    return dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')


#----------------------------------------------------------------------
# '2019-03-06T22:54:25.000Z' -> 1551884065
#----------------------------------------------------------------------
def iso_to_timestamp (iso):
    iso = iso.strip()
    if iso[-1:].upper() != 'Z':
        raise ValueError('require an ISO 8601 UTC format')
    if iso[10:11].upper() != 'T':
        raise ValueError('require an ISO 8601 UTC format')
    if '.' in iso:
        if len(iso) >= 28:
            if iso[19:20] == '.':
                iso = iso[:26] + 'Z'
            else:
                raise ValueError('bad iso 8601 format')
        dt = datetime.datetime.strptime(iso[:-1], '%Y-%m-%dT%H:%M:%S.%f')
    else:
        if len(iso) == 17:
            iso = iso[:16] + ':00Z'
        elif len(iso) == 12:
            iso = iso[:11] + '00:00:00Z'
        dt = datetime.datetime.strptime(iso[:-1], '%Y-%m-%dT%H:%M:%S')
    dt = dt.replace(tzinfo = timezone.utc)
    return datetime_to_timestamp(dt)


#----------------------------------------------------------------------
# read timestamp from various format
#----------------------------------------------------------------------
def read_timestamp (timestamp, tz = None):
    if isinstance(timestamp, datetime.datetime):
        return datetime_to_timestamp(timestamp)
    elif isinstance(timestamp, int) or isinstance(timestamp, long):
        return timestamp
    elif isinstance(timestamp, float):
        return timestamp
    elif len(timestamp) == 10 and timestamp.isdigit():
        return int(timestamp)
    elif len(timestamp) == 13 and timestamp.isdigit():
        return float(timestamp) * 0.001
    elif timestamp.find('.') == 10 and timestamp[:10].isdigit():
        return float(timestamp)
    elif timestamp[:1].isdigit() and timestamp[4:5] == '-':
        if len(timestamp) == 19:
            return string_to_timestamp(timestamp, tz)
        elif len(timestamp) == 16:
            return string_to_timestamp(timestamp + ':00', tz)
        elif len(timestamp) == 10:
            return string_to_timestamp(timestamp + ' 00:00:00', tz)
    if timestamp[:1].isdigit() and timestamp[-1:] == 'Z':
        return iso_to_timestamp(timestamp)
    return timestamp



#----------------------------------------------------------------------
# compact string: YYYYMMDDHHMM 
#----------------------------------------------------------------------
def compact_from_timestamp(ts, tz = None, seconds = False):
    fmt1 = '%Y%m%d%H%M'
    fmt2 = '%Y%m%d%H%M%S'
    dt = timestamp_to_datetime(ts, tz)
    return dt.strftime(seconds and fmt2 or fmt1)


#----------------------------------------------------------------------
# utc to local without tz
#----------------------------------------------------------------------
def utc_to_local(utc):
    epoch = time.mktime(utc.timetuple())
    offset = datetime.datetime.fromtimestamp(epoch) - \
        datetime.datetime.utcfromtimestamp(epoch)
    return utc + offset


#----------------------------------------------------------------------
# local to utc
#----------------------------------------------------------------------
def local_to_utc(local):
    epoch = time.mktime(local.timetuple())
    offset = datetime.datetime.fromtimestamp(epoch) - \
        datetime.datetime.utcfromtimestamp(epoch)
    return local - offset


#----------------------------------------------------------------------
# testing case
#----------------------------------------------------------------------
if __name__ == '__main__':
    def test1():
        ts = time.time()
        uc = datetime.datetime.utcfromtimestamp(ts)
        uc = timestamp_to_datetime(ts, timezone.utc)
        print(ts)
        print(uc.tzinfo)
        print(datetime_to_timestamp(uc))
        return 0
    def test2():
        ts = time.time()
        print(ts)
        text = timestamp_to_iso(ts)
        print(timestamp_to_iso(ts))
        print(iso_to_timestamp(text))
        tt = '2018-08-31T09:45:56.0000000Z'
        print(len(tt))
        ts = iso_to_timestamp(tt)
        dt = timestamp_to_datetime(ts, timezone.utc)
        print(dt)
        print(read_timestamp('2018-01-01 12:00:32'))
    def test3():
        dt = datetime.datetime.fromtimestamp(time.time())
        print(dt)
        utc = local_to_utc(dt)
        print(utc)
        print(utc_to_local(utc))
        return 0
    test3()



