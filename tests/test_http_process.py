"""Transport failures must cross real worker boundaries without killing peers."""
import multiprocessing
import unittest
from concurrent.futures import ProcessPoolExecutor
from mira_runner.client import HTTPFailure


def raise_http_failure():
    raise HTTPFailure(429, '{"error":"upstream rate limit"}')


def return_value(value):
    return value


class HTTPFailureProcessTests(unittest.TestCase):
    def test_http_failure_preserves_details_and_pool_survives(self):
        with ProcessPoolExecutor(max_workers=2,
                mp_context=multiprocessing.get_context('spawn')) as pool:
            failed = pool.submit(raise_http_failure)
            peer = pool.submit(return_value, 'peer completed')
            with self.assertRaises(HTTPFailure) as caught:
                failed.result(timeout=15)
            self.assertEqual(caught.exception.status, 429)
            self.assertEqual(caught.exception.body, '{"error":"upstream rate limit"}')
            self.assertEqual(str(caught.exception), 'OpenRouter HTTP 429')
            self.assertEqual(peer.result(timeout=15), 'peer completed')
            self.assertEqual(pool.submit(return_value, 'still usable').result(timeout=15),
                             'still usable')


if __name__ == '__main__':
    unittest.main()
