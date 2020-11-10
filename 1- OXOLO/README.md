# WikimediaDumpDownloader

This code offers the possibility to download dumps for Wikidata, Wikipedia, Wiktionary and Wikisource by language.

Before anything, choose yourself a root folder in which to load all wikimedia projects.

Once downloaded, the dump of a wikimedia project gets stored in that location, in sub path :

    root/wiki***/language/$DUMP$

(except for wikidata project which already is multilingual so doesn't have a language folder)

on top of those 4 projects is a hidden folder : .temp which is created in that root to temporarily containing the index html files listing available dumps to download for each projects.

This code can either be run as command line or refered to as a library

1) Command line parameters are :

    * -r <...> specify root folder in which to store dumps (compulsory parameter when allready has been specified previously : gets stored in the .config)
    * -p <...> wikimedia projet to download. Can be either 'wikidata', 'wikipedia', 'wikisource', 'wiktionary'
    * -l <...> language (i.e. 'en', 'fr', 'de', 'es'...)
    * -d delete mode (alternative mode : delete dump and path specific to it)
    * -u update-index (updates the html index pointing to dumps, use this argument alone when you want to refresh the indexes to dumps available to download)

*usage*:

    #create a source folder for the project
    python3 WikimediaDumpDownloader.py -r "."

    #update indexes
    python3 WikimediaDumpDownloader.py -u

    #download projects
    python3 WikimediaDumpDownloader.py -p wikidata
    python3 WikimediaDumpDownloader.py -p wiktionary -l fr

    #do all above in one step:
    *python3 WikimediaDumpDownloader.py -r "." -p wiktionary -l fr*
    ...

    #delete projects
    python3 WikimediaDumpDownloader.py -r -p wikidata -d
    python3 WikimediaDumpDownloader.py -p wiktionary -l fr -d
    ...


2) as a library:

*usage*:

    import WikimediaDumpDownloader

    #create a source folder for the project
    wb = WikimediaDumpDownloader(<path_root_project>)

    #update indexes
    wb.update_index()

    #download projects
    wb.download_dump("wikidata") #download wikidata into it
    wb.download_dump("wikipedia", "fr") #download wikipedia into it

    #delete projects
    wb.delete_dump("wikidata")
    wb.delete_dump("wikipedia", "fr") 
