# -*- coding: utf-8 -*-

import os
import shutil
import md5
import ConfigParser
import copy
import StringIO

class ppHashObject():
  '''
    Base Hash Class for Caching.
  '''

  def __init__( self ):
    '''
      Initialize self.Finalized with False, self.Digest with None and
      self.Sequence with a StringIO Object.
    '''
    self.Finalized = False
    self.Digest = None
    self.Sequence = StringIO.StringIO()

  def hexDigestLen( self ):
    '''
      Return the Digest Length (where Digest is an Hexadecimal string).
    '''
    pass

  def finalize( self ):
    '''
      Finalize the hash and set the resulting hexadecimal digest in self.Digest.
      Further Update calls will result in Exceptions.
    '''
    if self.Finalized:
      raise Exception( 'finalize can be called only once' )
    else:
      self.Finalized = True

  def update( self, argstr ):
    '''
      Update the hash with a string, after finalization this will result
      in an Exception.
    '''
    if not self.Finalized:
      self.Sequence.write(argstr)
    else:
      raise Exception( 'update after finalization is not allowed' )

  def clone( self ):
    '''
      Duplicate the current hash Object or the Digest when finalized.
    '''
    pass

  def __del__( self ):
    '''
      Close and Destroy the Sequence Object.
    '''
    self.Sequence.close()

class ppMD5HashObject(ppHashObject):
  '''
    Hash Class for MD5 Hashing Algorithm
  '''
  def __init__( self ):
    '''
      Initialize self. see ppHashObject.__init__
      Initialize additional md5 Object.
    '''
    ppHashObject.__init__(self)
    self.md5o = md5.new()

  def hexDigestLen( self ):
    '''
      Return md5 hexadecimal Digest Length.
    '''
    return self.md5o.digest_size*2

  def finalize( self ):
    '''
      Call ppHashObject.finalize and set self.Digest with the current
      md5 hexadecimal String for the Hash.
    '''
    ppHashObject.finalize( self )
    self.Digest = self.md5o.hexdigest()

  def update( self, argstr ):
    '''
      Call ppHashObject.update and update the md5 Object.
    '''
    ppHashObject.update( self, argstr )
    self.md5o.update( argstr )

  def clone( self ):
    ''' 
      Create and return a new ppMD5HashObject, which either contains the
      md5 Object and a Sequence copy (not finalized) or the Digest (finalized) 
      and a Sequence reference.
    '''
    res = ppMD5HashObject()
    if self.Finalized:
      res.Finalized = True
      res.Digest = self.Digest
      res.Sequence = self.Sequence
    else:
      res.md5o = self.md5o.copy()
      res.Sequence = copy.deepcopy( self.Sequence )
    return res

class ppFSFileCacheEntry():
  '''
   Projectplan Filesystem Cache Entry Object.
   Instances of this Class are returned by ppFSFileCache and support
   adding multiple files, identified by suffixes, for a given Cache hit/miss. 
   (Cache entry)
  '''

  def __init__( self, hobj, hpathfile ):
    '''
      Initialize the Table of suffixes for the current Entry (empty for misses)
      and set self.Exists which is True for Cache Hits, otherwise False.
      Two special files are created for an Entry:
        * <hexdigest> which saves a suffix list for wiping/access
        * <hexdigest>sequence which holds the full sequence for
          the resulting hash and is used for collision test
      The entry will be wiped on Collision and self.Exists returns False.

      Remark: the Hash Object must be alive until the last write! 
              It can be deleted afterwards.
    '''
    self.idfile = hpathfile
    self.hobj = hobj
    self.Exists = os.path.isfile( hpathfile )
    self.entrytab = ConfigParser.RawConfigParser()
    if self.Exists:
      self.entrytab.read( self.idfile )
      # collision test
      colliding = True
      if os.path.isfile( self.idfile+'sequence' ):
        f = open( self.idfile+'sequence', 'r' )
        try:
          eseq = f.read()
          colliding = not ( eseq == self.hobj.Sequence.getvalue() )
        finally:
          f.close()
      # collision or non existing sequence file - wipe and reset entry
      if colliding:
        try:
          self.wipe()
        except Exception, e:
          raise Exception( 'Cache Entry wiping failed with Exception: "%s"' % str(e) )
        self.Exists = False

  def entryExists( self, suffix ):
    '''
      Check wether the suffix exists in the entry table or not.
    '''
    return self.entrytab.has_section( suffix )

  def getFileName( self, suffix ):
    '''
      Build an absolute File Name for the File.
    '''
    return self.idfile+suffix

  def getFile( self, suffix, nofobj ):
    '''
      Get either a new Entry File for a new suffix ( write only ) or the
      existing File for an existing suffix (read/write).
      if suffix is empty or 'sequence', this will raise an Exception since
      those two files are special and used internally.
    '''
    if ( len(suffix)>0 ) or ( suffix != 'sequence' ):
      fn = self.getFileName( suffix )
    else:
      raise Exception( 'attempted internal file override' )
    if self.entryExists( suffix ):
      if not nofobj:
        return open( fn, mode='rw' )
    else:
      self.entrytab.add_section( suffix )
      if not nofobj:
        return open( fn, mode='w' )

  def wipe( self ):
    '''
      Delete each File, listed in the suffix Table and reset the
      cache Entry.
    '''
    if self.Exists:
      for s in self.entrytab.sections():
        if os.path.isfile( self.getFileName( s ) ):
          os.unlink( self.getFileName( s ) )
      self.entrytab = ConfigParser.RawConfigParser()

  def write( self ):
    '''
      Write the Cache Entry suffix Table and the HashObject Sequence.
    '''
    try:
      # write sequence for collision test
      f = open( self.idfile+'sequence', 'w' )
      try:
        f.write( self.hobj.Sequence.getvalue() )
        f.flush()
      finally:
        f.close()
      # write id file
      f = open( self.idfile, 'w' )
      try:
        self.entrytab.write( f )
        f.flush()
      finally:
        f.close()
    except Exception, e:
      raise Exception( 'Cache Entry writing failed with Exception: "%s"' % str(e) )

class ppFSFileCache:
  '''
    Cache Class for Filesystem/Fileobject based Cache Entries.
  '''

  def __createNonExisting( self, path ):
    '''
      Create Non-Existing pathes with Read/Write/Enter access for
      the current User.
    '''
    if not os.path.isdir( path ):
      os.makedirs( path, mode=0700 )

  def __buildHashPath( self, hashobject, dictlvl ):
    '''
      Build the Path from rootdir and Hash Digest
    '''
    if dictlvl >= hashobject.hexDigestLen():
      dictlvl = hashobject.hexDigestLen()
    elif dictlvl <= 0:
      return self.rootdir
    return os.path.join( self.rootdir, hashobject.Digest[0:dictlvl] )

  def __init__( self, rootdir, subrootdir=None, dictlvl=2 ):
    '''
      Initialize the Cache Pathes.
    '''
    self.root = os.path.normpath( rootdir )
    if subrootdir != None:
      self.subroot = os.path.normpath( subrootdir )
      if os.path.isabs( self.subroot ):
        raise Exception( 'subroot overriding cache rootpath!' )
      self.rootdir = os.path.join( self.root, self.subroot )
    self.dictlevel = dictlvl
    self.__createNonExisting( self.rootdir )

  def urlCacheFile( self, absname, subroot=False ):
    '''
	  Return relative Cache File (see relCacheFile), and
	  replace every '\' with '/'
	'''
    rel = self.relCacheFile( absname, subroot )
    if rel!=None:
      rel = rel.replace( '\\', '/' )
    return rel

  def relCacheFile( self, absname, subroot=False ):
    '''
      Return the normalized, relative Path for a Path in the Cache.
      Depending on subroot, it is relative from the Cache root
      or the subroot. None is returned when absname is not in the 
      Cache/Subroot Path.
      (no check for existence of the file/path)
    '''
    absname = os.path.normpath( absname )
    if subroot:
      if absname.startswith( self.rootdir ):
        return absname[len(self.rootdir):]
    else:
      if absname.startswith( self.root ):
        return absname[len(self.root):]
    return None

  def newHashObject( self ):
    '''
      Return a new HashObject. Currently this is an Instance of ppMD5HashObject.
    '''
    return ppMD5HashObject()

  def lookupEntry( self, hashobject, nocreate ):
    '''
      Lookup an Entry. If nocreate is set, this will return
      None for Misses (and collisions), 
      otherwise a ppFSFileCacheEntry Instance is returned for
      both Misses and Hits.
    '''
    hpath = self.__buildHashPath( hashobject, self.dictlevel )
    hpathfile = os.path.join( hpath, hashobject.Digest )
    res = None
    if os.path.isdir( hpath ):
      if nocreate:
        if not os.path.isfile( hpathfile ):
          return None
      res = ppFSFileCacheEntry( hashobject, hpathfile )
    else:
      if nocreate:
        return None
      self.__createNonExisting( hpath )
      res = ppFSFileCacheEntry( hashobject, hpathfile )
    # check if exists was reset due to collisions
    if nocreate and ( not res.Exists ):
      return None
    return res

  def wipe( self, onlysubroot=False ):
    '''
      Wipe the entire Cache when onlysubroot is set or all entries
      in the subroot.
    '''
    try:
      if onlysubroot:
        shutil.rmtree( self.rootdir )
      else:
        shutil.rmtree( self.root )
      self.__createNonExisting( self.rootdir )
    except Exception, e:
      raise Exception( '''Cache wiping failed with Exception: "%s"''' % str(e) )
