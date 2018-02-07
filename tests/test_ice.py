import asyncio
import pprint
import unittest

from aioice import ice, stun, exceptions


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class IceTest(unittest.TestCase):
    def setUp(self):
        stun.RETRY_MAX = 2

    def test_parse_candidate(self):
        candidate = ice.parse_candidate(
            '6815297761 1 udp 659136 1.2.3.4 31102 typ host generation 0')
        self.assertEqual(candidate.foundation, '6815297761')
        self.assertEqual(candidate.component, 1)
        self.assertEqual(candidate.transport, 'udp')
        self.assertEqual(candidate.priority, 659136)
        self.assertEqual(candidate.host, '1.2.3.4')
        self.assertEqual(candidate.port, 31102)
        self.assertEqual(candidate.type, 'host')
        self.assertEqual(candidate.generation, 0)

    def test_connect(self):
        conn_a = ice.Connection(ice_controlling=True)
        conn_b = ice.Connection(ice_controlling=False)

        # invite
        candidates_a = run(conn_a.get_local_candidates())
        print('CANDIDATES A')
        pprint.pprint(candidates_a)
        conn_b.remote_username = conn_a.local_username
        conn_b.remote_password = conn_a.local_password
        conn_b.set_remote_candidates(candidates_a)

        # accept
        candidates_b = run(conn_b.get_local_candidates())
        print('CANDIDATES B')
        pprint.pprint(candidates_b)
        conn_a.remote_username = conn_b.local_username
        conn_a.remote_password = conn_b.local_password
        conn_a.set_remote_candidates(candidates_b)

        # connect
        run(asyncio.gather(conn_a.connect(), conn_b.connect()))

        # send data
        run(conn_a.send(b'howdee'))
        data = run(conn_b.recv())
        self.assertEqual(data, b'howdee')

        # close
        run(conn_a.close())
        run(conn_b.close())

    def test_connect_no_local_candidates(self):
        """
        If local candidates have not been gathered, connect fails.
        """
        conn = ice.Connection(ice_controlling=True)
        conn.remote_username = 'foo'
        conn.remote_password = 'bar'
        conn.set_remote_candidates([ice.parse_candidate(
            '6815297761 1 udp 659136 1.2.3.4 31102 typ host generation 0')])
        with self.assertRaises(exceptions.ConnectionError):
            run(conn.connect())
        run(conn.close())

    def test_connect_no_remote_candidates(self):
        """
        If remote candidates have not been provided, connect fails.
        """
        conn = ice.Connection(ice_controlling=True)
        run(conn.get_local_candidates())
        conn.remote_username = 'foo'
        conn.remote_password = 'bar'
        with self.assertRaises(exceptions.ConnectionError):
            run(conn.connect())
        run(conn.close())

    def test_connect_no_remote_credentials(self):
        """
        If remote credentials have not been provided, connect fails.
        """
        conn = ice.Connection(ice_controlling=True)
        run(conn.get_local_candidates())
        conn.set_remote_candidates([ice.parse_candidate(
            '6815297761 1 udp 659136 1.2.3.4 31102 typ host generation 0')])
        with self.assertRaises(exceptions.ImproperlyConfigured):
            run(conn.connect())
        run(conn.close())

    def test_connect_role_conflict_both_controlling(self):
        conn_a = ice.Connection(ice_controlling=True)
        conn_b = ice.Connection(ice_controlling=True)

        # invite
        candidates_a = run(conn_a.get_local_candidates())
        print('CANDIDATES A')
        pprint.pprint(candidates_a)
        conn_b.remote_username = conn_a.local_username
        conn_b.remote_password = conn_a.local_password
        conn_b.set_remote_candidates(candidates_a)

        # accept
        candidates_b = run(conn_b.get_local_candidates())
        print('CANDIDATES B')
        pprint.pprint(candidates_b)
        conn_a.remote_username = conn_b.local_username
        conn_a.remote_password = conn_b.local_password
        conn_a.set_remote_candidates(candidates_b)

        # connect
        with self.assertRaises(exceptions.ConnectionError):
            run(asyncio.gather(conn_a.connect(), conn_b.connect()))

        # close
        run(conn_a.close())
        run(conn_b.close())

    def test_connect_role_conflict_both_controlled(self):
        conn_a = ice.Connection(ice_controlling=False)
        conn_b = ice.Connection(ice_controlling=False)

        # invite
        candidates_a = run(conn_a.get_local_candidates())
        print('CANDIDATES A')
        pprint.pprint(candidates_a)
        conn_b.remote_username = conn_a.local_username
        conn_b.remote_password = conn_a.local_password
        conn_b.set_remote_candidates(candidates_a)

        # accept
        candidates_b = run(conn_b.get_local_candidates())
        print('CANDIDATES B')
        pprint.pprint(candidates_b)
        conn_a.remote_username = conn_b.local_username
        conn_a.remote_password = conn_b.local_password
        conn_a.set_remote_candidates(candidates_b)

        # connect
        with self.assertRaises(exceptions.ConnectionError):
            run(asyncio.gather(conn_a.connect(), conn_b.connect()))

        # close
        run(conn_a.close())
        run(conn_b.close())

    def test_connect_timeout(self):
        conn = ice.Connection(ice_controlling=True)
        run(conn.get_local_candidates())
        conn.remote_username = 'foo'
        conn.remote_password = 'bar'
        conn.set_remote_candidates([ice.parse_candidate(
            '6815297761 1 udp 659136 1.2.3.4 31102 typ host generation 0')])
        with self.assertRaises(exceptions.ConnectionError):
            run(conn.connect())
        run(conn.close())
