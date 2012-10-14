#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2012 Team-XBMC
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
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

if sys.version_info < (2, 7):
    import simplejson
else:
    import json as simplejson

__addon__        = xbmcaddon.Addon()
__addonversion__ = __addon__.getAddonInfo('version')
__addonid__      = __addon__.getAddonInfo('id')
__addonname__    = __addon__.getAddonInfo('name')

def log(txt):
    message = '%s: %s' % (__addonname__, txt.encode('ascii', 'ignore'))
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)

class Main:
    def __init__(self):
        self._parse_argv()
        self._init_vars()
        self._init_property()
        # check how we were executed
        if self.ALBUMID:
            xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Player.Open", "params": { "item": { "albumid": %d } }, "id": 1 }' % int(self.ALBUMID))
        else:
            # clear our property, if another instance is already running it should stop now
            self.WINDOW.clearProperty('SkinWidgets_Running')
            a_total = datetime.datetime.now()
            self._fetch_info_randomitems()
            self._fetch_info_recommended()
            b_total = datetime.datetime.now()
            c_total = b_total - a_total
            log('Total time needed for all queries: %s' % c_total)
            # give a possible other instance some time to notice the empty property
            self.WINDOW.setProperty('SkinWidgets_Running', 'true')
            self._daemon()

    def _init_vars(self):
        self.WINDOW = xbmcgui.Window(10000)
        self.Player = MyPlayer(action = self._update)
        self.Monitor = MyMonitor(update_listitems = self._update, update_settings = self._init_property)
        self.LIMIT = 20

    def _init_property(self):
        self.WINDOW.setProperty('SkinWidgets_Recommended', '%s' % __addon__.getSetting("recommended_enable"))
        self.WINDOW.setProperty('SkinWidgets_RandomItems', '%s' % __addon__.getSetting("randomitems_enable"))
        self.RANDOMITEMS_UPDATE_METHOD = int(__addon__.getSetting("randomitems_method"))
        # convert time to seconds, times 2 for 0,5 second sleep compensation
        self.RANDOMITEMS_TIME = int(__addon__.getSetting("randomitems_time").rstrip('0').rstrip('.')) * 60 * 2

    def _parse_argv( self ):
        try:
            params = dict( arg.split( "=" ) for arg in sys.argv[ 1 ].split( "&" ) )
        except:
            params = {}
        self.ALBUMID = params.get( "albumid", "" )

    def _fetch_info_recommended(self):
        a = datetime.datetime.now()
        '''
        clear = ['recommendedMovie',
                 'recommendedEpisode',
                 'recommendedMusicVideo',
                 'recommendedAlbum']
        for item in clear:
            self._clear_properties(item)
        '''
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
        '''
        clear = ['RandomMovie',
                 'RandomEpisode',
                 'RandomMusicVideo',
                 'RandomAlbum',
                 'RandomArtist',
                 'RandomSong',
                 'RandomAddon']
        for item in clear:
            self._clear_properties(item)
        '''
        self.RANDOMITEMS_UNPLAYED = __addon__.getSetting("randomitems_unplayed") == 'true'
        if __addon__.getSetting("randomitems_enable") == 'true':
            self._fetch_movies('RandomMovie')
            self._fetch_tvshows_randomitems('RandomEpisode')
            self._fetch_musicvideo('RandomMusicVideo')
            self._fetch_albums('RandomAlbum')
            self._fetch_artist('RandomArtist')
            self._fetch_song('RandomSong')
            self._fetch_addon('RandomAddon')
            b = datetime.datetime.now()
            c = b - a
            log('Total time needed to request random queries: %s' % c)
           
    def _fetch_movies(self, request):
        if request == 'RecommendedMovie':
            json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": {"properties": ["title", "playcount", "year", "genre", "studio", "tagline", "plot", "runtime", "fanart", "thumbnail", "file", "plotoutline", "lastplayed", "trailer", "rating", "resume"], "sort": {"order": "descending", "method": "lastplayed"}, "limits": {"end": %d}, "filter": {"field": "inprogress", "operator": "true", "value": ""}}, "id": 1}' %self.LIMIT)
        elif self.RANDOMITEMS_UNPLAYED:
            json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": {"properties": ["title", "playcount", "year", "genre", "studio", "tagline", "plot", "runtime", "fanart", "thumbnail", "file", "plotoutline", "lastplayed", "trailer", "rating", "resume"], "sort": {"method": "random" }, "limits": {"end": %d} }, "filter": {"field": "playcount", "operator": "lessthan", "value": "1"}, "id": 1}' %self.LIMIT)
        else:
            json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": {"properties": ["title", "playcount", "year", "genre", "studio", "tagline", "plot", "runtime", "fanart", "thumbnail", "file", "plotoutline", "lastplayed", "trailer", "rating", "resume"], "sort": {"method": "random" }, "limits": {"end": %d} }, "id": 1}' %self.LIMIT)
        json_query = unicode(json_query, 'utf-8', errors='ignore')
        json_response = simplejson.loads(json_query)
        if json_response['result'].has_key('movies'):
            self._clear_properties(request)
            count = 0
            for item in json_response['result']['movies']:
                count += 1
                if item['resume']['position'] > 0:
                    resume = "true"
                    percentage = '%s%%'%int((float(item['resume']['position']) / float(item['resume']['total'])) * 100)
                else:
                    resume = "false"
                    percentage = '0%'
                path = media_path(item['file'])
                self.WINDOW.setProperty("%s.%d.Title"       % (request, count), item['title'])
                self.WINDOW.setProperty("%s.%d.Year"        % (request, count), str(item['year']))
                self.WINDOW.setProperty("%s.%d.Genre"       % (request, count), " / ".join(item['genre']))
                self.WINDOW.setProperty("%s.%d.Studio"      % (request, count), item['studio'][0])
                self.WINDOW.setProperty("%s.%d.Plot"        % (request, count), item['plot'])
                self.WINDOW.setProperty("%s.%d.PlotOutline" % (request, count), item['plotoutline'])
                self.WINDOW.setProperty("%s.%d.Tagline"     % (request, count), item['tagline'])
                self.WINDOW.setProperty("%s.%d.Runtime"     % (request, count), item['runtime'])
                self.WINDOW.setProperty("%s.%d.Rating"      % (request, count), str(round(float(item['rating']),1)))
                self.WINDOW.setProperty("%s.%d.Fanart"      % (request, count), item['fanart'])
                self.WINDOW.setProperty("%s.%d.Thumb"       % (request, count), item['thumbnail'])
                self.WINDOW.setProperty("%s.%d.Logo"        % (request, count), xbmc.validatePath(os.path.join(path, 'logo.png')))
                self.WINDOW.setProperty("%s.%d.Landscape"   % (request, count), xbmc.validatePath(os.path.join(path, 'landscape.png')))
                self.WINDOW.setProperty("%s.%d.Banner"      % (request, count), xbmc.validatePath(os.path.join(path, 'banner.png')))
                self.WINDOW.setProperty("%s.%d.Disc"        % (request, count), xbmc.validatePath(os.path.join(path, 'disc.png')))
                self.WINDOW.setProperty("%s.%d.Resume"      % (request, count), resume)
                self.WINDOW.setProperty("%s.%d.Percentage"  % (request, count), percentage)
                self.WINDOW.setProperty("%s.%d.File"        % (request, count), item['file'])
                self.WINDOW.setProperty("%s.%d.Path"        % (request, count), path)

    def _fetch_tvshows_recommended(self, request):
        json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows", "params": {"properties": ["title", "studio", "thumbnail", "file"], "sort": {"order": "descending", "method": "lastplayed"}, "filter": {"field": "inprogress", "operator": "true", "value": ""}, "limits": {"end": %d}}, "id": 1}' %self.LIMIT)
        json_query = unicode(json_query, 'utf-8', errors='ignore')
        json_response = simplejson.loads(json_query)
        if json_response['result'].has_key('tvshows'):
            self._clear_properties(request)
            count = 0
            for item in json_response['result']['tvshows']:
                count += 1
                json_query2 = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params": {"tvshowid": %d, "properties": ["title", "playcount", "plot", "season", "episode", "showtitle", "thumbnail", "fanart", "file", "lastplayed", "rating", "resume"], "sort": {"method": "episode"}, "filter": {"field": "playcount", "operator": "is", "value": "0"}, "limits": {"end": 1}}, "id": 1}' %item['tvshowid'])
                json_query2 = unicode(json_query2, 'utf-8', errors='ignore')
                json_response2 = simplejson.loads(json_query2)
                if json_response2.has_key('result') and json_response2['result'] != None and json_response2['result'].has_key('episodes'):
                    for item2 in json_response2['result']['episodes']:
                        episode = ("%.2d" % float(item2['episode']))
                        season = "%.2d" % float(item2['season'])
                        rating = str(round(float(item2['rating']),1))
                        episodeno = "s%se%s" %(season,episode)
                seasonthumb = ''
                if item2['resume']['position'] > 0:
                    resume = "true"
                    percentage = '%s%%'%int((float(item2['resume']['position']) / float(item2['resume']['total'])) * 100)
                else:
                    resume = "false"
                    percentage = '0%'
                path = media_path(item['file'])
                self.WINDOW.setProperty("%s.%d.Title"       % (request, count), item2['title'])
                self.WINDOW.setProperty("%s.%d.Episode"     % (request, count), episode)
                self.WINDOW.setProperty("%s.%d.EpisodeNo"   % (request, count), episodeno)
                self.WINDOW.setProperty("%s.%d.Season"      % (request, count), season)
                self.WINDOW.setProperty("%s.%d.Plot"        % (request, count), item2['plot'])
                self.WINDOW.setProperty("%s.%d.TVshowTitle" % (request, count), item2['showtitle'])
                self.WINDOW.setProperty("%s.%d.Rating"      % (request, count), rating)
                self.WINDOW.setProperty("%s.%d.Thumb"       % (request, count), item2['thumbnail'])
                self.WINDOW.setProperty("%s.%d.Fanart"      % (request, count), item2['fanart'])
                self.WINDOW.setProperty("%s.%d.Poster"      % (request, count), xbmc.validatePath(os.path.join(path, 'poster.jpg')))
                self.WINDOW.setProperty("%s.%d.Banner"      % (request, count), xbmc.validatePath(os.path.join(path, 'banner.jpg')))
                self.WINDOW.setProperty("%s.%d.Logo"        % (request, count), xbmc.validatePath(os.path.join(path, 'logo.png')))
                self.WINDOW.setProperty("%s.%d.Clearart"    % (request, count), xbmc.validatePath(os.path.join(path, 'clearart.png')))
                self.WINDOW.setProperty("%s.%d.Studio"      % (request, count), item['studio'][0])
                self.WINDOW.setProperty("%s.%d.TvshowThumb" % (request, count), item['thumbnail'])
                self.WINDOW.setProperty("%s.%d.SeasonThumb" % (request, count), seasonthumb)
                self.WINDOW.setProperty("%s.%d.IsResumable" % (request, count), resume)
                self.WINDOW.setProperty("%s.%d.Percentage"  % (request, count), percentage)
                self.WINDOW.setProperty("%s.%d.File"        % (request, count), item2['file'])
                self.WINDOW.setProperty("%s.%d.Path"        % (request, count), path)

    def _fetch_tvshows_randomitems(self, request):
        season_folders = __addon__.getSetting("randomitems_seasonfolders")
        if self.RANDOMITEMS_UNPLAYED:
            json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params": { "properties": ["title", "playcount", "season", "episode", "showtitle", "plot", "fanart", "thumbnail", "file", "rating", "resume", "tvshowid"], "sort": {"method": "random" }, "limits": {"end": %d}, "filter": {"field": "playcount", "operator": "lessthan", "value": "1"} }, "id": 1}' %self.LIMIT)
        else:
            json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params": { "properties": ["title", "playcount", "season", "episode", "showtitle", "plot", "fanart", "thumbnail", "file", "rating", "resume", "tvshowid"], "sort": {"method": "random" }, "limits": {"end": %d} }, "id": 1}' %self.LIMIT)
        json_query = unicode(json_query, 'utf-8', errors='ignore')
        json_response = simplejson.loads(json_query)
        if json_response['result'].has_key('episodes'):
            self._clear_properties(request)
            count = 0
            for item in json_response['result']['episodes']:
                count += 1
                '''
                # This part is commented out because it takes 1.5second extra on my system to request these which doubles the total time.
                # Hence the ugly path hack that will require users to have season folders.
                json_query2 = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShowDetails", "params": {"properties": ["file", "studio"], "tvshowid":%s}, "id": 1}' %item['tvshowid'])
                json_query2 = unicode(json_query2, 'utf-8', errors='ignore')
                json_response2 = simplejson.loads(json_query2)
                path = json_response2['result']['tvshowdetails']['file']
                studio = json_response2['result']['tvshowdetails']['studio'][0]
                '''
                if season_folders == 'true':
                    path = os.path.split(media_path(item['file']))[0]
                else:
                    path = media_path(item['file'])
                episode = ("%.2d" % float(item['episode']))
                season = "%.2d" % float(item['season'])
                episodeno = "s%se%s" %(season,episode)
                seasonthumb = ''
                resumable = "True"
                rating = str(round(float(item['rating']),1))
                if item['resume']['position'] > 0:
                    resume = "true"
                    percentage = '%s%%'%int((float(item['resume']['position']) / float(item['resume']['total'])) * 100)
                else:
                    resume = "false"
                    percentage = '0%'
                self.WINDOW.setProperty("%s.%d.Title"       % (request, count), item['title'])
                self.WINDOW.setProperty("%s.%d.Episode"     % (request, count), episode)
                self.WINDOW.setProperty("%s.%d.EpisodeNo"   % (request, count), episodeno)
                self.WINDOW.setProperty("%s.%d.Season"      % (request, count), season)
                self.WINDOW.setProperty("%s.%d.Plot"        % (request, count), item['plot'])
                self.WINDOW.setProperty("%s.%d.TVshowTitle" % (request, count), item['showtitle'])
                self.WINDOW.setProperty("%s.%d.Rating"      % (request, count), rating)
                self.WINDOW.setProperty("%s.%d.Thumb"       % (request, count), item['thumbnail'])
                self.WINDOW.setProperty("%s.%d.Fanart"      % (request, count), item['fanart'])
                self.WINDOW.setProperty("%s.%d.Poster"      % (request, count), xbmc.validatePath(os.path.join(path, 'poster.jpg')))
                self.WINDOW.setProperty("%s.%d.Banner"      % (request, count), xbmc.validatePath(os.path.join(path, 'banner.jpg')))
                self.WINDOW.setProperty("%s.%d.Logo"        % (request, count), xbmc.validatePath(os.path.join(path, 'logo.png')))
                self.WINDOW.setProperty("%s.%d.Clearart"    % (request, count), xbmc.validatePath(os.path.join(path, 'clearart.png')))
                # Requires extra JSON-RPC request, see commented out part
                #self.WINDOW.setProperty("%s.%d.Studio"      % (request, count), studio)
                self.WINDOW.setProperty("%s.%d.TVShowThumb" % (request, count), item['thumbnail'])
                self.WINDOW.setProperty("%s.%d.SeasonThumb" % (request, count), seasonthumb)
                self.WINDOW.setProperty("%s.%d.Resume"      % (request, count), resume)
                self.WINDOW.setProperty("%s.%d.Percentage"  % (request, count), percentage)
                self.WINDOW.setProperty("%s.%d.File"        % (request, count), item['file'])
                self.WINDOW.setProperty("%s.%d.Path"        % (request, count), path)

    def _fetch_seasonthumb(self, tvshowid, seasonnumber):
        json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetSeasons", "params": {"properties": ["season", "thumbnail"], "tvshowid":%s }, "id": 1}' % tvshowid)
        json_query = unicode(json_query, 'utf-8', errors='ignore')
        json_response = simplejson.loads(json_query)
        if json_response['result'].has_key('seasons'):
            for item in json_response['result']['seasons']:
                season = "%.2d" % float(item['season'])
                if season == seasonnumber:
                    thumbnail = item['thumbnail']
                    return thumbnail

    def _fetch_musicvideo(self, request):
        if request == 'RandomMusicVideo':
            json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMusicVideos", "params": {"properties": ["title", "artist", "playcount", "year", "plot", "genre", "runtime", "fanart", "thumbnail", "file"], "filter": {"field": "playcount", "operator": "lessthan", "value": "1"}, "sort": {"order": "descending", "method": "playcount" }, "limits": {"end": %d}}, "id": 1}'  %self.LIMIT)
        elif self.RANDOMITEMS_UNPLAYED:
            json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMusicVideos", "params": {"properties": ["title", "artist", "playcount", "year", "plot", "genre", "runtime", "fanart", "thumbnail", "file"], "filter": {"field": "playcount", "operator": "lessthan", "value": "1"}, "sort": {"method": "random"}, "limits": {"end": %d}}, "id": 1}'  %self.LIMIT)
        else:
            json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMusicVideos", "params": {"properties": ["title", "artist", "playcount", "year", "plot", "genre", "runtime", "fanart", "thumbnail", "file"], "sort": {"method": "random"}, "limits": {"end": %d}}, "id": 1}'  %self.LIMIT)
        json_query = unicode(json_query, 'utf-8', errors='ignore')
        json_response = simplejson.loads(json_query)
        if json_response['result'].has_key('musicvideos'):
            self._clear_properties(request)        
            count = 0
            for item in json_response['result']['musicvideos']:
                count += 1
                path = media_path(item['file'])
                self.WINDOW.setProperty("%s.%d.Title"       % (request, count), item['title'])
                self.WINDOW.setProperty("%s.%d.Artist"      % (request, count), " / ".join(item['artist']))
                self.WINDOW.setProperty("%s.%d.Year"        % (request, count), str(item['year']))
                self.WINDOW.setProperty("%s.%d.Plot"        % (request, count), item['plot'])
                self.WINDOW.setProperty("%s.%d.Genre"       % (request, count), " / ".join(item['genre']))
                self.WINDOW.setProperty("%s.%d.Runtime"     % (request, count), item['runtime'])
                self.WINDOW.setProperty("%s.%d.Thumb"       % (request, count), item['thumbnail'])
                self.WINDOW.setProperty("%s.%d.Fanart"      % (request, count), item['fanart'])
                self.WINDOW.setProperty("%s.%d.File"        % (request, count), item['file'])
                self.WINDOW.setProperty("%s.%d.Path"        % (request, count), path)

    def _fetch_albums(self, request):
        if request == 'RecommendedAlbum':
            json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "AudioLibrary.GetAlbums", "params": {"properties": ["title", "description", "albumlabel", "artist", "genre", "year", "thumbnail", "fanart", "rating", "playcount"], "sort": {"order": "descending", "method": "playcount" }, "limits": {"end": %d}}, "id": 1}' %self.LIMIT)
        elif self.RANDOMITEMS_UNPLAYED:
            json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "AudioLibrary.GetAlbums", "params": {"properties": ["title", "description", "albumlabel", "artist", "genre", "year", "thumbnail", "fanart", "rating", "playcount"], "filter": {"field": "playcount", "operator": "lessthan", "value": "1"}, "sort": {"method": "random"}, "limits": {"end": %d}}, "id": 1}'  %self.LIMIT)
        else:
            json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "AudioLibrary.GetAlbums", "params": {"properties": ["title", "description", "albumlabel", "artist", "genre", "year", "thumbnail", "fanart", "rating", "playcount"], "sort": {"method": "random"}, "limits": {"end": %d}}, "id": 1}'  %self.LIMIT)
        json_response = unicode(json_query, 'utf-8', errors='ignore')
        jsonobject = simplejson.loads(json_response)
        if jsonobject['result'].has_key('albums'):
            self._clear_properties(request)
            count = 0
            for item in jsonobject['result']['albums']:
                count += 1
                rating = str(item['rating'])
                if rating == '48':
                    rating = ''
                path = 'XBMC.RunScript(' + __addonid__ + ',albumid=' + str(item.get('albumid')) + ')'
                self.WINDOW.setProperty("%s.%d.Title"       % (request, count), item['title'])
                self.WINDOW.setProperty("%s.%d.Label"       % (request, count), item['title']) #needs to be removed
                self.WINDOW.setProperty("%s.%d.Artist"      % (request, count), " / ".join(item['artist']))
                self.WINDOW.setProperty("%s.%d.Genre"       % (request, count), " / ".join(item['genre']))
                self.WINDOW.setProperty("%s.%d.Year"        % (request, count), str(item['year']))
                self.WINDOW.setProperty("%s.%d.RecordLabel" % (request, count), item['albumlabel'])
                self.WINDOW.setProperty("%s.%d.Description" % (request, count), item['description'])
                self.WINDOW.setProperty("%s.%d.Rating"      % (request, count), rating)
                self.WINDOW.setProperty("%s.%d.Thumb"       % (request, count), item['thumbnail'])
                self.WINDOW.setProperty("%s.%d.Fanart"      % (request, count), item['fanart'])
                self.WINDOW.setProperty("%s.%d.Play"        % (request, count), path)

    def _fetch_artist(self, request):
        json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "AudioLibrary.GetArtists", "params": {"properties": ["genre", "description", "fanart", "thumbnail"], "sort": {"method": "random"}, "limits": {"end": %d}}, "id": 1}'  %self.LIMIT)
        json_response = unicode(json_query, 'utf-8', errors='ignore')
        jsonobject = simplejson.loads(json_response)
        if jsonobject['result'].has_key('artists'):
            self._clear_properties(request)
            count = 0
            for item in jsonobject['result']['artists']:
                count += 1
                path = 'musicdb://2/' + str(item['artistid']) + '/'
                self.WINDOW.setProperty("%s.%d.Title"       % (request, count), item['label'])
                self.WINDOW.setProperty("%s.%d.Genre"       % (request, count), " / ".join(item['genre']))
                self.WINDOW.setProperty("%s.%d.Fanart"      % (request, count), item['fanart'])
                self.WINDOW.setProperty("%s.%d.Thumb"       % (request, count), item['thumbnail'])
                self.WINDOW.setProperty("%s.%d.Description" % (request, count), item['description'])
                self.WINDOW.setProperty("%s.%d.LibraryPath" % (request, count), path)

    def _fetch_song(self, request):
        if self.RANDOMITEMS_UNPLAYED == "True":
            json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "AudioLibrary.GetSongs", "params": {"properties": ["title", "playcount", "artist", "album", "year", "file", "thumbnail", "fanart", "rating"], "filter": {"field": "playcount", "operator": "lessthan", "value": "1"}, "sort": {"method": "random"}, "limits": {"end": %d}}, "id": 1}'  %self.LIMIT)
        else:
            json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "AudioLibrary.GetSongs", "params": {"properties": ["title", "playcount", "artist", "album", "year", "file", "thumbnail", "fanart", "rating"], "sort": {"method": "random"}, "limits": {"end": %d}}, "id": 1}'  %self.LIMIT)
        json_response = unicode(json_query, 'utf-8', errors='ignore')
        jsonobject = simplejson.loads(json_response)
        if jsonobject['result'].has_key('songs'):
            self._clear_properties(request)
            count = 0
            for item in jsonobject['result']['songs']:
                count += 1
                path = media_path(item['file'])
                self.WINDOW.setProperty("%s.%d.Title"  % (request, count), item['title'])
                self.WINDOW.setProperty("%s.%d.Artist" % (request, count), " / ".join(item['artist']))
                self.WINDOW.setProperty("%s.%d.Year"   % (request, count), str(item['year']))
                self.WINDOW.setProperty("%s.%d.Rating" % (request, count), str(int(item['rating'])-48))
                self.WINDOW.setProperty("%s.%d.Album"  % (request, count), item['album'])
                self.WINDOW.setProperty("%s.%d.Thumb"  % (request, count), item['thumbnail'])
                self.WINDOW.setProperty("%s.%d.Fanart" % (request, count), item['fanart'])
                self.WINDOW.setProperty("%s.%d.File"   % (request, count), item['file'])
                self.WINDOW.setProperty("%s.%d.Path"   % (request, count), path)

    def _fetch_addon(self, request):
        json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Addons.GetAddons", "params": {"properties": ["name", "author", "summary", "version", "fanart", "thumbnail"]}, "id": 1}')
        json_response = unicode(json_query, 'utf-8', errors='ignore')
        jsonobject = simplejson.loads(json_response)
        if jsonobject['result'].has_key('addons'):
            # find plugins and scripts
            addonlist = []
            for item in jsonobject['result']['addons']:
                if item['type'] == 'xbmc.python.script' or item['type'] == 'xbmc.python.pluginsource':
                    addonlist.append(item)
            # randomize the list
            random.shuffle(addonlist)
            self._clear_properties(request)
            count = 0
            for item in addonlist:
                count += 1
                self.WINDOW.setProperty("%s.%d.Title"   % (request, count), item['name'])
                self.WINDOW.setProperty("%s.%d.Author"  % (request, count), item['author'])
                self.WINDOW.setProperty("%s.%d.Summary" % (request, count), item['summary'])
                self.WINDOW.setProperty("%s.%d.Version" % (request, count), item['version'])
                self.WINDOW.setProperty("%s.%d.Path"    % (request, count), item['addonid'])
                self.WINDOW.setProperty("%s.%d.Fanart"  % (request, count), item['fanart'])
                self.WINDOW.setProperty("%s.%d.Thumb"   % (request, count), item['thumbnail'])
                self.WINDOW.setProperty("%s.%d.Type"    % (request, count), item['type'])
                # stop if we've reached the number of items we need
                if count == self.LIMIT:
                    break
            self.WINDOW.setProperty("%s.Count" % (request), str(jsonobject['result']['limits']['total']))
                
    def _daemon(self):
        # deamon is meant to keep script running at all time
        count = 0
        while (not xbmc.abortRequested) and self.WINDOW.getProperty('SkinWidgets_Running') == 'true':
            xbmc.sleep(500)
            if self.RANDOMITEMS_UPDATE_METHOD == 0:
                count += 1
                if count == self.RANDOMITEMS_TIME:
                    self._fetch_info_randomitems()
                    count = 0    # reset counter
            
    def _clear_properties(self, request):
        count = 0
        for count in range(int(self.LIMIT)):
            count += 1
            self.WINDOW.clearProperty("%s.%d.Title" % (request, count))

    def _update(self, type):
        xbmc.sleep(500)
        if type == 'movie':
            self._fetch_movies('RecommendedMovie')
        elif type == 'episode':
            self._fetch_tvshows_recommended('RecommendedEpisode')
        elif type == 'video':
            #only on db update
            self._fetch_movies('RecommendedMovie')
            self._fetch_tvshows_recommended('RecommendedEpisode')
        elif type == 'music':
            self._fetch_albums('RecommendedAlbum')
        if self.RANDOMITEMS_UPDATE_METHOD == 1:
            # update random if db update is selected instead of timer
            if type == 'video':
                self._fetch_movies('RandomMovie')
                self._fetch_tvshows_randomitems('RandomEpisode')
                self._fetch_musicvideo('RandomMusicVideo')
            elif type == 'music':
                self._fetch_albums('RandomAlbum')
                self._fetch_artist('RandomArtist')
                self._fetch_song('RandomSong')
                self._fetch_addon('RandomAddon')

def media_path(path):
    # Check for stacked movies
    try:
        path = os.path.split(path)[0].rsplit(' , ', 1)[1].replace(",,",",")
    except:
        path = os.path.split(path)[0]
    # Fixes problems with rared movies and multipath
    if path.startswith("rar://"):
        path = [os.path.split(urllib.url2pathname(path.replace("rar://","")))[0]]
    elif path.startswith("multipath://"):
        temp_path = path.replace("multipath://","").split('%2f/')
        path = []
        for item in temp_path:
            path.append(urllib.url2pathname(item))
    else:
        path = [path]
    return path[0]
            
class MyMonitor(xbmc.Monitor):
    def __init__(self, *args, **kwargs):
        xbmc.Monitor.__init__(self)
        self.update_listitems = kwargs['update_listitems']
        self.update_settings = kwargs['update_settings']

    def onDatabaseUpdated(self, database):
        self.update_listitems(database)
        
    def onSettingsChanged(self):
        self.update_settings()

class MyPlayer(xbmc.Player):
    def __init__(self, *args, **kwargs):
        xbmc.Player.__init__(self)
        self.action = kwargs[ "action" ]
        self.substrings = [ '-trailer', 'http://' ]

    def onPlayBackStarted(self):
        xbmc.sleep(1000)
        self.type = ""
        # Set values based on the file content
        if (self.isPlayingAudio()):
            self.type = "album"  
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
        if self.type == 'movie':
            self.action('movie')
        elif self.type == 'episode':
            self.action('episode')
        elif self.type == 'album':
            self.action('album')
        self.type = ""
        

    def onPlayBackStopped(self):
        if self.type == 'movie':
            self.action('movie')
        elif self.type == 'episode':
            self.action('episode')
        elif self.type == 'album':
            self.action('album')
        self.type = ""

if (__name__ == "__main__"):
    log('script version %s started' % __addonversion__)
    Main()
