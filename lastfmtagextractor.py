#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
    lastfmtagextractor.py
    
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    @author: Aaron McKee (ucbmckee)
    v0.61 : May. 2012
'''

from lastfmtagextractor.config import LastFM_Config
from lastfmtagextractor.outputwrapper import OutputWrapper, KillRequestException
from lastfmtagextractor.medialibrary import MediaLibrary
import os.path
import sys
           
def main(argv=None):
    config = LastFM_Config(argv)
    
    if (config.getboolean('delcache') and os.path.exists(config.get('cachefile'))):
        if (config.getboolean('verbose')):
            print 'Removing existing cachefile'
        os.remove(config.get('cacheFile'))
    
    print ('Launching [' + os.path.basename(sys.argv[0]) + ']')    
                      
    outputWrapper = OutputWrapper(config)

    try:                
        library = MediaLibrary(config, outputWrapper)
        if (not config.getboolean('skipscan')):        
            library.readMedia()
            library.writeCache()
    
        if (not config.getboolean('skipfetch')):
            try:
                library.fetchTags()
            except KillRequestException, err:
                library.writeCache()
                raise
            library.writeCache()
            
        if (not config.getboolean('skipupdate')):
            library.updateTags()
            library.writeCache()
        
        outputWrapper.logNormal('DONE')
        
    except KillRequestException:
        outputWrapper.logNormal('Closing on user request')    
    finally:   
        outputWrapper.close()
    
if __name__ == '__main__':
    sys.exit(main())
