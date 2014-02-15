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

import lib.common
import sys
import xbmc
if sys.version_info < (2, 7):
    import simplejson
else:
    import json as simplejson

__addon__        = lib.common.__addon__
LIMIT = 20
RANDOMITEMS_UNPLAYED = __addon__.getSetting("randomitems_unplayed") == 'true'
RECENTITEMS_UNPLAYED = __addon__.getSetting("recentitems_unplayed") == 'true'

class req:
    def movies(self, request):
        json_string = '{"jsonrpc": "2.0",  "id": 1, "method": "VideoLibrary.GetMovies", "params": {"properties": ["title", "originaltitle", "playcount", "year", "genre", "studio", "country", "tagline", "plot", "runtime", "file", "plotoutline", "lastplayed", "trailer", "rating", "resume", "art", "streamdetails", "mpaa", "director", "votes"], "limits": {"end": %d},' %LIMIT
        if request == 'RecommendedMovie':
            json_query = xbmc.executeJSONRPC('%s "sort": {"order": "descending", "method": "lastplayed"}, "filter": {"field": "inprogress", "operator": "true", "value": ""}}}' %json_string)
        elif request == 'RecentMovie' and RECENTITEMS_UNPLAYED:
            json_query = xbmc.executeJSONRPC('%s "sort": {"order": "descending", "method": "dateadded"}, "filter": {"field": "playcount", "operator": "is", "value": "0"}}}' %json_string)
        elif request == 'RecentMovie':
            json_query = xbmc.executeJSONRPC('%s "sort": {"order": "descending", "method": "dateadded"}}}' %json_string)
        elif request == "RandomMovie" and RANDOMITEMS_UNPLAYED:
            json_query = xbmc.executeJSONRPC('%s "sort": {"method": "random" }, "filter": {"field": "playcount", "operator": "lessthan", "value": "1"}}}' %json_string)
        else:
            json_query = xbmc.executeJSONRPC('%s "sort": {"method": "random" } }}' %json_string)
        json_query = unicode(json_query, 'utf-8', errors='ignore')
        json_query = simplejson.loads(json_query)
        if json_query.has_key('result') and json_query['result'].has_key('movies'):
            return json_query
        else:
            return False

    def tvshows(self, request):
        json_string = '{"jsonrpc": "2.0", "id": 1, "method": "VideoLibrary.GetEpisodes", "params": { "properties": ["title", "playcount", "season", "episode", "showtitle", "plot", "file", "rating", "resume", "tvshowid", "art", "streamdetails", "firstaired", "runtime"], "limits": {"end": %d},' %LIMIT
        if request == 'RecentEpisode' and RECENTITEMS_UNPLAYED:
            json_query = xbmc.executeJSONRPC('%s "sort": {"order": "descending", "method": "dateadded"}, "filter": {"field": "playcount", "operator": "lessthan", "value": "1"}}}' %json_string)
        elif request == 'RecentEpisode':
            json_query = xbmc.executeJSONRPC('%s "sort": {"order": "descending", "method": "dateadded"}}}' %json_string)
        elif request == 'RandomEpisode' and RANDOMITEMS_UNPLAYED:
            json_query = xbmc.executeJSONRPC('%s "sort": {"method": "random" }, "filter": {"field": "playcount", "operator": "lessthan", "value": "1"}}}' %json_string)
        else:
            json_query = xbmc.executeJSONRPC('%s "sort": {"method": "random" }}}' %json_string)
        json_query = unicode(json_query, 'utf-8', errors='ignore')
        json_query = simplejson.loads(json_query)
        if json_query.has_key('result') and json_query['result'].has_key('episodes'):
            return json_query
        else:
            return False

    def tvshows_recommended(self, request):
        if not xbmc.abortRequested:
            # First unplayed episode of recent played tvshows
            json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows", "params": {"properties": ["title", "studio", "mpaa", "file", "art"], "sort": {"order": "descending", "method": "lastplayed"}, "filter": {"field": "inprogress", "operator": "true", "value": ""}, "limits": {"end": %d}}, "id": 1}' %LIMIT)
            json_query = unicode(json_query, 'utf-8', errors='ignore')
            json_query = simplejson.loads(json_query)
            if json_query.has_key('result') and json_query['result'].has_key('tvshows'):
                return json_query
            else:
                return False

    def seasonthumb(self, tvshowid, seasonnumber):
        json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetSeasons", "params": {"properties": ["season", "thumbnail"], "tvshowid":%s }, "id": 1}' % tvshowid)
        json_query = unicode(json_query, 'utf-8', errors='ignore')
        json_query = simplejson.loads(json_query)
        if json_query.has_key('result') and json_query['result'].has_key('seasons'):
            for item in json_query['result']['seasons']:
                season = "%.2d" % float(item['season'])
                if season == seasonnumber:
                    thumbnail = item['thumbnail']
                    return thumbnail

    def musicvideos(self, request):
        json_string = '{"jsonrpc": "2.0",  "id": 1, "method": "VideoLibrary.GetMusicVideos", "params": {"properties": ["title", "artist", "playcount", "year", "plot", "genre", "runtime", "fanart", "thumbnail", "file", "streamdetails", "resume"],  "limits": {"end": %d},' %LIMIT
        if request == 'RecommendedMusicVideo':
            json_query = xbmc.executeJSONRPC('%s "sort": {"order": "descending", "method": "playcount" }}}'  %json_string)
        elif request == 'RecentMusicVideo':
            json_query = xbmc.executeJSONRPC('%s "sort": {"order": "descending", "method": "dateadded"}}}'  %json_string)
        else:
            json_query = xbmc.executeJSONRPC('%s "sort": {"method": "random"}}}' %json_string)
        json_query = unicode(json_query, 'utf-8', errors='ignore')
        json_query = simplejson.loads(json_query)
        if json_query.has_key('result') and json_query['result'].has_key('musicvideos'):
            return json_query
        else:
            return False

    def albums(self, request):
        json_string = '{"jsonrpc": "2.0", "id": 1, "method": "AudioLibrary.GetAlbums", "params": {"properties": ["title", "description", "albumlabel", "theme", "mood", "style", "type", "artist", "genre", "year", "thumbnail", "fanart", "rating", "playcount"], "limits": {"end": %d},' %LIMIT
        if request == 'RecommendedAlbum':
            json_query = xbmc.executeJSONRPC('%s "sort": {"order": "descending", "method": "playcount" }}}' %json_string)
        elif request == 'RecentAlbum':
            json_query = xbmc.executeJSONRPC('%s "sort": {"order": "descending", "method": "dateadded" }}}' %json_string)
        else:
            json_query = xbmc.executeJSONRPC('%s "sort": {"method": "random"}}}' %json_string)
        json_query = unicode(json_query, 'utf-8', errors='ignore')
        json_query = simplejson.loads(json_query)
        if json_query.has_key('result') and json_query['result'].has_key('albums'):
            return json_query
        else:
            return False

    def artist(self, request):
        # Random artist
        json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "AudioLibrary.GetArtists", "params": {"properties": ["genre", "description", "mood", "style", "born", "died", "formed", "disbanded", "yearsactive", "instrument", "fanart", "thumbnail"], "sort": {"method": "random"}, "limits": {"end": %d}}, "id": 1}'  %LIMIT)
        json_query = unicode(json_query, 'utf-8', errors='ignore')
        json_query = simplejson.loads(json_query)
        if json_query.has_key('result') and json_query['result'].has_key('artists'):
            return json_query
        else:
            return False

    def songs(self, request):
        json_string = '{"jsonrpc": "2.0", "id": 1, "method": "AudioLibrary.GetSongs", "params": {"properties": ["title", "playcount", "artist", "album", "year", "file", "thumbnail", "fanart", "rating"], "filter": {"field": "playcount", "operator": "lessthan", "value": "1"}, "limits": {"end": %d},' %LIMIT
        if request == 'RandomSong' and RANDOMITEMS_UNPLAYED == "True":
            json_query = xbmc.executeJSONRPC('%s "sort": {"method": "random"}}}'  %json_string)
        else:
            json_query = xbmc.executeJSONRPC('%s  "sort": {"method": "random"}}}'  %json_string)
        json_query = unicode(json_query, 'utf-8', errors='ignore')
        json_query = simplejson.loads(json_query)
        if json_query.has_key('result') and json_query['result'].has_key('songs'):
            return json_query
        else:
            return False

    def addons(self, request):
        json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Addons.GetAddons", "params": {"properties": ["name", "author", "summary", "version", "fanart", "thumbnail"]}, "id": 1}')
        json_query = unicode(json_query, 'utf-8', errors='ignore')
        json_query = simplejson.loads(json_query)
        if json_query.has_key('result') and json_query['result'].has_key('addons'):
            return json_query
        else:
            return False