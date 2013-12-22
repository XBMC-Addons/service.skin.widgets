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

import os
import sys
import xbmc
import xbmcgui
import xbmcaddon
import random
import datetime
import _strptime
import urllib
import lib.common
from lib.common import log
from lib.utils import media_path, media_streamdetails
from lib.requests import req

if sys.version_info < (2, 7):
    import simplejson
else:
    import json as simplejson
REQ = req()

### get addon info
__addon__        = lib.common.__addon__
__addonid__      = lib.common.__addonid__
__addonname__    = lib.common.__addonname__
__addonpath__    = lib.common.__addonpath__
__addonprofile__ = lib.common.__addonprofile__
__localize__     = lib.common.__localize__
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
            self.WINDOW.clearProperty('SkinWidgets_Running')
            a_total = datetime.datetime.now()
            self._fetch_info_randomitems()
            self._fetch_info_recommended()
            self._fetch_info_recentitems()
            b_total = datetime.datetime.now()
            c_total = b_total - a_total
            log('Total time needed for all queries: %s' % c_total)
            # give a possible other instance some time to notice the empty property
            self.WINDOW.setProperty('SkinWidgets_Running', 'true')
            self._daemon()

    def _init_vars(self):
        self.WINDOW = xbmcgui.Window(10000)
        self.Player = Widgets_Player(action = self._update)
        self.Monitor = Widgets_Monitor(update_listitems = self._update, update_settings = self._on_change)
        self.LIMIT = 20

    def _on_change(self):
        clearlist_groups = ['Recommended','Random','Recent']
        clearlist_types = ['Movie','Episode','MusicVideo','Album', 'Artist','Song','Addon']
        for item_group in clearlist_groups:
            for item_type in clearlist_types:
                clear = item_group + item_type
                self._clear_properties(clear)
        self._init_property()
        self._fetch_info_randomitems()
        self._fetch_info_recommended()
        self._fetch_info_recentitems()

    def _init_property(self):
        self.WINDOW.setProperty('SkinWidgets_Recommended', '%s' % __addon__.getSetting("recommended_enable"))
        self.WINDOW.setProperty('SkinWidgets_RandomItems', '%s' % __addon__.getSetting("randomitems_enable"))
        self.WINDOW.setProperty('SkinWidgets_RecentItems', '%s' % __addon__.getSetting("recentitems_enable"))
        self.WINDOW.setProperty('SkinWidgets_RandomItems_Update', 'false')
        self.RANDOMITEMS_UPDATE_METHOD = int(__addon__.getSetting("randomitems_method"))
        self.RECENTITEMS_HOME_UPDATE = __addon__.getSetting("recentitems_homeupdate")
        self.PLOT_ENABLE = __addon__.getSetting("plot_enable")  == 'true'
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
        a = datetime.datetime.now()
        if __addon__.getSetting("recommended_enable") == 'true':
            self._fetch_movies('RecommendedMovie')
            self._fetch_tvshows_recommended('RecommendedEpisode')
            self._fetch_albums('RecommendedAlbum')
            self._fetch_musicvideo('RecommendedMusicVideo')
            b = datetime.datetime.now()
            c = b - a
            log('Total time needed to request recommended queries: %s' % c)

    def _fetch_info_randomitems(self):
        a = datetime.datetime.now()
        if __addon__.getSetting("randomitems_enable") == 'true':
            self.RANDOMITEMS_UNPLAYED = __addon__.getSetting("randomitems_unplayed") == 'true'
            self._fetch_movies('RandomMovie')
            self._fetch_tvshows('RandomEpisode')
            self._fetch_musicvideo('RandomMusicVideo')
            self._fetch_albums('RandomAlbum')
            self._fetch_artist('RandomArtist')
            self._fetch_song('RandomSong')
            self._fetch_addon('RandomAddon')
            b = datetime.datetime.now()
            c = b - a
            log('Total time needed to request random queries: %s' % c)

    def _fetch_info_recentitems(self):
        a = datetime.datetime.now()
        if __addon__.getSetting("recentitems_enable") == 'true':
            self.RECENTITEMS_UNPLAYED = __addon__.getSetting("recentitems_unplayed") == 'true'
            self._fetch_movies('RecentMovie')
            self._fetch_tvshows('RecentEpisode')
            self._fetch_musicvideo('RecentMusicVideo')
            self._fetch_albums('RecentAlbum')
            b = datetime.datetime.now()
            c = b - a
            log('Total time needed to request recent items queries: %s' % c)
            
    def _fetch_movies(self, request):
        if not xbmc.abortRequested:
            json_query = REQ.movies(request)
            if json_query:
                self._clear_properties(request)
                count = 0
                for item in json_query['result']['movies']:
                    count += 1
                    if (item['resume']['position'] and item['resume']['total'])> 0:
                        resume = "true"
                        played = '%s%%'%int((float(item['resume']['position']) / float(item['resume']['total'])) * 100)
                    else:
                        resume = "false"
                        played = '0%'
                    if item['playcount'] >= 1:
                        watched = "true"
                    else:
                        watched = "false"
                    if not self.PLOT_ENABLE and watched == "false":
                        plot = __localize__(32014)
                    else:
                        plot = item['plot']
                    art = item['art']
                    path = media_path(item['file'])
                    play = 'XBMC.RunScript(' + __addonid__ + ',movieid=' + str(item.get('movieid')) + ')'
                    streaminfo = media_streamdetails(item['file'].encode('utf-8').lower(),
                                               item['streamdetails'])
                    self.WINDOW.setProperty("%s.%d.DBID"            % (request, count), str(item.get('movieid')))
                    self.WINDOW.setProperty("%s.%d.Title"           % (request, count), item['title'])
                    self.WINDOW.setProperty("%s.%d.OriginalTitle"   % (request, count), item['originaltitle'])
                    self.WINDOW.setProperty("%s.%d.Year"            % (request, count), str(item['year']))
                    self.WINDOW.setProperty("%s.%d.Genre"           % (request, count), " / ".join(item['genre']))
                    self.WINDOW.setProperty("%s.%d.Studio"          % (request, count), item['studio'][0])
                    self.WINDOW.setProperty("%s.%d.Country"         % (request, count), item['country'][0])
                    self.WINDOW.setProperty("%s.%d.Plot"            % (request, count), plot)
                    self.WINDOW.setProperty("%s.%d.PlotOutline"     % (request, count), item['plotoutline'])
                    self.WINDOW.setProperty("%s.%d.Tagline"         % (request, count), item['tagline'])
                    self.WINDOW.setProperty("%s.%d.Runtime"         % (request, count), str(int((item['runtime'] / 60) + 0.5)))
                    self.WINDOW.setProperty("%s.%d.Rating"          % (request, count), str(round(float(item['rating']),1)))
                    self.WINDOW.setProperty("%s.%d.mpaa"            % (request, count), item['mpaa'])
                    self.WINDOW.setProperty("%s.%d.Director"        % (request, count), " / ".join(item['director']))
                    self.WINDOW.setProperty("%s.%d.Trailer"         % (request, count), item['trailer'])
                    self.WINDOW.setProperty("%s.%d.Art(poster)"     % (request, count), art.get('poster',''))
                    self.WINDOW.setProperty("%s.%d.Art(fanart)"     % (request, count), art.get('fanart',''))
                    self.WINDOW.setProperty("%s.%d.Art(clearlogo)"  % (request, count), art.get('clearlogo',''))
                    self.WINDOW.setProperty("%s.%d.Art(clearart)"   % (request, count), art.get('clearart',''))
                    self.WINDOW.setProperty("%s.%d.Art(landscape)"  % (request, count), art.get('landscape',''))
                    self.WINDOW.setProperty("%s.%d.Art(banner)"     % (request, count), art.get('banner',''))
                    self.WINDOW.setProperty("%s.%d.Art(discart)"    % (request, count), art.get('discart',''))                
                    self.WINDOW.setProperty("%s.%d.Resume"          % (request, count), resume)
                    self.WINDOW.setProperty("%s.%d.PercentPlayed"   % (request, count), played)
                    self.WINDOW.setProperty("%s.%d.Watched"         % (request, count), watched)
                    self.WINDOW.setProperty("%s.%d.File"            % (request, count), item['file'])
                    self.WINDOW.setProperty("%s.%d.Path"            % (request, count), path)
                    self.WINDOW.setProperty("%s.%d.Play"            % (request, count), play)
                    self.WINDOW.setProperty("%s.%d.VideoCodec"      % (request, count), streaminfo['videocodec'])
                    self.WINDOW.setProperty("%s.%d.VideoResolution" % (request, count), streaminfo['videoresolution'])
                    self.WINDOW.setProperty("%s.%d.VideoAspect"     % (request, count), streaminfo['videoaspect'])
                    self.WINDOW.setProperty("%s.%d.AudioCodec"      % (request, count), streaminfo['audiocodec'])
                    self.WINDOW.setProperty("%s.%d.AudioChannels"   % (request, count), str(streaminfo['audiochannels']))
            del json_query

    def _fetch_tvshows_recommended(self, request):
        if not xbmc.abortRequested:
            json_query = REQ.tvshows_recommended(request)
            if json_query:
                self._clear_properties(request)
                count = 0
                for item in json_query['result']['tvshows']:
                    if xbmc.abortRequested:
                        break
                    count += 1
                    json_query2 = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params": {"tvshowid": %d, "properties": ["title", "playcount", "plot", "season", "episode", "showtitle", "file", "lastplayed", "rating", "resume", "art", "streamdetails", "firstaired", "runtime"], "sort": {"method": "episode"}, "filter": {"field": "playcount", "operator": "is", "value": "0"}, "limits": {"end": 1}}, "id": 1}' %item['tvshowid'])
                    json_query2 = unicode(json_query2, 'utf-8', errors='ignore')
                    json_query2 = simplejson.loads(json_query2)
                    if json_query2.has_key('result') and json_query2['result'] != None and json_query2['result'].has_key('episodes'):
                        for item2 in json_query2['result']['episodes']:
                            episode = ("%.2d" % float(item2['episode']))
                            season = "%.2d" % float(item2['season'])
                            rating = str(round(float(item2['rating']),1))
                            episodeno = "s%se%s" %(season,episode)
                            art2 = item2['art']
                    #seasonthumb = ''
                    if (item2['resume']['position'] and item2['resume']['total']) > 0:
                        resume = "true"
                        played = '%s%%'%int((float(item2['resume']['position']) / float(item2['resume']['total'])) * 100)
                    else:
                        resume = "false"
                        played = '0%'
                    if item2['playcount'] >= 1:
                        watched = "true"
                    else:
                        watched = "false"
                    if not self.PLOT_ENABLE and watched == "false":
                        plot = __localize__(32014)
                    else:
                        plot = item2['plot']
                    art = item['art']
                    path = media_path(item['file'])
                    play = 'XBMC.RunScript(' + __addonid__ + ',episodeid=' + str(item2.get('episodeid')) + ')'
                    streaminfo = media_streamdetails(item['file'].encode('utf-8').lower(),
                                                     item2['streamdetails'])
                    self.WINDOW.setProperty("%s.%d.DBID"                % (request, count), str(item2.get('episodeid')))
                    self.WINDOW.setProperty("%s.%d.Title"               % (request, count), item2['title'])
                    self.WINDOW.setProperty("%s.%d.Episode"             % (request, count), episode)
                    self.WINDOW.setProperty("%s.%d.EpisodeNo"           % (request, count), episodeno)
                    self.WINDOW.setProperty("%s.%d.Season"              % (request, count), season)
                    self.WINDOW.setProperty("%s.%d.Plot"                % (request, count), plot)
                    self.WINDOW.setProperty("%s.%d.TVshowTitle"         % (request, count), item2['showtitle'])
                    self.WINDOW.setProperty("%s.%d.Rating"              % (request, count), rating)
                    self.WINDOW.setProperty("%s.%d.Runtime"             % (request, count), str(int((item2['runtime'] / 60) + 0.5)))
                    self.WINDOW.setProperty("%s.%d.Premiered"           % (request, count), item2['firstaired'])
                    self.WINDOW.setProperty("%s.%d.Art(thumb)"          % (request, count), art2.get('thumb',''))
                    self.WINDOW.setProperty("%s.%d.Art(tvshow.fanart)"  % (request, count), art2.get('tvshow.fanart',''))
                    self.WINDOW.setProperty("%s.%d.Art(tvshow.poster)"  % (request, count), art2.get('tvshow.poster',''))
                    self.WINDOW.setProperty("%s.%d.Art(tvshow.banner)"  % (request, count), art2.get('tvshow.banner',''))
                    self.WINDOW.setProperty("%s.%d.Art(tvshow.clearlogo)"% (request, count), art2.get('tvshow.clearlogo',''))
                    self.WINDOW.setProperty("%s.%d.Art(tvshow.clearart)" % (request, count), art2.get('tvshow.clearart',''))
                    self.WINDOW.setProperty("%s.%d.Art(tvshow.landscape)"% (request, count), art2.get('tvshow.landscape',''))
                    self.WINDOW.setProperty("%s.%d.Art(tvshow.characterart)"% (request, count), art2.get('tvshow.characterart',''))
                    #self.WINDOW.setProperty("%s.%d.Art(season.poster)" % (request, count), seasonthumb)
                    self.WINDOW.setProperty("%s.%d.Studio"              % (request, count), item['studio'][0])
                    self.WINDOW.setProperty("%s.%d.mpaa"                % (request, count), item['mpaa'])
                    self.WINDOW.setProperty("%s.%d.Resume"              % (request, count), resume)
                    self.WINDOW.setProperty("%s.%d.PercentPlayed"       % (request, count), played)
                    self.WINDOW.setProperty("%s.%d.Watched"             % (request, count), watched)
                    self.WINDOW.setProperty("%s.%d.File"                % (request, count), item2['file'])
                    self.WINDOW.setProperty("%s.%d.Path"                % (request, count), path)
                    self.WINDOW.setProperty("%s.%d.Play"                % (request, count), play)
                    self.WINDOW.setProperty("%s.%d.VideoCodec"          % (request, count), streaminfo['videocodec'])
                    self.WINDOW.setProperty("%s.%d.VideoResolution"     % (request, count), streaminfo['videoresolution'])
                    self.WINDOW.setProperty("%s.%d.VideoAspect"         % (request, count), streaminfo['videoaspect'])
                    self.WINDOW.setProperty("%s.%d.AudioCodec"          % (request, count), streaminfo['audiocodec'])
                    self.WINDOW.setProperty("%s.%d.AudioChannels"       % (request, count), str(streaminfo['audiochannels']))
            del json_query

    def _fetch_tvshows(self, request):
        if not xbmc.abortRequested:
            json_query = REQ.tvshows(request)
            if json_query:
                season_folders = __addon__.getSetting("randomitems_seasonfolders")
                self._clear_properties(request)
                count = 0
                for item in json_query['result']['episodes']:
                    count += 1
                    '''
                    # This part is commented out because it takes 1.5second extra on my system to request these which doubles the total time.
                    # Hence the ugly path hack that will require users to have season folders.
                    json_query2 = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShowDetails", "params": {"properties": ["file", "studio"], "tvshowid":%s}, "id": 1}' %item['tvshowid'])
                    json_query2 = unicode(json_query2, 'utf-8', errors='ignore')
                    json_query2 = simplejson.loads(json_query2)
                    path = json_query2['result']['tvshowdetails']['file']
                    studio = json_query2['result']['tvshowdetails']['studio'][0]
                    '''
                    if season_folders == 'true':
                        path = os.path.split(media_path(item['file']))[0]
                    else:
                        path = media_path(item['file'])
                    episode = ("%.2d" % float(item['episode']))
                    season = "%.2d" % float(item['season'])
                    episodeno = "s%se%s" %(season,episode)
                    #seasonthumb = ''
                    rating = str(round(float(item['rating']),1))
                    if (item['resume']['position'] and item['resume']['total']) > 0:
                        resume = "true"
                        played = '%s%%'%int((float(item['resume']['position']) / float(item['resume']['total'])) * 100)
                    else:
                        resume = "false"
                        played = '0%'
                    if item['playcount'] >= 1:
                        watched = "true"
                    else:
                        watched = "false"
                    if not self.PLOT_ENABLE and watched == "false":
                        plot = __localize__(32014)
                    else:
                        plot = item['plot']
                    art = item['art']
                    path = media_path(item['file'])
                    play = 'XBMC.RunScript(' + __addonid__ + ',episodeid=' + str(item.get('episodeid')) + ')'
                    streaminfo = media_streamdetails(item['file'].encode('utf-8').lower(),
                                                     item['streamdetails'])
                    self.WINDOW.setProperty("%s.%d.DBID"                % (request, count), str(item.get('episodeid')))
                    self.WINDOW.setProperty("%s.%d.Title"               % (request, count), item['title'])
                    self.WINDOW.setProperty("%s.%d.Episode"             % (request, count), episode)
                    self.WINDOW.setProperty("%s.%d.EpisodeNo"           % (request, count), episodeno)
                    self.WINDOW.setProperty("%s.%d.Season"              % (request, count), season)
                    self.WINDOW.setProperty("%s.%d.Plot"                % (request, count), plot)
                    self.WINDOW.setProperty("%s.%d.TVshowTitle"         % (request, count), item['showtitle'])
                    self.WINDOW.setProperty("%s.%d.Rating"              % (request, count), rating)
                    self.WINDOW.setProperty("%s.%d.Runtime"             % (request, count), str(int((item['runtime'] / 60) + 0.5)))
                    self.WINDOW.setProperty("%s.%d.Premiered"           % (request, count), item['firstaired'])
                    self.WINDOW.setProperty("%s.%d.Art(thumb)"          % (request, count), art.get('thumb',''))
                    self.WINDOW.setProperty("%s.%d.Art(tvshow.fanart)"  % (request, count), art.get('tvshow.fanart',''))
                    self.WINDOW.setProperty("%s.%d.Art(tvshow.poster)"  % (request, count), art.get('tvshow.poster',''))
                    self.WINDOW.setProperty("%s.%d.Art(tvshow.banner)"  % (request, count), art.get('tvshow.banner',''))
                    self.WINDOW.setProperty("%s.%d.Art(tvshow.clearlogo)"% (request, count), art.get('tvshow.clearlogo',''))
                    self.WINDOW.setProperty("%s.%d.Art(tvshow.clearart)" % (request, count), art.get('tvshow.clearart',''))
                    self.WINDOW.setProperty("%s.%d.Art(tvshow.landscape)"% (request, count), art.get('tvshow.landscape',''))
                    self.WINDOW.setProperty("%s.%d.Art(tvshow.characterart)"% (request, count), art.get('tvshow.characterart',''))
                    self.WINDOW.setProperty("%s.%d.Resume"              % (request, count), resume)
                    self.WINDOW.setProperty("%s.%d.PercentPlayed"       % (request, count), played)
                    self.WINDOW.setProperty("%s.%d.Watched"             % (request, count), watched)
                    self.WINDOW.setProperty("%s.%d.File"                % (request, count), item['file'])
                    self.WINDOW.setProperty("%s.%d.Path"                % (request, count), path)
                    self.WINDOW.setProperty("%s.%d.Play"                % (request, count), play)
                    self.WINDOW.setProperty("%s.%d.VideoCodec"          % (request, count), streaminfo['videocodec'])
                    self.WINDOW.setProperty("%s.%d.VideoResolution"     % (request, count), streaminfo['videoresolution'])
                    self.WINDOW.setProperty("%s.%d.VideoAspect"         % (request, count), streaminfo['videoaspect'])
                    self.WINDOW.setProperty("%s.%d.AudioCodec"          % (request, count), streaminfo['audiocodec'])
                    self.WINDOW.setProperty("%s.%d.AudioChannels"       % (request, count), str(streaminfo['audiochannels']))
            del json_query

    def _fetch_musicvideo(self, request):
        if not xbmc.abortRequested:
            json_query = REQ.musicvideos(request)
            if json_query:
                self._clear_properties(request)        
                count = 0
                for item in json_query['result']['musicvideos']:
                    count += 1
                    if (item['resume']['position'] and item['resume']['total'])> 0:
                        resume = "true"
                        played = '%s%%'%int((float(item['resume']['position']) / float(item['resume']['total'])) * 100)
                    else:
                        resume = "false"
                        played = '0%'
                    if item['playcount'] >= 1:
                        watched = "true"
                    else:
                        watched = "false"
                    play = 'XBMC.RunScript(' + __addonid__ + ',musicvideoid=' + str(item.get('musicvideoid')) + ')'
                    path = media_path(item['file'])
                    streaminfo = media_streamdetails(item['file'].encode('utf-8').lower(),
                                                     item['streamdetails'])
                    self.WINDOW.setProperty("%s.%d.DBID"           % (request, count), str(item.get('musicvideoid')))
                    self.WINDOW.setProperty("%s.%d.Title"           % (request, count), item['title'])
                    self.WINDOW.setProperty("%s.%d.Artist"          % (request, count), " / ".join(item['artist']))
                    self.WINDOW.setProperty("%s.%d.Year"            % (request, count), str(item['year']))
                    self.WINDOW.setProperty("%s.%d.Plot"            % (request, count), item['plot'])
                    self.WINDOW.setProperty("%s.%d.Genre"           % (request, count), " / ".join(item['genre']))
                    self.WINDOW.setProperty("%s.%d.Runtime"         % (request, count), str(int((item['runtime'] / 60) + 0.5)))
                    self.WINDOW.setProperty("%s.%d.Thumb"           % (request, count), item['thumbnail']) #remove
                    self.WINDOW.setProperty("%s.%d.Fanart"          % (request, count), item['fanart']) #remove
                    self.WINDOW.setProperty("%s.%d.Art(thumb)"      % (request, count), item['thumbnail'])
                    self.WINDOW.setProperty("%s.%d.Art(fanart)"     % (request, count), item['fanart'])
                    self.WINDOW.setProperty("%s.%d.File"            % (request, count), item['file'])
                    self.WINDOW.setProperty("%s.%d.Path"            % (request, count), path)
                    self.WINDOW.setProperty("%s.%d.Resume"          % (request, count), resume)
                    self.WINDOW.setProperty("%s.%d.PercentPlayed"   % (request, count), played)
                    self.WINDOW.setProperty("%s.%d.Watched"         % (request, count), watched)
                    self.WINDOW.setProperty("%s.%d.Play"            % (request, count), play)
                    self.WINDOW.setProperty("%s.%d.VideoCodec"      % (request, count), streaminfo['videocodec'])
                    self.WINDOW.setProperty("%s.%d.VideoResolution" % (request, count), streaminfo['videoresolution'])
                    self.WINDOW.setProperty("%s.%d.VideoAspect"     % (request, count), streaminfo['videoaspect'])
                    self.WINDOW.setProperty("%s.%d.AudioCodec"      % (request, count), streaminfo['audiocodec'])
                    self.WINDOW.setProperty("%s.%d.AudioChannels"   % (request, count), str(streaminfo['audiochannels']))
            del json_query

    def _fetch_albums(self, request):
        if not xbmc.abortRequested:
            json_query = REQ.albums(request)
            if json_query:
                self._clear_properties(request)
                count = 0
                for item in json_query['result']['albums']:
                    count += 1
                    rating = str(item['rating'])
                    if rating == '48':
                        rating = ''
                    play = 'XBMC.RunScript(' + __addonid__ + ',albumid=' + str(item.get('albumid')) + ')'
                    self.WINDOW.setProperty("%s.%d.Title"       % (request, count), item['title'])
                    self.WINDOW.setProperty("%s.%d.Label"       % (request, count), item['title']) #needs to be removed
                    self.WINDOW.setProperty("%s.%d.Artist"      % (request, count), " / ".join(item['artist']))
                    self.WINDOW.setProperty("%s.%d.Genre"       % (request, count), " / ".join(item['genre']))
                    self.WINDOW.setProperty("%s.%d.Theme"       % (request, count), " / ".join(item['theme']))
                    self.WINDOW.setProperty("%s.%d.Mood"        % (request, count), " / ".join(item['mood']))
                    self.WINDOW.setProperty("%s.%d.Style"       % (request, count), " / ".join(item['style']))
                    self.WINDOW.setProperty("%s.%d.Type"        % (request, count), " / ".join(item['type']))
                    self.WINDOW.setProperty("%s.%d.Year"        % (request, count), str(item['year']))
                    self.WINDOW.setProperty("%s.%d.RecordLabel" % (request, count), item['albumlabel'])
                    self.WINDOW.setProperty("%s.%d.Description" % (request, count), item['description'])
                    self.WINDOW.setProperty("%s.%d.Rating"      % (request, count), rating)
                    self.WINDOW.setProperty("%s.%d.Thumb"       % (request, count), item['thumbnail']) #remove
                    self.WINDOW.setProperty("%s.%d.Fanart"      % (request, count), item['fanart']) #remove
                    self.WINDOW.setProperty("%s.%d.Art(thumb)"  % (request, count), item['thumbnail'])
                    self.WINDOW.setProperty("%s.%d.Art(fanart)" % (request, count), item['fanart'])
                    self.WINDOW.setProperty("%s.%d.Play"        % (request, count), play)
            del json_query

    def _fetch_artist(self, request):
        if not xbmc.abortRequested:
            json_query = REQ.artist(request)
            if json_query:
                self._clear_properties(request)
                count = 0
                for item in json_query['result']['artists']:
                    count += 1
                    path = 'musicdb://2/' + str(item['artistid']) + '/'
                    self.WINDOW.setProperty("%s.%d.Title"       % (request, count), item['label'])
                    self.WINDOW.setProperty("%s.%d.Genre"       % (request, count), " / ".join(item['genre']))
                    self.WINDOW.setProperty("%s.%d.Thumb"       % (request, count), item['thumbnail']) #remove
                    self.WINDOW.setProperty("%s.%d.Fanart"      % (request, count), item['fanart']) #remove
                    self.WINDOW.setProperty("%s.%d.Art(thumb)"  % (request, count), item['thumbnail'])
                    self.WINDOW.setProperty("%s.%d.Art(fanart)" % (request, count), item['fanart'])
                    self.WINDOW.setProperty("%s.%d.Description" % (request, count), item['description'])
                    self.WINDOW.setProperty("%s.%d.Born"        % (request, count), item['born'])
                    self.WINDOW.setProperty("%s.%d.Died"        % (request, count), item['died'])
                    self.WINDOW.setProperty("%s.%d.Formed"      % (request, count), item['formed'])
                    self.WINDOW.setProperty("%s.%d.Disbanded"   % (request, count), item['disbanded'])
                    self.WINDOW.setProperty("%s.%d.YearsActive" % (request, count), " / ".join(item['yearsactive']))
                    self.WINDOW.setProperty("%s.%d.Style"       % (request, count), " / ".join(item['style']))
                    self.WINDOW.setProperty("%s.%d.Mood"        % (request, count), " / ".join(item['mood']))
                    self.WINDOW.setProperty("%s.%d.Instrument"  % (request, count), " / ".join(item['instrument']))
                    self.WINDOW.setProperty("%s.%d.LibraryPath" % (request, count), path)

    def _fetch_song(self, request):
        if not xbmc.abortRequested:
            json_query = REQ.songs(request)
            if json_query:
                self._clear_properties(request)
                count = 0
                for item in json_query['result']['songs']:
                    count += 1
                    play = 'XBMC.RunScript(' + __addonid__ + ',songid=' + str(item.get('songid')) + ')'
                    path = media_path(item['file'])
                    self.WINDOW.setProperty("%s.%d.Title"       % (request, count), item['title'])
                    self.WINDOW.setProperty("%s.%d.Artist"      % (request, count), " / ".join(item['artist']))
                    self.WINDOW.setProperty("%s.%d.Year"        % (request, count), str(item['year']))
                    self.WINDOW.setProperty("%s.%d.Rating"      % (request, count), str(int(item['rating'])-48))
                    self.WINDOW.setProperty("%s.%d.Album"       % (request, count), item['album'])
                    self.WINDOW.setProperty("%s.%d.Thumb"       % (request, count), item['thumbnail']) #remove
                    self.WINDOW.setProperty("%s.%d.Fanart"      % (request, count), item['fanart']) #remove
                    self.WINDOW.setProperty("%s.%d.Art(thumb)"  % (request, count), item['thumbnail'])
                    self.WINDOW.setProperty("%s.%d.Art(fanart)" % (request, count), item['fanart'])
                    self.WINDOW.setProperty("%s.%d.File"        % (request, count), item['file'])
                    self.WINDOW.setProperty("%s.%d.Path"        % (request, count), path)
                    self.WINDOW.setProperty("%s.%d.Play"        % (request, count), play)
            del json_query

    def _fetch_addon(self, request):
        if not xbmc.abortRequested:
            json_query = REQ.addons(request)
            if json_query:
                # find plugins and scripts
                addonlist = []
                for item in json_query['result']['addons']:
                    if item['type'] == 'xbmc.python.script' or item['type'] == 'xbmc.python.pluginsource':
                        addonlist.append(item)
                # randomize the list
                random.shuffle(addonlist)
                self._clear_properties(request)
                count = 0
                for item in addonlist:
                    count += 1
                    self.WINDOW.setProperty("%s.%d.Title"       % (request, count), item['name'])
                    self.WINDOW.setProperty("%s.%d.Author"      % (request, count), item['author'])
                    self.WINDOW.setProperty("%s.%d.Summary"     % (request, count), item['summary'])
                    self.WINDOW.setProperty("%s.%d.Version"     % (request, count), item['version'])
                    self.WINDOW.setProperty("%s.%d.Path"        % (request, count), item['addonid'])
                    self.WINDOW.setProperty("%s.%d.Thumb"       % (request, count), item['thumbnail']) #remove
                    self.WINDOW.setProperty("%s.%d.Fanart"      % (request, count), item['fanart']) #remove
                    self.WINDOW.setProperty("%s.%d.Art(thumb)"  % (request, count), item['thumbnail'])
                    self.WINDOW.setProperty("%s.%d.Art(fanart)" % (request, count), item['fanart'])
                    self.WINDOW.setProperty("%s.%d.Type"        % (request, count), item['type'])
                    # stop if we've reached the number of items we need
                    if count == self.LIMIT:
                        break
                self.WINDOW.setProperty("%s.Count" % (request), str(json_query['result']['limits']['total']))
            del json_query

    def _daemon(self):
        # deamon is meant to keep script running at all time
        count = 0
        home_update = False
        while (not xbmc.abortRequested) and self.WINDOW.getProperty('SkinWidgets_Running') == 'true':
            xbmc.sleep(500)
            if not xbmc.Player().isPlayingVideo():
                if self.RANDOMITEMS_UPDATE_METHOD == 0:
                    count += 1
                    if count == self.RANDOMITEMS_TIME:
                        self._fetch_info_randomitems()
                        count = 0    # reset counter
                if self.WINDOW.getProperty('SkinWidgets_RandomItems_Update') == 'true':
                    count = 0
                    self.WINDOW.setProperty('SkinWidgets_RandomItems_Update','false')
                    self._fetch_info_randomitems()
                if  self.RECENTITEMS_HOME_UPDATE == 'true' and home_update and xbmcgui.getCurrentWindowId() == 10000:
                    self._fetch_info_recentitems()
                    home_update = False
                elif self.RECENTITEMS_HOME_UPDATE == 'true' and not home_update and xbmcgui.getCurrentWindowId() != 10000:
                    home_update = True

    def _clear_properties(self, request):
        count = 0
        for count in range(int(self.LIMIT)):
            count += 1
            self.WINDOW.clearProperty("%s.%d.Title" % (request, count))

    def _update(self, type):
        xbmc.sleep(1000)
        if type == 'movie':
            self._fetch_movies('RecommendedMovie')
            self._fetch_movies('RecentMovie')
        elif type == 'episode':
            self._fetch_tvshows_recommended('RecommendedEpisode')
            self._fetch_tvshows('RecentEpisode')
        elif type == 'video':
            #only on db update
            self._fetch_movies('RecommendedMovie')
            self._fetch_tvshows_recommended('RecommendedEpisode')
            self._fetch_movies('RecentMovie')
            self._fetch_tvshows('RecentEpisode')
            self._fetch_musicvideo('RecentMusicVideo')
        elif type == 'music':
            self._fetch_albums('RecommendedAlbum')
            self._fetch_albums('RecentAlbum')
        if self.RANDOMITEMS_UPDATE_METHOD == 1:
            # update random if db update is selected instead of timer
            if type == 'video':
                self._fetch_movies('RandomMovie')
                self._fetch_tvshows('RandomEpisode')
                self._fetch_musicvideo('RandomMusicVideo')
            elif type == 'music':
                self._fetch_albums('RandomAlbum')
                self._fetch_artist('RandomArtist')
                self._fetch_song('RandomSong')
                self._fetch_addon('RandomAddon')

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
