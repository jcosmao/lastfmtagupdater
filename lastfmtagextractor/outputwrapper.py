#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
    lastfmtagextractor/outputwrapper.py
    
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

from Tkinter import *
from .config import LastFM_Config
import threading
import Queue
import os
import codecs

'''
This helper class facilitates output to either the console or a GUI. If GUI mode is selected, the window will open
as a background thread.
'''
class OutputWrapper(threading.Thread):

    config = None      
    useGui = False
    root = None
    text = None
    logFileHandle = None
    killExceptionRaised = False
    
    def __init__(self, config):
        self.config = config
        if (self.config.getboolean('gui')):
            self.logNormal('Spawning output window')
            self.useGui = True
            threading.Thread.__init__(self)
            self.start()
            
        logFile = self.config.get('logFile')
        if (logFile is not None):
            self.logFileHandle = codecs.open(logFile, 'w+', 'utf_8_sig')

            
    def run(self):
        if (not self.useGui):
            return

        self.queue = Queue.Queue()
    
        root = Tk()
        root.title('LastFM Tag Extractor')
        
        scrollY = Scrollbar(root)
        text = Text(root)
        
        text.focus()
        scrollY.pack(side=RIGHT, fill=Y)
        text.pack(side=LEFT, fill=BOTH, expand=1)
        scrollY.config(command=text.yview)
        text.config(yscrollcommand=scrollY.set)
                
        root.update()
        
        self.root = root
        self.text = text
        self.root.after(50, self._task)
        self.root.mainloop()

        
    def _task(self):        
        try:
            while True:
                msg = self.queue.get_nowait()
                if (msg is None):
                    self.text.delete(1.0, END)
                else:
                    self.text.insert(END, msg + '\n')
                    self.root.update()
                self.text.see(END)
        except Queue.Empty:
            pass        
        self.root.after(10, self._task)

          
    def logNormal(self, msg):
        self._logHelper(msg, sys.stdout)

        
    def logError(self, msg):
        self._logHelper(msg, sys.stderr)


    def _logHelper(self, msg, consoleStream):    
        
        if (self.logFileHandle is not None):
            self.logFileHandle.write(msg + '\n')
            self.logFileHandle.flush()

        if (self.useGui and not self.killExceptionRaised):
            # Window close signals only cascade to the main thread on a log write. Aside from me
            # being a bit lazy, it also facilitates having well-known termination points in the main
            # code, which facilitated the partial-save feature of the fetch stage.  
            # for my laziness here. =) It            
            if (not self.isAlive()):
                self.killExceptionRaised = True
                raise KillRequestException('Output window closed, killing program')
            self.queue.put(msg, True)
        else:
            if (isinstance(msg, unicode)):
                msg = msg.encode('latin1', 'replace')
            try:
                print >> consoleStream, msg
            except:
                print >> consoleStream
                pass
            consoleStream.flush()

        
    def close(self):
        if (self.logFileHandle is not None):
            self.logFileHandle.close()                        


''' Used by the GUI mode to signal a close request '''
class KillRequestException(Exception):
    pass
