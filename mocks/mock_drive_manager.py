"""Module containing the definition of a mocked out GDocs dependency. This is for test use only"""

class MockDriveManager():
    """Mocked out version of DriveManager for test purposes"""

    def __init__(self):
        none = None
        self.file_entries = None
    
    # Mock Override APIs

    def set_file_entries_return(self, file_entries):
        """Takes a param of type Dictionary<string, List<{name, data, id}>> and forces the mock to return it.
           Format is a Dictionary where the key is the file name
           and the value is a list of {name, data, id} objects"""
        
        self.file_entries = file_entries

    # Mock APIs adhering to interface from 

    def get_file_entries(self, file):
        return self.file_entries[file['id']]

    def get_drive_filetype(self):
        none = None

    def get_all_books_sheets(self):
        none = None

    def get_games_result(self):
        none = None

    def convert_rank(self):
        none = None

    def get_current_leaders(self):
        none = None

    def get_unwritten_leaderboard_games(self):
        none = None

    def get_history_game_points(self):
        none = None

    def overwrite_leaderboard(self):
        none = None

    def update_answerkey_results(self):
        none = None

    def update_game_start_time(self):
        none = None

    def create_new_sheet(self):
        none = None

    def new_response_data_available(self):
        none = None
