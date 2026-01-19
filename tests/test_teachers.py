import unittest

from app.core.teachers import find_teacher_profile, get_teacher_profile, list_teacher_profiles


class TeacherProfileTests(unittest.TestCase):
    def test_list_profiles_has_defaults(self) -> None:
        profiles = list_teacher_profiles()
        self.assertGreaterEqual(len(profiles), 3)
        self.assertTrue(any(profile.id == "klara" for profile in profiles))

    def test_find_profile_normalizes_id(self) -> None:
        profile = find_teacher_profile("KLARA")
        self.assertIsNotNone(profile)
        self.assertEqual(profile.id, "klara")

    def test_get_profile_falls_back_to_default(self) -> None:
        profile = get_teacher_profile("unknown")
        self.assertEqual(profile.id, "klara")


if __name__ == "__main__":
    unittest.main()
