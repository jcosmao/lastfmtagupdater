import getopt,os.path,sys,configparser
from . import common

class LastFM_Config:
    config_section = 'lastfm_tagger'

    usage_message = '''
This utility updates media files with tags retrieved from LastFM. Please see the configuration file and
documentation for an explanation of the various operating parameters. You very likely do not want to use
the defaults.

Usage:
    --cfg=file     the configuration file to use (default: lastfm_tagger.conf)
    --dir=mediadir set directory to work on ( override config file )
    --delcache     delete an existing cache file, if it exists
    --skipscan     do not scan the media directory (use only those values already in the cache file)
    --skipfetch    do not fetch tags from LastFM (use only those values already in the cache file)
    --skipupdate   do not update the media files (useful if you want to audit the cache file first)
'''


    defaults = dict(
        lastFMAPI_key='',
        lastFMAPI_secret='',
        verbose='true',
        cfg='lastfm_tagger.conf',
        delcache='false',
        skipscan='false',
        skipfetch='false',
        skipupdate='false',
        cacheFile='librarycache.xml',
        logFile='lastfmtagupdater.log',
        mediadir='.',
        niceness='50',
        ignoreCase='true',
        refetchCachedTags='false',
        getArtistTags='true',
        getTrackTags='true',
        minArtistTagWeight='50',
        minTrackTagWeight='50',
        maxTagLength='25',
        minLibraryCount='1',
        minLastFMCount='0',
        tagSynonymsFile='',
        artistSkipListFile='',
        capTagWords='true',
        skipExtensions='jpg,ini,m3u,db,nfo,par2',
        writeUntaggedTag='no',
        artistField='both',
        artistTagFields='comment',
        trackTagFields='comment',
        overwriteFields='',
        forceOverwriteFields='',
        genreMaxTags='1',
        groupingMaxTags='5',
        commentMaxTags='10',
        genreTagSkipCount='0',
        groupingTagSkipCount='0',
        commentTagSkipCount='0',
        genreSort='record',
        groupingSort='record',
        commentSort='record',
        id3v1Handling='0',
        id3v2DupeHeaderFix='false',
        tagStartDelim='',
        tagEndDelim='',
        tagSep=';')

    allowedMediaWriteFields = set(['genre', 'grouping', 'comment', ''])
    allowedSortOptions = set(['record', 'popularity', 'library'])

    def __init__(self, argv=None):
        self.config = self.parseargs(argv)


    def parseargs(self, argv=None):
        if argv is None:
            argv = sys.argv
        try:
            # command line processing
            opts, args = getopt.getopt(argv[1:], 'h',
                ['help',
                 'cfg=',
                 'delcache',
                 'skipscan',
                 'skipfetch',
                 'dir=',
                 'skipupdate'])

            for option, value in opts:
                if (option in ('-h', '--help')):
                    raise Exception()

                if (option in ('--cfg')):
                    self.defaults['cfg'] = value
                    print('Using config file [' + value + ']')

                if (option in ('--dir')):
                    self.defaults['mediadir'] = value
                    print('Music dir [' + value + ']')

                if (option == '--delcache'):
                    self.defaults['delcache'] = 'true'

                if (option == '--skipscan'):
                    self.defaults['skipscan'] = 'true'

                if (option == '--skipfetch'):
                    self.defaults['skipfetch'] = 'true'

                if (option == '--skipupdate'):
                    self.defaults['skipupdate'] = 'true'


            # end command line parsing


            # Validate the cfg file value and load it
            configfile = self.defaults['cfg']
            if (os.path.exists(configfile) and not os.path.isfile(configfile)):
                raise IOError('Config file already exists as a directory or other non-file type: ' + configfile)
            elif (not os.access(configfile, os.R_OK)):
                raise IOError('Could not open config file for reading: ' + os.path.abspath(configfile))
            config = configparser.SafeConfigParser(self.defaults)
            config.read(configfile)

            # Decode the various delim/sep fields, if the user had to enter a keyword for a char
            config.set(self.config_section, 'tagSep', self.decode_string(config.get(self.config_section, 'tagSep')))
            config.set(self.config_section, 'tagStartDelim', self.decode_string(config.get(self.config_section, 'tagStartDelim')))
            config.set(self.config_section, 'tagEndDelim', self.decode_string(config.get(self.config_section, 'tagEndDelim')))

            # Sanity check various settings
            mediadir = self.defaults['mediadir']
            if ( mediadir ):
                config.set(self.config_section, 'mediaDir', mediadir )
            else:
                mediadir = config.get(self.config_section, 'mediaDir')

            if (not os.path.exists(mediadir) or not os.path.isdir(mediadir) or not os.access(mediadir, os.R_OK)):
                raise IOError('Directory does not exist or you do not have access: ' + mediadir)

            cachefile = config.get(self.config_section, 'cacheFile')
            if (os.path.exists(cachefile) and not os.path.isfile(cachefile)):
                raise IOError('Cache file already exists as a directory or other non-file type: ' + cachefile)
            elif (not os.access(os.path.dirname(os.path.abspath(cachefile)), os.W_OK)):
                raise IOError('Could not open cachefile directory for writing: ' + cachefile)

            logFile = config.get(self.config_section, 'logFile')
            if (os.path.exists(logFile) and not os.path.isfile(logFile)):
                raise IOError('Log file already exists as a directory or other non-file type: ' + logFile)
            elif (not os.access(os.path.dirname(os.path.abspath(logFile)), os.W_OK)):
                raise IOError('Could not open log file directory for writing: ' + logFile)

            skipscan = config.getboolean(self.config_section, 'skipscan')
            if (skipscan and not os.path.exists(cachefile)):
                raise Exception('NOOP: Cannot bypass media file scanning if the cachefile is empty')

            for option in ['artistTagFields', 'trackTagFields', 'overwriteFields', 'forceOverwriteFields']:
                list =  map(str, config.get(self.config_section, option).lower().split(','))
                fields = set(map(str.strip, list ))
                self.validFieldSet(option, fields, self.allowedMediaWriteFields)

            for option in ['genreSort', 'groupingSort', 'commentSort']:
                list =  map(str,  config.get(self.config_section, option).lower().split(',') )
                sorts = set(map(str.strip, list))
                self.validFieldSet(option, sorts, self.allowedSortOptions)

            if (config.get(self.config_section, 'artistField').lower() not in ['artist', 'albumartist', 'both']):
                raise Exception('An invalid artistField value was specified: ' + config.get(self.config_section, 'artistField'))

            if (config.get(self.config_section, 'writeUntaggedTag').lower() not in ['artist', 'track', 'both', 'no']):
                raise Exception('An invalid writeUntaggedTag value was specified: ' + config.get(self.config_section, 'writeUntaggedTag'))

            return config

        except Exception as err:
            sys.stderr.write(os.path.basename(sys.argv[0]) + ': ' + str(err))
            sys.stderr.write(self.usage_message)
            sys.exit(-1)


    def validFieldSet(self, option, configSet, validSet):
        if (configSet is None or validSet is None or len(configSet) == 0):
            return
        if (len(configSet.difference(validSet)) > 0):
            raise Exception('One or more invalid fields were specified for option [' + option + ']: ' + str(configSet.difference(validSet)))

    def decode_string(self, str):
        if (common.isempty(str)):
            return ''

        if (str.lower() == 'space'):
            return ' '
        elif (str.lower() == 'semi'):
            return ';'
        elif (str.lower() == 'hash'):
            return '#'
        elif (str.lower() == 'percent'):
            return '%'
        else:
            return str

    def get(self, option):
        return self.config.get(self.config_section, option)

    def getint(self, option):
        return self.config.getint(self.config_section, option)

    def getfloat(self, option):
        return self.config.getfloat(self.config_section, option)

    def getboolean(self, option):
        return self.config.getboolean(self.config_section, option)


