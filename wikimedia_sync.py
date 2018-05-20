#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-

"""
 wikimedia_sync.py

 usage : ./wikimedia_sync.py <config_file.yml>

 author : Florent Kaisser

 Copy WikiMedia pages from a Wiki source (ex : a Wikipedia) to a Wiki 
 destionation (like a third-party wikis).

 A config file given in args contain name of pages and categories to 
 synchronize, and Wiki source and destination.

 IMPORTANT : We must have user-password.py and user-config.py in same 
 directory of this script to congigure pywikibot. 
 See : https://www.mediawiki.org/wiki/Manual:Pywikibot/user-config.py
"""

# For use WikiMedia API
from pywikibot import Site,Page,Category,logging

# For load YAML file config
import sys
import yaml

# We use typing 
from typing import List
PageList = List[Page]


def syncPages(src : Site, dst : Site, pages : PageList) -> int: 
  """Synchronize wiki pages from src to dst
    
    return the number of synchronized pages succes
  """
  
  nbSyncPage = 0
  nbPage = len(pages)
  
  #disable mechanics to slow down wiki write
  dst.throttle.maxdelay=0
  
  for i,p in enumerate(pages):
    title = p.title()
    print ("== %i/%i Sync %s " % (i+1,nbPage,title))
    
    # create a new page on dest wiki
    newPage = Page(dst, title)
    
    if(newPage.exists()):  
      print ("Page %s exist" % title)
    elif(newPage.site == dst):
    #elif(newPage.canBeEdited()):
      # copy the content of the page
      newPage.text = p.text
      
      # commit the new page on dest wiki
      if (dst.editpage(newPage)):
        nbSyncPage = nbSyncPage + 1
      else:
        print ("Error on saving page %s" % title)
    else:
      print ("Page %s not editable on dest" % title)

  return nbSyncPage
  
def syncPagesAndCategories(
  srcFam : str, srcCode : str, dstFam : str, dstCode : str, 
  pagesName : List[str], categoriesName : List[str]) -> int :
  """Synchronize wiki pages from named page list
        and named categories list
    
    return the number of synchronized pages succes
  """  
  
  # configure sites
  siteSrc = Site(fam=srcFam,code=srcCode)
  siteDst = Site(fam=dstFam,code=dstCode)
  
  pages = []
  
  if( pagesName ):
    # pages from their names
    pages += [ Page(siteSrc, name) for name in pagesName ]
  
  if( categoriesName ):
    # retrieve all pages from categories
    categories = [ Category(siteSrc,name) for name in categoriesName ]
    for cat in categories :
      pages += [ Page(siteSrc, cat.title()) ]
      print ("Retrieve pages from " + cat.title())
      # add pages of this categorie to pages list to sync
      pages += list( cat.articles() )
    
  templates = []
  for p in pages :
    tplt = list(p.itertemplates())
    nbTplt = len(tplt)
    if(nbTplt > 0):
      print ("Add %i templates of %s" % (nbTplt, p.title()))
      templates += tplt
      
  references = []    
  for t in set(templates) :
    ref = list(t.itertemplates())
    nbRef = len(ref)
    if(nbRef > 0):
      print ("Add %i reference of %s" % (nbRef, t.title()))
      references += ref      

  uniqReference = list(set(references + templates))
  
  return syncPages(siteSrc, siteDst, pages + uniqReference )

######################################
# Main parts

def main(fileconfig):
  with open(fileconfig, 'r') as ymlfile:
    cfg = yaml.load(ymlfile)
    src = cfg['sites']['src']
    dst = cfg['sites']['dst']
    pages = cfg['pages']
    cats = cfg['categories']
    
    nb = syncPagesAndCategories(src['fam'], src['code'], dst['fam'], 
      dst['code'], pages, cats)
      
    print ("%i pages synchronized" % nb)

if __name__ == "__main__":
  if(len(sys.argv)>1):
    main(sys.argv[1])
  else:
    print ("Usage : ./wikimedia_sync.py <config_file.yml>")
  

######################################
# Test parts

def test() -> bool:
  siteSrc = Site(fam="wikipedia",code="en")
  siteDst = Site(fam="kiwix")
  pages = [Page(siteSrc,"New_York_City"), 
           Page(siteSrc,"Paris"), 
           Page(siteSrc,"Geneva") ]
           
  simpleTest = (syncPages(siteSrc, siteDst, pages) == 3)
  
  pagesName = ["The_Handmaid's_Tale_(TV_series)","Black_Mirror","The_Wire"]
  catsName = ["Cuba","Lille"]
  
  mainTest = ( syncPagesAndCategories("wikipedia","en","kiwix","kiwix",
                pagesName, catsName ) == 27)
  
  return simpleTest and mainTest

#if __name__ == "__main__":
#  if test():
#    print ("Test OK")
#  else:
#    print ("Test Error")
