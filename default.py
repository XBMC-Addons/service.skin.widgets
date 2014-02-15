#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2012-2013 Team-XBMC
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#    This script is based on script.randomitems & script.wacthlist
#    Thanks to their original authors

import sys
import xbmc
import xbmcgui
import datetime
import lib.common
from lib.common import log
from lib.utils import media_path, media_streamdetails
from lib.properties import gui
from lib.requests import req

GUI = gui()
REQ = req()
WINDOW = xbmcgui.Window(10000)
LIMIT = 20

### get addon info
__addon__        = lib.common.__addon__
__addonprofile__ = lib.common.__addonprofile__
__version__      = lib.common.__version__

class Main:
    def __init__(self):
        self._parse_argv()
        # check how we were executed
        if self.MOVIEID:
            xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Player.Open", "params": { "item": { "movieid": %d }, "options":{ "resume": %s } }, "id": 1 }' % (int(self.MOVIEID), self.RESUME))
        elif self.EPISODEID:
            xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Player.Open", "params": { "item": { "episodeid": %d }, "options":{ "resume": %s }  }, "id": 1 }' % (int(self.EPISODEID), self.RESUME))
        elif self.MUSICVIDEOID:
            xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Player.Open", "params": { "item": { "musicvideoid": %d } }, "id": 1 }' % int(self.MUSICVIDEOID))
        elif self.ALBUMID:
            xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Player.Open", "params": { "item": { "albumid": %d } }, "id": 1 }' % int(self.ALBUMID))
        elif self.SONGID:
            xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Player.Open", "params": { "item": { "songid": %d } }, "id": 1 }' % int(self.SONGID))
        else:
            self._init_vars()
            self._init_property()
            # clear our property, if another instance is already running it should stop now
            WINDOW.clearProperty('SkinWidgets_Running')
            #a_total = datetime.datetime.now()
            self._fetch_info_randomitems()
            self._fetch_info_recommended()
            self._fetch_info_recentitems()
            #b_total = datetime.datetime.now()
            #c_total = b_total - a_total
            #log('Total time needed for all queries: %s' % c_total)
            # give a possible other instance some time to notice the empty property
            WINDOW.setProperty('SkinWidgets_Running', 'true')
            self._daemon()

    def _init_vars(self):
        self.Player = Widgets_Player(action = self._update)
        self.Monitor = Widgets_Monitor(update_listitems = self._update, update_settings = self._on_change)

    def _on_change(self):
        self._init_property()
        self._fetch_info_randomitems()
        self._fetch_info_recommended()
        self._fetch_info_recentitems()

    def _init_property(self):
        WINDOW.setProperty('SkinWidgets_Recommended', '%s' % __addon__.getSetting("recommended_enable"))
        WINDOW.setProperty('SkinWidgets_RandomItems', '%s' % __addon__.getSetting("randomitems_enable"))
        WINDOW.setProperty('SkinWidgets_RecentItems', '%s' % __addon__.getSetting("recentitems_enable"))
        WINDOW.setProperty('SkinWidgets_RandomItems_Update', 'false')
        self.RANDOMITEMS_UPDATE_METHOD = int(__addon__.getSetting("randomitems_method"))
        self.RECENTITEMS_HOME_UPDATE = __addon__.getSetting("recentitems_homeupdate")
        # convert time to seconds, times 2 for 0,5 second sleep compensation
        self.RANDOMITEMS_TIME = int(float(__addon__.getSetting("randomitems_time"))) * 60 * 2

    def _parse_argv( self ):
        try:
            params = dict( arg.split( "=" ) for arg in sys.argv[ 1 ].split( "&" ) )
        except:
            params = {}
        self.MOVIEID = params.get( "movieid", "" )
        self.EPISODEID = params.get( "episodeid", "" )
        self.MUSICVIDEOID = params.get( "musicvideoid", "" )
        self.ALBUMID = params.get( "albumid", "" )
        self.SONGID = params.get( "songid", "" )
        self.RESUME = "true"
        for arg in sys.argv:
            param = str(arg)
            if 'resume=' in param:
                if param.replace('resume=', '') == "false":
                    self.RESUME = "false"

    def _fetch_info_recommended(self):
        #a = datetime.datetime.now()
        if __addon__.getSetting("recommended_enable") == 'true':
            self._fetch_movies('RecommendedMovie')
            self._fetch_episodes_recommended('RecommendedEpisode')
            self._fetch_albums('RecommendedAlbum')
            self._fetch_musicvideos('RecommendedMusicVideo')
            #b = datetime.datetime.now()
            #c = b - a
            #log('Total time needed to request recommended queries: %s' % c)

    def _fetch_info_randomitems(self):
        #a = datetime.datetime.now()
        if __addon__.getSetting("randomitems_enable") == 'true':
            self._fetch_movies('RandomMovie')
            self._fetch_tvshows('RandomEpisode')
            self._fetch_musicvideos('RandomMusicVideo')
            self._fetch_albums('RandomAlbum')
            self._fetch_artists('RandomArtist')
            self._fetch_songs('RandomSong')
            self._fetch_addons('RandomAddon')
            #b = datetime.datetime.now()
            #c = b - a
            #log('Total time needed to request random queries: %s' % c)

    def _fetch_info_recentitems(self):
        #a = datetime.datetime.now()
        if __addon__.getSetting("recentitems_enable") == 'true':
            self._fetch_movies('RecentMovie')
            self._fetch_tvshows('RecentEpisode')
            self._fetch_musicvideos('RecentMusicVideo')
            self._fetch_albums('RecentAlbum')
            #b = datetime.datetime.now()
            #c = b - a
            #log('Total time needed to request recent items queries: %s' % c)
            
    def _fetch_movies(self, request):
        if not xbmc.abortRequested:
            data = REQ.movies(request)
            GUI.movies(request, data)

    def _fetch_episodes_recommended(self, request):
        if not xbmc.abortRequested:
            data = REQ.episodes_recommended(request)
            GUI.episodes_recommended(request, data)

    def _fetch_tvshows(self, request):
        if not xbmc.abortRequested:
            data = REQ.episodes(request)
            GUI.episodes(request, data)

    def _fetch_musicvideos(self, request):
        if not xbmc.abortRequested:
            data = REQ.musicvideos(request)
            GUI.musicvideos(request, data)

    def _fetch_albums(self, request):
        if not xbmc.abortRequested:
            data = REQ.albums(request)
            GUI.albums(request, data)

    def _fetch_artists(self, request):
        if not xbmc.abortRequested:
            data = REQ.artist(request)
            GUI.artists(request, data)

    def _fetch_songs(self, request):
        if not xbmc.abortRequested:
            data = REQ.songs(request)
            GUI.songs(request, data)

    def _fetch_addons(self, request):
        if not xbmc.abortRequested:
            data = REQ.addons(request)
            GUI.addons(request, data)

    def _daemon(self):
        # deamon is meant to keep script running at all time
        count = 0
        home_update = False
        while (not xbmc.abortRequested) and WINDOW.getProperty('SkinWidgets_Running') == 'true':
            xbmc.sleep(500)
            if not xbmc.Player().isPlayingVideo():
                if self.RANDOMITEMS_UPDATE_METHOD == 0:
                    count += 1
                    if count == self.RANDOMITEMS_TIME:
                        self._fetch_info_randomitems()
                        count = 0    # reset counter
                if WINDOW.getProperty('SkinWidgets_RandomItems_Update') == 'true':
                    count = 0
                    WINDOW.setProperty('SkinWidgets_RandomItems_Update','false')
                    self._fetch_info_randomitems()
                if  self.RECENTITEMS_HOME_UPDATE == 'true' and home_update and xbmcgui.getCurrentWindowId() == 10000:
                    self._fetch_info_recentitems()
                    home_update = False
                elif self.RECENTITEMS_HOME_UPDATE == 'true' and not home_update and xbmcgui.getCurrentWindowId() != 10000:
                    home_update = True

    def _update(self, type):
        xbmc.sleep(1000)
        if type == 'movie':
            self._fetch_movies('RecommendedMovie')
            self._fetch_movies('RecentMovie')
        elif type == 'episode':
            self._fetch_episodes_recommended('RecommendedEpisode')
            self._fetch_tvshows('RecentEpisode')
        elif type == 'video':
            #only on db update
            self._fetch_movies('RecommendedMovie')
            self._fetch_episodes_recommended('RecommendedEpisode')
            self._fetch_movies('RecentMovie')
            self._fetch_tvshows('RecentEpisode')
            self._fetch_musicvideos('RecentMusicVideo')
        elif type == 'music':
            self._fetch_albums('RecommendedAlbum')
            self._fetch_albums('RecentAlbum')
        if self.RANDOMITEMS_UPDATE_METHOD == 1:
            # update random if db update is selected instead of timer
            if type == 'video':
                self._fetch_movies('RandomMovie')
                self._fetch_tvshows('RandomEpisode')
                self._fetch_musicvideos('RandomMusicVideo')
            elif type == 'music':
                self._fetch_albums('RandomAlbum')
                self._fetch_artists('RandomArtist')
                self._fetch_songs('RandomSong')
                self._fetch_addons('RandomAddon')

class Widgets_Monitor(xbmc.Monitor):
    def __init__(self, *args, **kwargs):
        xbmc.Monitor.__init__(self)
        self.update_listitems = kwargs['update_listitems']
        self.update_settings = kwargs['update_settings']

    def onDatabaseUpdated(self, database):
        self.update_listitems(database)
        
    def onSettingsChanged(self):
        self.update_settings()

class Widgets_Player(xbmc.Player):
    def __init__(self, *args, **kwargs):
        xbmc.Player.__init__(self)
        self.type = ""
        self.action = kwargs[ "action" ]
        self.substrings = [ '-trailer', 'http://' ]

    def onPlayBackStarted(self):
        xbmc.sleep(1000)
        # Set values based on the file content
        if (self.isPlayingAudio()):
            self.type = "music"  
        else:
            if xbmc.getCondVisibility('VideoPlayer.Content(movies)'):
                filename = ''
                isMovie = True
                try:
                    filename = self.getPlayingFile()
                except:
                    pass
                if filename != '':
                    for string in self.substrings:
                        if string in filename:
                            isMovie = False
                            break
                if isMovie:
                    self.type = "movie"
            elif xbmc.getCondVisibility('VideoPlayer.Content(episodes)'):
                # Check for tv show title and season to make sure it's really an episode
                if xbmc.getInfoLabel('VideoPlayer.Season') != "" and xbmc.getInfoLabel('VideoPlayer.TVShowTitle') != "":
                    self.type = "episode"

    def onPlayBackEnded(self):
        self.onPlayBackStopped()

    def onPlayBackStopped(self):
        if self.type == 'movie':
            self.action('movie')
        elif self.type == 'episode':
            self.action('episode')
        elif self.type == 'music':
            self.action('music')
        self.type = ""

if (__name__ == "__main__"):
    log('script version %s started' % __version__)
    Main()
    del Widgets_Monitor
    del Widgets_Player
    del Main
    log('script version %s stopped' % __version__)
