import argparse
import os
import re
import subprocess

#a class to download amongst wikimedia's following dumps : wikidata, wikipedia, wikisource and wiktionary.
#This class is meant to be a library or executed through bash.
#Because of the structure of wikimedia's projects, wikidata is internally handeled distinctly than other projects.
class WikimediaDumpDownloader():

    #TODO(1): For usage as library, would idealy require an additionnal parameter of maximum weight in octets we want the WikimediaDump folder to be. Whenever the weight is reached it should delete progressivly starting from the oldest downloaded dump; starting from xml files and keeping the bz2 for ultimate necessity
    def __init__(self, path_root_project):

        if path_root_project ==  None:
            raise Exception("Specify path to root of dumps.")

        #url to json wikidata
        self.url_wikidata_dump = "https://dumps.wikimedia.org/wikidatawiki/entities/"
        #url to wikimedia projects excluding wikidata
        self.url_wiki_dumps = "https://dumps.wikimedia.org/backup-index.html"
        #url to wikidata
        self.prefix_url_wiki_dumps = "https://dumps.wikimedia.org/"
        #local path to the root of the project
        self.path_root_project = path_root_project
        #index summerizing dumps urls
        self.path_index_wikis_dumps = None

        #normalize path
        path_root_project=path_root_project.rstrip("/").rstrip("WikimediaDumps")+"/"

        #Checks if folder at path_root_project level exists, if not creates it.
        bool_root_exists_allready = False
        for dirname in os.listdir(path_root_project):
            if dirname == 'WikimediaDumps':
                bool_root_exists_allready = True

        self.path_root_project = path_root_project+"WikimediaDumps/"
        if not bool_root_exists_allready:
            os.mkdir(self.path_root_project)

        #projects

        #if the subfolders have not been created yet, creates them: project_name and temp
        bool_exists_allready = False
        bool_exists_allready2 = False
        bool_exists_allready3 = False
        bool_exists_allready4 = False
        bool_exists_allready5 = False

        for dirname in os.listdir(self.path_root_project):
            if dirname == "wikidata":
                bool_exists_allready = True
            if dirname == "wikipedia":
                bool_exists_allready2 = True
            if dirname == "wikisource":
                bool_exists_allready3 = True
            if dirname == "wiktionary":
                bool_exists_allready4 = True
            if dirname == ".temp":
                bool_exists_allready5 = True

        if not bool_exists_allready:
            os.mkdir(self.path_root_project+"wikidata")
        if not bool_exists_allready2:
            os.mkdir(self.path_root_project+"wikipedia")
        if not bool_exists_allready3:
            os.mkdir(self.path_root_project+"wikisource")
        if not bool_exists_allready4:
            os.mkdir(self.path_root_project+"wiktionary")
        if not bool_exists_allready5:
            os.mkdir(self.path_root_project+".temp")

        #HTML INDEXES: those files contain tables with links of urls to download 

        #if the subfolders have not been created yet, creates them: temp + index_name
        bool_exists_allready = False
        bool_exists_allready2 = False
        for dirname in os.listdir(self.path_root_project+".temp/"):
            if dirname == "index_wikidata":
                bool_exists_allready = True
            if dirname == "index_wikis":
                bool_exists_allready2 = True

        if not bool_exists_allready:
            os.mkdir(self.path_root_project+"/.temp/index_wikidata")
        if not bool_exists_allready2:
            os.mkdir(self.path_root_project+"/.temp/index_wikis")

    #In order to download indexes properly, we target their urls into an output folder and return the absolute path of the downladed index
    def _download_file_and_return_absolute_path(self, output_folder, target_url):
        
        #delete all previous files downloaded in the same emplacement
        for root, dirs, files in os.walk(output_folder):
            for filename in files:
                try:
                    os.remove(output_folder+filename)
                except(FileNotFoundError):
                    pass

        #download wikidata dump
        subprocess.run(["wget", target_url, "--directory-prefix="+output_folder])

        #file just downloaded has name we can deduct from target url
        downloaded_file_name = target_url.split("/")[-1]

        #return absolute path of this fils
        return output_folder+downloaded_file_name

    #downloads wikidata dump and keeps its absolute path in self.path_index_wikidata_dumps
    def _wget_url_wikidata_dump(self):
        self.path_index_wikidata_dumps = self._download_file_and_return_absolute_path(self.path_root_project+"/.temp/index_wikidata/", self.url_wikidata_dump)

    #downloads wikidata dump and keeps its absolute path in self.path_index_wikis_dumps
    def _wget_url_wiki_dumps(self):
        self.path_index_wikis_dumps = self._download_file_and_return_absolute_path(self.path_root_project+"/.temp/index_wikis/", self.url_wiki_dumps)

    #to get most recent versions of wikimedia project, update indexes 
    def update_index(self):
        self._wget_url_wikidata_dump()
        self._wget_url_wiki_dumps()

    #from html index file we extract a list of url which are urls to wrap-up pages of project for given langage (the url to final dump can be found in those pages)
    def _get_table_wikis(self, path_index_wikis_dumps):
        reg_extr_url = re.compile("^<li>[0-9 :\-]{20}<a href=\"([^\"]+)\"")
        list_href = []
        with open(self.path_index_wikis_dumps) as fp:
            for line in fp:
                matcher_reg_extr = reg_extr_url.search(line)
                if not matcher_reg_extr == None:
                    value_href = matcher_reg_extr.group(1)
                    list_href.append(value_href)
        return list_href

    #downloads dump of specified project and langage into adequate folder and unzips it
    def download_dump(self, project, langage=None):
        #will contain absolute path of downloaded file
        retour = ""
        #case 1: targeted project is wikidata
        if project=="wikidata":
            print("lang", langage)
            if langage:
                raise Exception("Wikidata is multilingual, should not target a language while extracting wikidata.")
            else:
                #delete previous version
                for root, dirs, files in os.walk(self.path_root_project+"wikidata"):
                    for filename in files:
                        os.remove(self.path_root_project+"wikidata/"+filename)
                subprocess.run(["wget", self.url_wikidata_dump+"/latest-all.json.bz2", "--directory-prefix="+self.path_root_project+"wikidata"])
                zip=""
                for root, dirs, files in os.walk(self.path_root_project+"wikidata"):
                    for f in files:
                        zip = f
                subprocess.run(["bzip2", "-d", self.path_root_project+"wikidata/"+zip])
                #return the file's path
                filename = zip[:-4]
                retour = self.path_root_project+"wikidata/"+filename

        #case 2: targeted project is not  wikidata
        else:
            if langage=="None":
                raise Exception("Specify language")
            #if index aren't present (first download), download them
            if not self.path_index_wikis_dumps:
                self.update_index()
            
            #build list of href to wrap-up pages found in index. Those contain information of project's name and langage
            list_href = self._get_table_wikis(self.path_index_wikis_dumps)

            #each url can be associated to a project using a regex on it
            project2prefix_suffixe_reg = {"wikipedia": re.compile("^(.+)(wiki)$"),"wikisource":re.compile("^(.+)(wikisource)$"),"wiktionary":re.compile("^(.+)(wiktionary)$")}

            #in those wrap-up pages the final dump to download is the first href of this form
            reg_page_dump_extractor = re.compile("<li class='file'><a href=\"([^\"]+)\">")
            
            #find which href to wrap-up page is required for download
            target_url = ""
            url_date = ""
            for link in list_href:
                #split url
                splitted=link.split('/')
                url_date = splitted[1]
                url_lg_project = splitted[0]
                #figure which project it links to using adequate regex
                for key in project2prefix_suffixe_reg.keys():
                    matcher_reg_extr = project2prefix_suffixe_reg[key].search(url_lg_project)
                    if not matcher_reg_extr == None:
                        #extract langage and project reading url
                        extracted_langage = matcher_reg_extr.group(1)
                        extracted_project = key
                        #if url fits required project and langage, download it as file into temp folder
                        if extracted_langage == langage and extracted_project == project:
                            url_project = matcher_reg_extr.group(2)
                            target_url = self.prefix_url_wiki_dumps+langage+url_project+"/"+url_date
                            #downloaded url is a wrap-up page for given project and langage. In this html page we find the url to targeted dump.
                            path_to_downloaded_url = self._download_file_and_return_absolute_path(self.path_root_project+".temp/", target_url)  
                            with open(path_to_downloaded_url) as fp:
                                for line in fp:
                                    matcher_url_dump = reg_page_dump_extractor.search(line)
                                    #breaks looping through file at first match
                                    if not matcher_url_dump == None:
                                        #href to final dump
                                        href = "https://dumps.wikimedia.org"+matcher_url_dump.group(1)
                                        #check if adequate langage folder exists in project folder
                                        bool_exists_allready = False
                                        for dirname in os.listdir(self.path_root_project+project):
                                            if dirname == langage:
                                                bool_exists_allready = True
                                        #if not we create it
                                        if not bool_exists_allready:
                                            os.mkdir(self.path_root_project+project+"/"+langage)
                                        #otherwise we delete previous dump inside it
                                        else:
                                            for root, dirs, files in os.walk(self.path_root_project+project+"/"+langage):
                                                for f in files:
                                                    filename = f
                                                    os.remove(self.path_root_project+project+"/"+langage+"/"+f)

                                        #download dump!
                                        subprocess.run(["wget", href, "--directory-prefix="+self.path_root_project+project+"/"+langage])
                                        
                                        #unzip dump
                                        zip = ""
                                        for root, dirs, files in os.walk(self.path_root_project+project+"/"+langage):
                                            for filename in files:
                                                zip = filename
                                                subprocess.run(["bzip2", "-d", self.path_root_project+project+"/"+langage+"/"+filename])
                                                
                                        #return the file's path (striping ".bz2" away)
                                        filename = zip.rstrip(".bz2")
                                        retour = self.path_root_project+project+"/"+langage+"/"+filename
                                        break

                            #remove all files from temp
                            for root, dirs, files in os.walk(self.path_root_project+".temp"):
                                for f in files:
                                    try:
                                        os.remove(self.path_root_project+".temp/"+f)
                                    except(FileNotFoundError):
                                        pass
        return retour

    #returns first xml at expected folder if dump exists, returns None otherwise
    def path_to_dump(self, project, langage=None):
        folder_path = self.path_root_project + project + "/" + langage
        for filename in os.listdir(folder_path):
            if filename.endswith(".xml"):
                return folder_path + "/" + filename
        return None

    #deletes folder for specified project and langage if exists
    def delete_dump(self, project, langage=None):
        if project=="wikidata":
            if not langage=="None":
                raise Exception("Wikidata is multilingual, should not target a language while extracting wikidata.")
            else:
                for root, dirs, files in os.walk(self.path_root_project+project):
                    for file in files:
                        os.remove(self.path_root_project+project+"/"+file)
        else:
            for root, dirs, files in os.walk(self.path_root_project+project):
                for dir in dirs:
                    if dir == langage:
                        for root, dirs, files in os.walk(self.path_root_project+project+"/"+langage):
                            for file in files:
                                os.remove(self.path_root_project+project+"/"+langage+"/"+file)
                        os.rmdir(self.path_root_project+project+"/"+langage)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='A partir de la racine donné en paramètre, permet de télécharger/supprimer un dump voulu')

    #root folder to main folder containing the dumps to be downloaded
    parser.add_argument("-r", "--root", help="Root for storing dumps. Compulsory parameter when allready has been specified", default="None")
    #one of wikidata, wikipedia, wikisource and wiktionary
    #required except if -u argument is used
    parser.add_argument("-p", "--project", help="Project targeted. Can be either 'wikidata', 'wikipedia', 'wikisource', 'wiktionary'.", default="None")
    #if project is wikidata, this argument is to be skipped
    parser.add_argument("-l", "--langage", help="Language targeted. (i.e. 'en', 'fr', 'de', 'es'...)", default="None")
    #if d request deletion of language in project
    parser.add_argument("-d", "--delete", help="Delete mode (takes no argument)", action='store_true', default="None")
    #use this arument to update index files pointing to dumps
    parser.add_argument("-u", "--update_index", help="Update html index files. Use it when you want to update the date of the dumps, don't if you want to keep the same date as previous session. (takes no argument)", action='store_true', default="None")

    '''#a feature we could integrate in future would be option to download dumps from n last days (history of modification)
    parser.add_argument("-t", "--time", help="télécharger les dumps des d derniers jours (default = latest).",  default='latest')
    '''
    args = parser.parse_args()

    update_index=args.update_index
    path_root_project = args.root
    project = args.project
    langage = args.langage
    delete = args.delete

    #try to upload from config file if none in cmd line arguments
    if path_root_project == "None":
        try:
            with open(".config") as fp:
                for line in fp:
                    path_root_project = line
        except(FileNotFoundError):
            raise ValueError("Please specify a path to command line arguments (-r)")

    #throw error if still no path
    if path_root_project == "None":
        raise ValueError("Please specify a path to command line arguments (-r)")

    #unless -u is used, -p argument is required
    if not update_index == "None" and project == "None":
        raise ValueError("Please specify a project to command line arguments (-p). Can be either 'wikidata', 'wikipedia', 'wikisource', 'wiktionary'.")


    wikimedia_dumps = WikimediaDumpDownloader(path_root_project)
    config_file = open(".config", "w")
    config_file.write(path_root_project)
    config_file.close()

    #throw error if update-index is used uncorrectly
    if not update_index == "None":
        if not project == "None":
            raise ValueError("Do not specify project if updating indexes.")
        elif not langage == "None":
            raise ValueError("Do not specify languages if updating indexes.")
        elif not delete == "None":
            raise ValueError("Do not specify deletion if updating indexes.")
        else:
            wikimedia_dumps.update_index()
    else:
        if delete == "None":
            path = wikimedia_dumps.download_dump(project, langage)
        else:
            wikimedia_dumps.delete_dump(project.lower(), langage.lower())
