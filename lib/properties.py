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
from lib.utils import media_path, media_streamdetails
from lib.requests import req
import os
import random
import sys
import xbmc
import xbmcgui
import xbmcvfs
if sys.version_info < (2, 7):
    import simplejson
else:
    import json as simplejson

__addon__        = lib.common.__addon__
__addonid__      = lib.common.__addonid__
__localize__     = lib.common.__localize__

WINDOW = xbmcgui.Window(10000)
LIMIT = 20
PLOT_ENABLE = __addon__.getSetting("plot_enable")  == 'true'

class gui:
    def movies(self, request, data):
        if data:
            clear_properties(request)
            count = 0
            for item in data['result']['movies']:
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
                if not PLOT_ENABLE and watched == "false":
                    plot = __localize__(32014)
                else:
                    plot = item['plot']
                art = item['art']
                path = media_path(item['file'])
                play = 'XBMC.RunScript(' + __addonid__ + ',movieid=' + str(item.get('movieid')) + ')'
                streaminfo = media_streamdetails(item['file'].encode('utf-8').lower(),
                                                 item['streamdetails'])
                WINDOW.setProperty("%s.%d.DBID"            % (request, count), str(item.get('movieid')))
                WINDOW.setProperty("%s.%d.Title"           % (request, count), item['title'])
                WINDOW.setProperty("%s.%d.OriginalTitle"   % (request, count), item['originaltitle'])
                WINDOW.setProperty("%s.%d.Year"            % (request, count), str(item['year']))
                WINDOW.setProperty("%s.%d.Genre"           % (request, count), " / ".join(item['genre']))
                WINDOW.setProperty("%s.%d.Studio"          % (request, count), item['studio'][0])
                WINDOW.setProperty("%s.%d.Country"         % (request, count), item['country'][0])
                WINDOW.setProperty("%s.%d.Plot"            % (request, count), plot)
                WINDOW.setProperty("%s.%d.PlotOutline"     % (request, count), item['plotoutline'])
                WINDOW.setProperty("%s.%d.Tagline"         % (request, count), item['tagline'])
                WINDOW.setProperty("%s.%d.Runtime"         % (request, count), str(int((item['runtime'] / 60) + 0.5)))
                WINDOW.setProperty("%s.%d.Rating"          % (request, count), str(round(float(item['rating']),1)))
                WINDOW.setProperty("%s.%d.mpaa"            % (request, count), item['mpaa'])
                WINDOW.setProperty("%s.%d.Director"        % (request, count), " / ".join(item['director']))
                WINDOW.setProperty("%s.%d.Trailer"         % (request, count), item['trailer'])
                WINDOW.setProperty("%s.%d.Art(poster)"     % (request, count), art.get('poster',''))
                WINDOW.setProperty("%s.%d.Art(fanart)"     % (request, count), art.get('fanart',''))
                WINDOW.setProperty("%s.%d.Art(clearlogo)"  % (request, count), art.get('clearlogo',''))
                WINDOW.setProperty("%s.%d.Art(clearart)"   % (request, count), art.get('clearart',''))
                WINDOW.setProperty("%s.%d.Art(landscape)"  % (request, count), art.get('landscape',''))
                WINDOW.setProperty("%s.%d.Art(banner)"     % (request, count), art.get('banner',''))
                WINDOW.setProperty("%s.%d.Art(discart)"    % (request, count), art.get('discart',''))                
                WINDOW.setProperty("%s.%d.Resume"          % (request, count), resume)
                WINDOW.setProperty("%s.%d.PercentPlayed"   % (request, count), played)
                WINDOW.setProperty("%s.%d.Watched"         % (request, count), watched)
                WINDOW.setProperty("%s.%d.File"            % (request, count), item['file'])
                WINDOW.setProperty("%s.%d.Path"            % (request, count), path)
                WINDOW.setProperty("%s.%d.Play"            % (request, count), play)
                WINDOW.setProperty("%s.%d.VideoCodec"      % (request, count), streaminfo['videocodec'])
                WINDOW.setProperty("%s.%d.VideoResolution" % (request, count), streaminfo['videoresolution'])
                WINDOW.setProperty("%s.%d.VideoAspect"     % (request, count), streaminfo['videoaspect'])
                WINDOW.setProperty("%s.%d.AudioCodec"      % (request, count), streaminfo['audiocodec'])
                WINDOW.setProperty("%s.%d.AudioChannels"   % (request, count), str(streaminfo['audiochannels']))
        del data

    def episodes_recommended(self, request, data):
        if data:
            clear_properties(request)
            count = 0
            for item in data['result']['tvshows']:
                if xbmc.abortRequested:
                    break
                count += 1
                data2 = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params": {"tvshowid": %d, "properties": ["title", "playcount", "plot", "season", "episode", "showtitle", "file", "lastplayed", "rating", "resume", "art", "streamdetails", "firstaired", "runtime"], "sort": {"method": "episode"}, "filter": {"field": "playcount", "operator": "is", "value": "0"}, "limits": {"end": 1}}, "id": 1}' %item['tvshowid'])
                data2 = unicode(data2, 'utf-8', errors='ignore')
                data2 = simplejson.loads(data2)
                if data2.has_key('result') and data2['result'] != None and data2['result'].has_key('episodes'):
                    for item2 in data2['result']['episodes']:
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
                        if not PLOT_ENABLE and watched == "false":
                            plot = __localize__(32014)
                        else:
                            plot = item2['plot']
                        art = item['art']
                        path = media_path(item['file'])
                        play = 'XBMC.RunScript(' + __addonid__ + ',episodeid=' + str(item2.get('episodeid')) + ')'
                        streaminfo = media_streamdetails(item['file'].encode('utf-8').lower(),
                                                         item2['streamdetails'])
                        WINDOW.setProperty("%s.%d.DBID"                % (request, count), str(item2.get('episodeid')))
                        WINDOW.setProperty("%s.%d.Title"               % (request, count), item2['title'])
                        WINDOW.setProperty("%s.%d.Episode"             % (request, count), episode)
                        WINDOW.setProperty("%s.%d.EpisodeNo"           % (request, count), episodeno)
                        WINDOW.setProperty("%s.%d.Season"              % (request, count), season)
                        WINDOW.setProperty("%s.%d.Plot"                % (request, count), plot)
                        WINDOW.setProperty("%s.%d.TVshowTitle"         % (request, count), item2['showtitle'])
                        WINDOW.setProperty("%s.%d.Rating"              % (request, count), rating)
                        WINDOW.setProperty("%s.%d.Runtime"             % (request, count), str(int((item2['runtime'] / 60) + 0.5)))
                        WINDOW.setProperty("%s.%d.Premiered"           % (request, count), item2['firstaired'])
                        WINDOW.setProperty("%s.%d.Art(thumb)"          % (request, count), art2.get('thumb',''))
                        WINDOW.setProperty("%s.%d.Art(tvshow.fanart)"  % (request, count), art2.get('tvshow.fanart',''))
                        WINDOW.setProperty("%s.%d.Art(tvshow.poster)"  % (request, count), art2.get('tvshow.poster',''))
                        WINDOW.setProperty("%s.%d.Art(tvshow.banner)"  % (request, count), art2.get('tvshow.banner',''))
                        WINDOW.setProperty("%s.%d.Art(tvshow.clearlogo)"% (request, count), art2.get('tvshow.clearlogo',''))
                        WINDOW.setProperty("%s.%d.Art(tvshow.clearart)" % (request, count), art2.get('tvshow.clearart',''))
                        WINDOW.setProperty("%s.%d.Art(tvshow.landscape)"% (request, count), art2.get('tvshow.landscape',''))
                        WINDOW.setProperty("%s.%d.Art(tvshow.characterart)"% (request, count), art2.get('tvshow.characterart',''))
                        #WINDOW.setProperty("%s.%d.Art(season.poster)" % (request, count), seasonthumb)
                        WINDOW.setProperty("%s.%d.Studio"              % (request, count), item['studio'][0])
                        WINDOW.setProperty("%s.%d.mpaa"                % (request, count), item['mpaa'])
                        WINDOW.setProperty("%s.%d.Resume"              % (request, count), resume)
                        WINDOW.setProperty("%s.%d.PercentPlayed"       % (request, count), played)
                        WINDOW.setProperty("%s.%d.Watched"             % (request, count), watched)
                        WINDOW.setProperty("%s.%d.File"                % (request, count), item2['file'])
                        WINDOW.setProperty("%s.%d.Path"                % (request, count), path)
                        WINDOW.setProperty("%s.%d.Play"                % (request, count), play)
                        WINDOW.setProperty("%s.%d.VideoCodec"          % (request, count), streaminfo['videocodec'])
                        WINDOW.setProperty("%s.%d.VideoResolution"     % (request, count), streaminfo['videoresolution'])
                        WINDOW.setProperty("%s.%d.VideoAspect"         % (request, count), streaminfo['videoaspect'])
                        WINDOW.setProperty("%s.%d.AudioCodec"          % (request, count), streaminfo['audiocodec'])
                        WINDOW.setProperty("%s.%d.AudioChannels"       % (request, count), str(streaminfo['audiochannels']))
                del data2
        del data

    def episodes(self, request, data):
        if data:
            season_folders = __addon__.getSetting("randomitems_seasonfolders")
            clear_properties(request)
            count = 0
            for item in data['result']['episodes']:
                count += 1
                '''
                # This part is commented out because it takes 1.5second extra on my system to request these which doubles the total time.
                # Hence the ugly path hack that will require users to have season folders.
                data2 = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShowDetails", "params": {"properties": ["file", "studio"], "tvshowid":%s}, "id": 1}' %item['tvshowid'])
                data2 = unicode(data2, 'utf-8', errors='ignore')
                data2 = simplejson.loads(data2)
                path = data2['result']['tvshowdetails']['file']
                studio = data2['result']['tvshowdetails']['studio'][0]
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
                if not PLOT_ENABLE and watched == "false":
                    plot = __localize__(32014)
                else:
                    plot = item['plot']
                art = item['art']
                path = media_path(item['file'])
                play = 'XBMC.RunScript(' + __addonid__ + ',episodeid=' + str(item.get('episodeid')) + ')'
                streaminfo = media_streamdetails(item['file'].encode('utf-8').lower(),
                                                 item['streamdetails'])
                WINDOW.setProperty("%s.%d.DBID"                % (request, count), str(item.get('episodeid')))
                WINDOW.setProperty("%s.%d.Title"               % (request, count), item['title'])
                WINDOW.setProperty("%s.%d.Episode"             % (request, count), episode)
                WINDOW.setProperty("%s.%d.EpisodeNo"           % (request, count), episodeno)
                WINDOW.setProperty("%s.%d.Season"              % (request, count), season)
                WINDOW.setProperty("%s.%d.Plot"                % (request, count), plot)
                WINDOW.setProperty("%s.%d.TVshowTitle"         % (request, count), item['showtitle'])
                WINDOW.setProperty("%s.%d.Rating"              % (request, count), rating)
                WINDOW.setProperty("%s.%d.Runtime"             % (request, count), str(int((item['runtime'] / 60) + 0.5)))
                WINDOW.setProperty("%s.%d.Premiered"           % (request, count), item['firstaired'])
                WINDOW.setProperty("%s.%d.Art(thumb)"          % (request, count), art.get('thumb',''))
                WINDOW.setProperty("%s.%d.Art(tvshow.fanart)"  % (request, count), art.get('tvshow.fanart',''))
                WINDOW.setProperty("%s.%d.Art(tvshow.poster)"  % (request, count), art.get('tvshow.poster',''))
                WINDOW.setProperty("%s.%d.Art(tvshow.banner)"  % (request, count), art.get('tvshow.banner',''))
                WINDOW.setProperty("%s.%d.Art(tvshow.clearlogo)"% (request, count), art.get('tvshow.clearlogo',''))
                WINDOW.setProperty("%s.%d.Art(tvshow.clearart)" % (request, count), art.get('tvshow.clearart',''))
                WINDOW.setProperty("%s.%d.Art(tvshow.landscape)"% (request, count), art.get('tvshow.landscape',''))
                WINDOW.setProperty("%s.%d.Art(tvshow.characterart)"% (request, count), art.get('tvshow.characterart',''))
                WINDOW.setProperty("%s.%d.Resume"              % (request, count), resume)
                WINDOW.setProperty("%s.%d.PercentPlayed"       % (request, count), played)
                WINDOW.setProperty("%s.%d.Watched"             % (request, count), watched)
                WINDOW.setProperty("%s.%d.File"                % (request, count), item['file'])
                WINDOW.setProperty("%s.%d.Path"                % (request, count), path)
                WINDOW.setProperty("%s.%d.Play"                % (request, count), play)
                WINDOW.setProperty("%s.%d.VideoCodec"          % (request, count), streaminfo['videocodec'])
                WINDOW.setProperty("%s.%d.VideoResolution"     % (request, count), streaminfo['videoresolution'])
                WINDOW.setProperty("%s.%d.VideoAspect"         % (request, count), streaminfo['videoaspect'])
                WINDOW.setProperty("%s.%d.AudioCodec"          % (request, count), streaminfo['audiocodec'])
                WINDOW.setProperty("%s.%d.AudioChannels"       % (request, count), str(streaminfo['audiochannels']))
        del data

    def musicvideos(self, request, data):
        if data:
            clear_properties(request)        
            count = 0
            for item in data['result']['musicvideos']:
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
                WINDOW.setProperty("%s.%d.DBID"           % (request, count), str(item.get('musicvideoid')))
                WINDOW.setProperty("%s.%d.Title"           % (request, count), item['title'])
                WINDOW.setProperty("%s.%d.Artist"          % (request, count), " / ".join(item['artist']))
                WINDOW.setProperty("%s.%d.Year"            % (request, count), str(item['year']))
                WINDOW.setProperty("%s.%d.Plot"            % (request, count), item['plot'])
                WINDOW.setProperty("%s.%d.Genre"           % (request, count), " / ".join(item['genre']))
                WINDOW.setProperty("%s.%d.Runtime"         % (request, count), str(int((item['runtime'] / 60) + 0.5)))
                WINDOW.setProperty("%s.%d.Thumb"           % (request, count), item['thumbnail']) #remove
                WINDOW.setProperty("%s.%d.Fanart"          % (request, count), item['fanart']) #remove
                WINDOW.setProperty("%s.%d.Art(thumb)"      % (request, count), item['thumbnail'])
                WINDOW.setProperty("%s.%d.Art(fanart)"     % (request, count), item['fanart'])
                WINDOW.setProperty("%s.%d.File"            % (request, count), item['file'])
                WINDOW.setProperty("%s.%d.Path"            % (request, count), path)
                WINDOW.setProperty("%s.%d.Resume"          % (request, count), resume)
                WINDOW.setProperty("%s.%d.PercentPlayed"   % (request, count), played)
                WINDOW.setProperty("%s.%d.Watched"         % (request, count), watched)
                WINDOW.setProperty("%s.%d.Play"            % (request, count), play)
                WINDOW.setProperty("%s.%d.VideoCodec"      % (request, count), streaminfo['videocodec'])
                WINDOW.setProperty("%s.%d.VideoResolution" % (request, count), streaminfo['videoresolution'])
                WINDOW.setProperty("%s.%d.VideoAspect"     % (request, count), streaminfo['videoaspect'])
                WINDOW.setProperty("%s.%d.AudioCodec"      % (request, count), streaminfo['audiocodec'])
                WINDOW.setProperty("%s.%d.AudioChannels"   % (request, count), str(streaminfo['audiochannels']))
        del data

    def albums(self, request, data):
        if data:
            clear_properties(request)
            count = 0
            for item in data['result']['albums']:
                count += 1
                rating = str(item['rating'])
                if rating == '48':
                    rating = ''
                play = 'XBMC.RunScript(' + __addonid__ + ',albumid=' + str(item.get('albumid')) + ')'
                WINDOW.setProperty("%s.%d.Title"       % (request, count), item['title'])
                WINDOW.setProperty("%s.%d.Label"       % (request, count), item['title']) #needs to be removed
                WINDOW.setProperty("%s.%d.Artist"      % (request, count), " / ".join(item['artist']))
                WINDOW.setProperty("%s.%d.Genre"       % (request, count), " / ".join(item['genre']))
                WINDOW.setProperty("%s.%d.Theme"       % (request, count), " / ".join(item['theme']))
                WINDOW.setProperty("%s.%d.Mood"        % (request, count), " / ".join(item['mood']))
                WINDOW.setProperty("%s.%d.Style"       % (request, count), " / ".join(item['style']))
                WINDOW.setProperty("%s.%d.Type"        % (request, count), " / ".join(item['type']))
                WINDOW.setProperty("%s.%d.Year"        % (request, count), str(item['year']))
                WINDOW.setProperty("%s.%d.RecordLabel" % (request, count), item['albumlabel'])
                WINDOW.setProperty("%s.%d.Description" % (request, count), item['description'])
                WINDOW.setProperty("%s.%d.Rating"      % (request, count), rating)
                WINDOW.setProperty("%s.%d.Thumb"       % (request, count), item['thumbnail']) #remove
                WINDOW.setProperty("%s.%d.Fanart"      % (request, count), item['fanart']) #remove
                WINDOW.setProperty("%s.%d.Art(thumb)"  % (request, count), item['thumbnail'])
                WINDOW.setProperty("%s.%d.Art(fanart)" % (request, count), item['fanart'])
                WINDOW.setProperty("%s.%d.Play"        % (request, count), play)
        del data
        
    def artists(self, request, data):
        if data:
            clear_properties(request)
            count = 0
            for item in data['result']['artists']:
                count += 1
                path = 'musicdb://2/' + str(item['artistid']) + '/'
                WINDOW.setProperty("%s.%d.Title"       % (request, count), item['label'])
                WINDOW.setProperty("%s.%d.Genre"       % (request, count), " / ".join(item['genre']))
                WINDOW.setProperty("%s.%d.Thumb"       % (request, count), item['thumbnail']) #remove
                WINDOW.setProperty("%s.%d.Fanart"      % (request, count), item['fanart']) #remove
                WINDOW.setProperty("%s.%d.Art(thumb)"  % (request, count), item['thumbnail'])
                WINDOW.setProperty("%s.%d.Art(fanart)" % (request, count), item['fanart'])
                WINDOW.setProperty("%s.%d.Description" % (request, count), item['description'])
                WINDOW.setProperty("%s.%d.Born"        % (request, count), item['born'])
                WINDOW.setProperty("%s.%d.Died"        % (request, count), item['died'])
                WINDOW.setProperty("%s.%d.Formed"      % (request, count), item['formed'])
                WINDOW.setProperty("%s.%d.Disbanded"   % (request, count), item['disbanded'])
                WINDOW.setProperty("%s.%d.YearsActive" % (request, count), " / ".join(item['yearsactive']))
                WINDOW.setProperty("%s.%d.Style"       % (request, count), " / ".join(item['style']))
                WINDOW.setProperty("%s.%d.Mood"        % (request, count), " / ".join(item['mood']))
                WINDOW.setProperty("%s.%d.Instrument"  % (request, count), " / ".join(item['instrument']))
                WINDOW.setProperty("%s.%d.LibraryPath" % (request, count), path)
                
    def songs(self, request, data):
        if data:
            clear_properties(request)
            count = 0
            for item in data['result']['songs']:
                count += 1
                play = 'XBMC.RunScript(' + __addonid__ + ',songid=' + str(item.get('songid')) + ')'
                path = media_path(item['file'])
                WINDOW.setProperty("%s.%d.Title"       % (request, count), item['title'])
                WINDOW.setProperty("%s.%d.Artist"      % (request, count), " / ".join(item['artist']))
                WINDOW.setProperty("%s.%d.Year"        % (request, count), str(item['year']))
                WINDOW.setProperty("%s.%d.Rating"      % (request, count), str(int(item['rating'])-48))
                WINDOW.setProperty("%s.%d.Album"       % (request, count), item['album'])
                WINDOW.setProperty("%s.%d.Thumb"       % (request, count), item['thumbnail']) #remove
                WINDOW.setProperty("%s.%d.Fanart"      % (request, count), item['fanart']) #remove
                WINDOW.setProperty("%s.%d.Art(thumb)"  % (request, count), item['thumbnail'])
                WINDOW.setProperty("%s.%d.Art(fanart)" % (request, count), item['fanart'])
                WINDOW.setProperty("%s.%d.File"        % (request, count), item['file'])
                WINDOW.setProperty("%s.%d.Path"        % (request, count), path)
                WINDOW.setProperty("%s.%d.Play"        % (request, count), play)
        del data  

    def addons(self, request, data):
        if data:
            # find plugins and scripts
            addonlist = []
            for item in data['result']['addons']:
                if item['type'] == 'xbmc.python.script' or item['type'] == 'xbmc.python.pluginsource':
                    addonlist.append(item)
            # randomize the list
            random.shuffle(addonlist)
            clear_properties(request)
            count = 0
            for item in addonlist:
                count += 1
                WINDOW.setProperty("%s.%d.Title"       % (request, count), item['name'])
                WINDOW.setProperty("%s.%d.Author"      % (request, count), item['author'])
                WINDOW.setProperty("%s.%d.Summary"     % (request, count), item['summary'])
                WINDOW.setProperty("%s.%d.Version"     % (request, count), item['version'])
                WINDOW.setProperty("%s.%d.Path"        % (request, count), item['addonid'])
                WINDOW.setProperty("%s.%d.Thumb"       % (request, count), item['thumbnail']) #remove
                WINDOW.setProperty("%s.%d.Fanart"      % (request, count), item['fanart']) #remove
                WINDOW.setProperty("%s.%d.Art(thumb)"  % (request, count), item['thumbnail'])
                WINDOW.setProperty("%s.%d.Art(fanart)" % (request, count), item['fanart'])
                WINDOW.setProperty("%s.%d.Type"        % (request, count), item['type'])
                # stop if we've reached the number of items we need
                if count == LIMIT:
                    break
            WINDOW.setProperty("%s.Count" % (request), str(data['result']['limits']['total']))
        del data

def clear_properties(request):
    count = 0
    for count in range(int(LIMIT)):
        count += 1
        WINDOW.clearProperty("%s.%d.Title" % (request, count))
