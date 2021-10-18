from pysnmp import hlapi


def construct_object_types(list_of_oids):
    return [hlapi.ObjectType(hlapi.ObjectIdentity(oid)) for oid in list_of_oids]


def construct_value_pairs(list_of_pairs):
    return [
        hlapi.ObjectType(hlapi.ObjectIdentity(key), value)
        for key, value in list_of_pairs.items()
    ]


def get(target, oids, credentials, port=161, engine=hlapi.SnmpEngine(), context=hlapi.ContextData()):
    handler = hlapi.getCmd(
        engine,
        credentials,
        hlapi.UdpTransportTarget((target, port)),
        context,
        *construct_object_types(oids)
    )
    return fetch(handler, 1)[0]


def set(target, value_pairs, credentials, port=161, engine=hlapi.SnmpEngine(), context=hlapi.ContextData()):
    handler = hlapi.setCmd(
        engine,
        credentials,
        hlapi.UdpTransportTarget((target, port)),
        context,
        *construct_value_pairs(value_pairs)
    )
    return fetch(handler, 1)[0]


def get_bulk(target, oids, credentials, count, start_from=0, port=161,
             engine=hlapi.SnmpEngine(), context=hlapi.ContextData()):
    handler = hlapi.bulkCmd(
        engine,
        credentials,
        hlapi.UdpTransportTarget((target, port)),
        context,
        start_from, count,
        *construct_object_types(oids)
    )
    return fetch(handler, count)


def get_bulk_auto(target, oids, credentials, count_oid, start_from=0, port=161,
                  engine=hlapi.SnmpEngine(), context=hlapi.ContextData()):
    count = get(target, [count_oid], credentials, port, engine, context)[count_oid]
    return get_bulk(target, oids, credentials, count, start_from, port, engine, context)


def cast(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        try:
            return float(value)
        except (ValueError, TypeError):
            try:
                return str(value)
            except (ValueError, TypeError):
                pass
    return value


def fetch(handler, count):
    result = []
    for _ in range(count):
        try:
            error_indication, error_status, error_index, var_binds = next(handler)
            if error_indication or error_status:
                raise RuntimeError('Got SNMP error: {0}'.format(error_indication))
            items = {str(var_bind[0]): cast(var_bind[1]) for var_bind in var_binds}
            result.append(items)
        except StopIteration:
            break
    return result
