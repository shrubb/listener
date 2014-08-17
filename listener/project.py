"""Utility functions for processing source-code directories into vocabularies"""
from . import tokenizer, ipatoarpabet
import logging, traceback, os, subprocess
log = logging.getLogger( __name__)


def iter_translated_lines( files, working_context ):
    parser = tokenizer.Tokenizer( working_context.dictionary_cache )
    for filename in files:
        log.info('Translating: %s', filename )
        lines = open( filename ).readlines()
        try:
            yield parser( lines )
        except Exception as err:
            log.error( 'Unable to translate: %s\n%s', filename, traceback.format_exc())
            continue 
            
def iter_unmapped_words( translated, working_context ):
    unmapped = set()
    all_words = set()
    for line in translated:
        all_words |= set(line)
    log.info( 'Checking %s words for transcriptions', len(all_words))
    transcriptions = working_context.transcriptions( sorted(all_words) )
    for word,arpa in transcriptions.items():
        if not arpa:
            unmapped.add( word )
    log.info( '%s words unmapped', len(unmapped))
    for word in unmapped:
        possible = ipatoarpabet.translate( word )
        for i,pron in enumerate( possible ):
            yield word,pron

def get_project_files( directory ):
    """Retrieve all files checked into a source-code project"""
    if os.path.exists( os.path.join( directory,'.git') ):
        files = subprocess.check_output(
            ['git','ls-files'],
        )
        files = [ 
            os.path.join( directory, f ) 
            for f in files.splitlines() 
            if f.strip() 
        ]
    elif os.path.exists( os.path.join( os.path.directory, '.bzr') ):
        files = subprocess.check_output(
            ['bzr','ls','--recursive','--from-root','--versioned'],
        )
        files = [ 
            os.path.join( directory, f ) 
            for f in files.splitlines() 
            if f.strip() 
        ]
    elif os.path.exists( os.path.join( os.path.directory, '.hg') ):
        files = [
            [ x[6:].strip() ]
            for x in subprocess.check_output(
                ['hg','manifest']
            ).read().splitlines()
            if x[6:].strip()
        ]
    else:
        files = []
        def visit( path, subdirs, files ):
            files.extend( [
                os.path.join( directory, path, file )
                for file in files 
            ])
    return files

def get_python_files( directory ):
    """Given a vcs directory, list the checked-in python files"""
    return [
        name for name in get_project_files( directory )
        if (
            name.endswith( '.py' ) or 
            name.endswith( '.pyx' ) or 
            name.endswith( '.pyw' ) or 
            name.endswith( '.py2' ) or 
            name.endswith( '.py3' )
        )
    ]
