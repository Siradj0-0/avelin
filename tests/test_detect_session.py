import unittest
from avelin.detect.session import SessionHints, detect_session


class SessionTests(unittest.TestCase):
    def test_desktop_and_type_are_separate(self):
        result = detect_session({'XDG_CURRENT_DESKTOP': 'ubuntu:GNOME',
                                 'XDG_SESSION_DESKTOP': 'GNOME',
                                 'XDG_SESSION_TYPE': 'wayland'})
        self.assertEqual(result, SessionHints(('ubuntu', 'GNOME'), 'GNOME', 'wayland'))

    def test_conflicting_evidence_is_retained(self):
        result = detect_session({'XDG_CURRENT_DESKTOP': 'KDE',
                                 'XDG_SESSION_DESKTOP': 'GNOME',
                                 'XDG_SESSION_TYPE': 'x11'})
        self.assertEqual(result.current_desktops, ('KDE',))
        self.assertEqual(result.session_desktop, 'GNOME')
        self.assertEqual(result.session_type, 'x11')

    def test_unknowns_and_malformed_single_desktop(self):
        for env in ({}, {'XDG_SESSION_TYPE': 'unknown'}, {'XDG_SESSION_TYPE': 'unspecified'}):
            self.assertEqual(detect_session(env).session_type, None)
        self.assertIsNone(detect_session({'XDG_SESSION_DESKTOP': 'A:B'}).session_desktop)
        self.assertEqual(detect_session({'XDG_CURRENT_DESKTOP': ':XFCE::'}).current_desktops, ('XFCE',))

    def test_recognized_session_types(self):
        for kind in ('x11', 'wayland', 'tty', 'mir', 'web'):
            with self.subTest(kind=kind):
                self.assertEqual(detect_session({'XDG_SESSION_TYPE': kind}).session_type, kind)

    def test_legacy_desktop_session_is_not_authoritative(self):
        self.assertEqual(detect_session({'DESKTOP_SESSION': 'gnome'}), SessionHints((), None, None))


if __name__ == '__main__':
    unittest.main()
