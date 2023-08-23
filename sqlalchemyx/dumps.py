import datetime
from decimal import Decimal


def to_dict(instance, fields=None, exclude_fields=None):
    keys = set()
    columns = set([
        c.name for c in
        instance.__table__.columns
    ])
    if fields:
        keys = columns & set(fields)
    if exclude_fields:
        keys = columns - set(exclude_fields)

    data = {}
    for key in keys:
        value = getattr(instance, key, None)
        if isinstance(value, datetime.datetime):
            data[key] = value.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(value, datetime.date):
            data[key] = value.strftime('%Y-%m-%d')
        elif isinstance(value, datetime.time):
            data[key] = value.strftime('%H:%M:%S')
        elif isinstance(value, Decimal):
            data[key] = '{0:f}'.format(value)
        else:
            data[key] = value

    return data
