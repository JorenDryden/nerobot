class Playlist:
    def __init__(self, title):
        self.title = title
        self.tracks = []

    def add_track(self, track):
        self.tracks.append(track)

    def remove_track(self, track):
        self.tracks.remove(track)

    def get_title(self):
        return self.title

    def get_tracks(self):
        return self.tracks