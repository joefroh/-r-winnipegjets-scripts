import unittest

from gwg_leader_updater import GWGLeaderUpdater

# import test mocks
from mocks.mock_drive_manager import MockDriveManager
from mocks.mock_secret_manager import MockSecretManager

class TestGWGLeaderUpdater(unittest.TestCase):

    # setup and teardown methods
    # these get ran before EVERY test method below
    def setUp(self):
        gwg_args = lambda: None
        gwg_args.test = True
        gwg_args.debug = False
        gwg_args.single = False
        gwg_args.prod = False

        self.gwg_leader_updater = GWGLeaderUpdater(MockDriveManager(), MockSecretManager(), gwg_args)

#    def tearDown(self): 
# un-comment and define if a tear down method is ever needed

    # test cases
    def test_constructor_return_not_null(self):
        self.assertIsInstance(self.gwg_leader_updater, GWGLeaderUpdater, "If this test fails, you changed the type of the test prop. Don't do that.")

    def test_get_list_of_entries_happy_path(self):
        test_file = lambda: None
        test_file.name = "test file"
        test_file.id = 0
        test_file.data = None

        test_artifact = {'test': test_file}
        self.gwg_leader_updater.gdrive.set_file_entries_return(test_artifact)

        result = self.gwg_leader_updater.get_list_of_entries([{"id":"test", "createdDate":0}])[0]
        self.assertEqual(test_file, result)
    
    def test_format_results_data(self):
        self.assertIsNone("Not implemented")

    def test_get_players_points(self):
        self.assertIsNone("Not implemented")

    def test_get_gwg_answers(self):
        self.assertIsNone("Not implemented")

    def test_get_game_headers(self):
        self.assertIsNone("Not implemented")

    def test_create_game_history(self):
        self.assertIsNone("Not implemented")

    def test_add_user_rankings(self):
        self.assertIsNone("Not implemented")

    def test_add_new_user_points(self):
        self.assertIsNone("Not implemented")

    def test_update_master_list(self):
        self.assertIsNone("Not implemented")

    def test_alert_late_users(self):
        self.assertIsNone("Not implemented")

    def test_update_leaderboard_spreadsheet(self):
        self.assertIsNone("Not implemented")

    def test_convert_response_filename(self):
        self.assertIsNone("Not implemented")

    def test_get_pending_game_data(self):
        self.assertIsNone("Not implemented")

    def test_notify_reddit(self):
        self.assertIsNone("Not implemented")

    def test_manage_gwg_leaderboard(self):
        self.assertIsNone("Not implemented")


if __name__ == '__main__':
    unittest.main()
