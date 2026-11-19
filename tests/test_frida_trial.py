import unittest
from unittest.mock import Mock, patch

import frida
import ultra0
import wizard


class FridaTrialTests(unittest.TestCase):
    def run_messages(self, messages=(), load_error=None):
        script, session, device = Mock(), Mock(), Mock()
        device.attach.return_value = session
        session.create_script.return_value = script
        callbacks = {}
        script.on.side_effect = lambda name, fn: callbacks.update({name: fn})

        def load():
            if load_error:
                raise load_error
            for message in messages:
                callbacks['message'](message, None)

        script.load.side_effect = load
        with patch.object(frida, '__version__', '17.24.3'), \
             patch.object(frida, 'get_usb_device', return_value=device):
            result = ultra0.run_trial(123, wait=0)
        script.unload.assert_called_once()
        session.detach.assert_called_once()
        return result, callbacks['message'], session

    def test_javascript_error_is_reported_and_bridge_is_bundled(self):
        result, _, session = self.run_messages([
            {'type': 'error', 'description': 'ReferenceError: Java is not defined',
             'stack': 'test stack'},
        ])
        self.assertEqual(result['errors'][0]['ev'], 'frida_error')
        self.assertEqual(result['errors'][0]['stack'], 'test stack')
        self.assertFalse(result['timed_out'])
        self.assertIn('globalThis.Java', session.create_script.call_args.args[0])

    def test_no_trial_requires_an_explicit_query_result(self):
        result, _, _ = self.run_messages([
            {'type': 'send', 'payload': {'ev': 'pd', 'code': 0, 'n': 0}},
            {'type': 'send', 'payload': {'ev': 'no_trial', 'reason': 'no_products'}},
        ])
        self.assertTrue(result['no_trial'])
        self.assertEqual(result['errors'], [])

    def test_billing_setup_failure_is_not_no_trial(self):
        result, _, _ = self.run_messages([
            {'type': 'send', 'payload': {'ev': 'setup', 'code': 3}},
        ])
        self.assertEqual(result['errors'][0]['code'], 3)
        self.assertFalse(result['no_trial'])

    def test_timeout_ignores_late_callbacks(self):
        result, callback, _ = self.run_messages()
        self.assertTrue(result['timed_out'])
        callback({'type': 'send', 'payload': {'ev': 'launched', 'code': 0}}, None)
        self.assertIsNone(result['launched'])
        self.assertEqual(result['events'], [])

    def test_load_failure_releases_script_and_session(self):
        result, _, _ = self.run_messages(load_error=RuntimeError('load failed'))
        self.assertEqual(result['errors'][0]['ev'], 'injection_error')

    def test_report_separates_technical_failures_from_no_trial(self):
        cases = [
            ({'errors': [{'ev': 'frida_error'}]}, 'injection_failed'),
            ({'no_trial': True}, 'no_trial'),
            ({'timed_out': True}, 'query_timeout'),
            ({'launched': {'code': 3}}, 'billing_launch_failed'),
        ]
        for extra, expected in cases:
            with self.subTest(status=expected):
                trial = {'offers': [], 'launched': None, 'errors': [], **extra}
                with patch.object(ultra0, 'sh', return_value='package:/test.apk'), \
                     patch.object(ultra0, 'switch_play', return_value=True), \
                     patch.object(ultra0, 'launch_app', return_value=123), \
                     patch.object(ultra0, 'run_trial', return_value=trial):
                    result = ultra0.process('test@example.com', add=False)
                self.assertEqual(result['status'], expected)
                self.assertNotIn('换个号', wizard.interpret(result)[1])


if __name__ == '__main__':
    unittest.main()
