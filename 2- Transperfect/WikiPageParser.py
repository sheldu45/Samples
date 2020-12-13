import re
import argparse
import json
import math
import sys
import os
import progressbar

from lxml import etree

class InputError(Exception):
    """Exception raised for errors in the input. Those can be used to improve wikimedia projects.

    Attributes:
        localization -- localization of the error occurred (wiki page)
        expression -- input expression in which the error occurred (~ lign)
        message -- explanation of the error
    """

    def __init__(self, localization, expression, message):
        self.localization = localization
        self.expression = expression.replace("\n", "\\n")
        self.message = message

    def __str__(self):
        return "".join([self.message, "\t",  self.localization, "\t", self.expression, "\n"])


#A general parser for wiki pages (from Wiktionary or Wikipedia), converts html dumps into its equivalent dict structure, respecting nested structure of its sections.
'''
page_title: {
    'content': "..."
    'title_1': {
        'content': "..."
        'sub_title_1': {
            ...
        }
        ...
    }
    'title_2': {
        ...
    }
    ...
}
'''
#Parsing methods can be given through functional arguments used to extract datas from content section on-the-go.
#A couple of generic methods for data extraction in wikis are given.
class WikiPageParser:

    """constructor
    
    Args:
    ign (bool): if set to true, 'ignore' out of range errors during title normalization. Such errors will than be printed in error file, instead of stoping execution, and title won't be normalized.
    targeted_title (str) : in order to build the regex, we need to know the titles of bracketed expressions which we want to extract
    print_to_std (bool) : do we want the output also printed to terminal
    """
    def __init__(self, ignore=True, targeted_title=None, print_to_std=False):
        #a couple of regular expressions which will be used by the parser
        #... to detect sections and titles
        self.regex_potential_section_title = re.compile("(\s*=={,7}\s*.*\s*[^=]=={,7}\s*)\n")
        self.regex_section_title_group_matcher = re.compile("(=={,7})\s*(.*\s*[^=])(=={,7})\s*$")
        #... to detect bracketed expressions
        self.curly_bracketed_expr = re.compile("{{([^}])*}}")
        self.square_bracketed_expr = re.compile("\[\[([^\]])*\]\]")
        #...to detect bracketed expression with title
        conc_reg = targeted_title+"\|" if targeted_title else ""
        self.titled_curly_bracketed_expr = re.compile("{{"+conc_reg+"([^}])*}}")
        self.titled_square_bracketed_expr = re.compile("\[\["+conc_reg+"([^\]])*\]\]")
        self.ignore = ignore
        self.print_to_std = print_to_std

    """this function reccursively transforms a wiki page into its equivalent dictionary form
    
    Args:
    str_section (str): full page or section
    context_titles (list(str)): succesion of titles in which current section is nested
    section_titles_normalisation_funct (funct): function str -> str applied on section titles to normalize them
    content_extraction_funct (funct): function  (str:content, list_str:titles_context) -> printable_object ; applied on values of "content" keys with information of titles context in which section is nested
    add_empty_contents (bool) : set to True if you want to keep (key, value) pairs for "content" key when value is empty
    content_attribute_name (str) : if you want "content" section to be named differently change this argement
    default_attribute_name (str) : Default name of title variables when none found
    section_level (int) : reccursive arguement, not to be set externally  (default : 1)

    Returns:
    dictionary: a dictionary representing the content of the wiki
    """
    def toDict(self, str_section, context_titles, section_titles_normalisation_funct, content_extraction_funct, add_empty_contents, content_attribute_name, default_attribute_name, section_level=1):
        local_context_titles = context_titles.copy()

        #page is splitted over potential titles
        splitted_page = self.regex_potential_section_title.split(str_section)
        parsed_dict = {}

        #initialisation of reccurence
        if len(splitted_page) == 1:
            content = content_extraction_funct(str_section, local_context_titles)
            if not(len(content) == 0 and not add_empty_contents):
                if content_attribute_name == "":
                    content_attribute_name = default_attribute_name
                parsed_dict[content_attribute_name] = content
            return parsed_dict

        #"content" for this level of reccursion
        header = splitted_page.pop(0)
        if header:
            content = content_extraction_funct(header, local_context_titles)
            if not(len(content) == 0 and not add_empty_contents):
                if content_attribute_name == "":
                    content_attribute_name = default_attribute_name
                parsed_dict[content_attribute_name] = content

        i = -1
        current_title = ""
        last_title = ""
        last_sub_section = ""
        #looping through splits
        for split in splitted_page:
            i+=1
            #split is a potential title
            if i%2 == 0:
                #matches and groups from titles
                section_title_group_matcher = self.regex_section_title_group_matcher.search(split)
                whole_match = section_title_group_matcher.group(0)
                left_equals = section_title_group_matcher.group(1)
                right_equals = section_title_group_matcher.group(3)
                
                #unexpected syntax error in page
                if not left_equals == right_equals:
                    raise InputError("/".join(context_titles), whole_match, "unbalanced_equals")

                #title is of expected level for this reccursion step
                if len(left_equals) == section_level + 1:
                    #extract title group from regex
                    last_title = current_title
                    current_title = section_title_group_matcher.group(2)
                    #normalization function outputs a set, title normalization should be of only one element
                    try:
                        set_output_normalization_function = section_titles_normalisation_funct(current_title, local_context_titles)
                        if len(set_output_normalization_function) > 1:
                            #TODO(2) find a better exception type
                            raise Exception(str("normalization function for title unexpectedly returned a set of more than 1 element : ", set_output_normalization_function))
                        current_title = set_output_normalization_function.pop()
                    except(InputError):
                            current_title = current_title

                    #add to parsed_dict last parsed sub section if exists
                    if last_sub_section:
                        local_context_titles.append(last_title)
                        #adding parsed section to dict
                        if last_title == "":
                            last_title = default_attribute_name
                        parsed_dict[last_title] = self.toDict(last_sub_section.rstrip("\n"), local_context_titles, section_titles_normalisation_funct, content_extraction_funct, add_empty_contents, content_attribute_name, default_attribute_name, section_level+1)
                        local_context_titles.pop(-1)
                        last_sub_section = ""
                #title is of a subtitle
                elif len(left_equals) > section_level + 1:
                    last_sub_section += "\n"+whole_match+"\n"
            #split is a section
            else:
                last_sub_section += split+"\n"

        #adding last parsed section to dict
        local_context_titles.append(current_title)
        parsed_dict[current_title] = self.toDict(last_sub_section.rstrip("\n"), local_context_titles, section_titles_normalisation_funct, content_extraction_funct, add_empty_contents, content_attribute_name, default_attribute_name, section_level+1)
        local_context_titles.pop(-1)

        return parsed_dict



    """this function parses all wiki pages from an xml dump 
    
    Args:
    lang (str): language of wiki dump
    path_to_dump (str): path to dump that is to be parsed
    path_to_output (str): path to output file which will contain the json resulting from the parsing
    path_to_errors (str): path to file which will contain syntax errors detected during the parsing
    section_titles_normalisation_funct (funct): function str, list(str) -> str applied on section titles to normalize them (default is left unchanged)
    content_extraction_funct (funct): function  (str:content, list_str:titles_context) -> printable_object ; applied on values of "content" keys with information of titles context in which section is nested (default is left unchanged) 
    add_empty_contents (bool) : set to True if you want to keep (key, value) pairs for "content" key when value is empty (default is set to False)
    content_attribute_name (str) : if you want "content" section to be named differently change this argement (default : "content")
    refresh_bar_frequency (int) : number of parsed pages after which progress bar is refreshed 
    default_attribute_name (str) : Default name of title variables when none found (default 'unnamed')
    
    Returns:
    None
    """
    def parse_dump(self, lang, path_to_dump, path_to_output, path_to_errors, section_titles_normalisation_funct=lambda expr, context_titles: expr, content_extraction_funct=lambda content, context_titles : content, add_empty_contents=False, content_attribute_name="content", default_attribute_name="unnamed", refresh_bar_frequency = 100000):
        
        def strip_tag_name(t):
            t = elem.tag
            idx = k = t.rfind("}")
            if idx != -1:
                t = t[idx + 1:]
            return t

        #init ouput files handler
        out = open(path_to_output, "w")
        errors = open(path_to_errors, "w")

        #files headers
        if self.print_to_std:
            print("[")
        out.write("[\n")
        errors.write("\t".join(["error", "localization", "expression"])+"\n")

        #retrieve size of dump for progressbar and init it (if output isn't printed in terminal)
        bar = None
        if not self.print_to_std:
            dump_total_size = os.path.getsize(path_to_dump)
            bar = progressbar.ProgressBar(maxval = dump_total_size, widgets=[progressbar.Bar("=", '[', ']'), ' ', progressbar.Percentage(), " ", progressbar.ETA()])
        
        #keep unexpected error messages to print in std after parse
        unexpected_errors = []

        #loop through wiki pages
        page_id = None
        i = 0
        if bar:
            bar.start()
        with open(path_to_dump, 'rb') as f:
            event_context = etree.iterparse(f, events=('end', ))
            try:
                for event, elem in event_context:
                    tname = strip_tag_name(elem.tag)
                    i += 1
                    if event == 'end':
                        #new page to parse
                        if tname == 'text':
                            page = etree.tostring(elem, encoding = "unicode", method='text')
                            context_titles = [title]
                            try:
                                parsed_page = self.toDict(page, context_titles, section_titles_normalisation_funct, content_extraction_funct, add_empty_contents, content_attribute_name, default_attribute_name)
                                full_parsed_page = {'id':page_id, 'ns':ns, 'content':parsed_page}
                                page_id = None
                                to_print = "".join(['"', title, '": ', self.pretty_str(full_parsed_page), ","])
                                if self.print_to_std:
                                    print(to_print)
                                out.write(to_print)
                            except(InputError):
                                e = sys.exc_info()[1]
                                errors.write(str(e))
                        #title to parse
                        elif tname == 'title':
                            title = elem.text
                        #ns
                        elif tname == 'ns':
                            ns = elem.text
                        #id (of page, not to be overritten when parsing id of user)
                        elif tname == 'id' and not page_id:
                            page_id = elem.text

                    elem.clear()
                    if bar and i % refresh_bar_frequency == 0:
                        bar.update(f.tell())

            except(etree.XMLSyntaxError):
                e = sys.exc_info()[1]
                unexpected_errors.append(str(e))
                event_context.next()
        if bar:
            bar.finish()

        #print error messages
        for e in unexpected_errors:
            print(e)

        #files footers
        if self.print_to_std:
            print("]")
        out.write("[\n")

    """This function normalizes a bracketed expression either from a function indicating which indexes to extract, or from a regular expression retrieving all values of a "var = val" assignement, where var matches the regular expression. Note that even if the function is called normalization, it can be used to extract a part of the bracketed expression.
    
    Args:
    expr (str): expression we want to normalize
    context_titles (list(str)): succesion of titles in which current section is nested
    regex_attr_or_funct_splitted2elems (funct or str): 
        either function (list(str), list(str)) -> list(str) ; applied on a splitted string, gives a list of elements to return
        or regex_attr (str): regex to be applied on each var of "var = val" assignements to know which values to extract
    post_processing_funct (function) : function  str, list(str) -> str ; after extraction of relevent substring, which function is to be applied for postprocessing
    brackets (couple(str)) : a couple indicating which is left and right bracket for expression


    Returns:
    set : a set of string object which are the valid normalized strings for the bracketed expression
    """
    def norm_bracket_expr(self, expr, context_titles, regex_attr_or_funct_splitted2elems, post_processing_funct=lambda expr, context_titles : expr, brackets = ("{{","}}")):
        
        """Both form of normalization requires the same init steps to split the expression correctly
        Args:
        expr (str): expression we want to normalize
        brackets (couple(str)) : a couple indicating which is left and right bracket for expression

        Returns:
        list : a splitted form of the expression
        """
        def init_norm(expr, brackets):
            left_bra = brackets[0]
            right_bra = brackets[1]

            #assign correct reg expr
            if brackets[0] == "{{" and brackets[1] == "}}":
                bracketed_expr = self.curly_bracketed_expr
            elif brackets[0] == "[[" and brackets[1] == "]]":
                bracketed_expr = self.square_bracketed_expr
            else:
                bracketed_expr = re.compile("".join([left_bra, "([^}])*", right_bra]))

            #change expr to bracketed expression
            matcher = bracketed_expr.search(expr)
            #if there is no bracketed expression, expr is left unchanges
            if matcher :
                expr = matcher.group(0)
            else:
                raise InputError("/".join(context_titles), expr, "expected bracketed expression")

            #strip brackets
            expr = expr.rstrip(right_bra).lstrip(left_bra)
            #split over pipes
            splitted = expr.split("|")

            return splitted
            
        """normalizes a bracketed expression, splitting it along the pipes and retrieving a list of elements (using a function)
        
        Args:
        expr (str): expression we want to normalize
        context_titles (list(str)): succesion of titles in which current section is nested
        funct_splitted2elems (funct): function (list(str), list(str)) -> list(str) ; applied on a splitted string, gives a list of elements to return
        post_processing_funct (function) : function  str, list(str) -> str ; after extraction of relevent substring, which function is to be applied for postprocessing
        brackets (couple(str)) : a couple indicating which is left and right bracket for expression

        Returns:
        set : a set of one unique str object which is the normalized str for the bracketed expression
        """
        def norm_bracket_expr_by_lambda_over_splitted(expr, context_titles, funct_splitted_and_context_titles_2elems, post_processing_funct, brackets):
            #splitted expression
            splitted = init_norm(expr, brackets)
            #the return object
            return_set = set()
            #get index of splitted element to return
            #try:
            try:
                list_elems = funct_splitted_and_context_titles_2elems(splitted, context_titles)
            except(IndexError):
                if self.ignore:
                    raise InputError("/".join(context_titles), "|".join(splitted), "list index out of range")
                else:
                    e = sys.exc_info()[1]
                    raise IndexError(str(e))
            #add pron to return set
            for elem in list_elems:
                return_set.add(post_processing_funct(elem, context_titles))
            return return_set

        """normalizes a bracketed expression retrieving the value of a "var = val" assignement (using a regex over var)
        
        Args:
        expr (str): expression we want to normalize
        context_titles (list(str)): succesion of titles in which current section is nested
        regex_attr (str): regex to be applied on each var of "var = val" assignements to know which values to extract
        post_processing_funct (function) : function  str, list(str) -> str ; after extraction of relevent substring, which function is to be applied for postprocessing
        brackets (couple(str)) : a couple indicating which is left and right bracket for expression

        Returns:
        set : a set of all string values assigned to variables matching the regex_attr
        """
        def norm_bracket_expr_by_attribute_name(expr, context_titles, regex_attr, post_processing_funct, brackets):
            #splitted expression
            splitted = init_norm(expr, brackets)
            #the return object
            return_set = set()
            for spl in splitted:
                subspl = spl.split("=")
                if len(subspl) > 1:
                    #check if the left side of assignement matches the regex
                    matcher = re.compile(regex_attr).match(subspl[0])
                    #if it does, add the right part (after post-processing)
                    if matcher:
                        return_set.add(post_processing_funct(subspl[1], context_titles))
            return return_set


        #if regex_attr_or_funct_splitted2elems is string, use it as a regex for norm_bracket_expr_by_attribute_name method
        if isinstance(regex_attr_or_funct_splitted2elems, str):
            norm_function = norm_bracket_expr_by_attribute_name
        #else use it as a function for norm_bracket_expr_by_lambda_over_splitted method
        else:
            norm_function = norm_bracket_expr_by_lambda_over_splitted
        return norm_function(expr, context_titles, regex_attr_or_funct_splitted2elems, post_processing_funct, brackets)


    """given a string content, retrieves all bracketed expressions out of it of matching name
        
    Args:
    content (str): content we want to extract bracketed expressions from
    context_titles (list(str)): succesion of titles in which current section is nested
    name (str): name (first element of bracketed expression) of expressions we want to extract
    brackets (couple(str)) : a couple indicating which is left and right bracket for expression
    norm_function (funct) : function  str, list(str) -> str ; a normalization function to apply on all extracted bracket expression
    keep_empty_expr (bool) : should empty extracated (& normalized) elements be kept in result

    Returns:
    list(str) : a list of all bracketed expressions matching required name
    """
    def extr_all_bracket_expr_by_name(self, content, context_titles, name, brackets = ("{{","}}"), norm_function=lambda expr, context_titles: expr, keep_empty_expr=False):
        left_bra = brackets[0]
        right_bra = brackets[1]
        #TODO(5): following regex could lead to bugs if nested bracketed expression exist
        pipe = "\|" if name else ""
        if left_bra == "{{" and right_bra == "}}":
            regex = self.titled_curly_bracketed_expr
        elif left_bra == "[[" and right_bra == "]]":
            regex = self.titled_square_bracketed_expr
        else:
            regex = "".join([left_bra, name, pipe, "([^", right_bra,"])*", right_bra])
        reg_bracket_expr_by_name = re.compile(regex)
        matcher = re.finditer(reg_bracket_expr_by_name, content)
        return_list_bracket_expr_by_name = []
        if matcher :
            for m in matcher:
                #normalize match
                normalized_match = list(norm_function(m.group(0), context_titles))
                #do not add if empty and keep_empty_expr=False
                if not keep_empty_expr and not normalized_match:
                    break
                return_list_bracket_expr_by_name += normalized_match
        return return_list_bracket_expr_by_name

    """given a string content, retrieves all bracketed expressions out of it
        
    Args:
    content (str): content we want to extract bracketed expressions from
    context_titles (list(str)): succesion of titles in which current section is nested
    brackets (couple(str)) : a couple indicating which is left and right bracket for expression
    norm_function (funct) : a normalization function to apply on all extracted bracket expression
    keep_empty_expr (bool) : should empty extracated (& normalized) elements be kept in result

    Returns:
    list(str) : a list of all bracketed expressions
    """
    def extr_all_bracket_expr(self, content, context_titles, brackets = ("{{","}}"), norm_function=lambda expr, context_titles: expr, keep_empty_expr=False):
        return self.extr_all_bracket_expr_by_name(content, context_titles, "", brackets, norm_function, keep_empty_expr)

    #in order to make the dictionary more easy to read when printed this functions returns a correctly indented string
    def pretty_str(self, parsed_dict):
        return json.dumps(parsed_dict, ensure_ascii=False, indent=4)


if __name__ == '__main__': 

    parser = argparse.ArgumentParser(description='A general parser for wiki pages.')
    parser.add_argument("-l", "--lang", help="Language targeted. (i.e. 'en', 'fr', 'de', 'es'...)", default=None)
    parser.add_argument("-p", "--path", help="Path for dump.", default=None)
    parser.add_argument("-o", "--out", help="Path for output of parsing.", default=None)
    parser.add_argument("-s", "--std", help="Print output on terminal", action='store_true', default=False)
    parser.add_argument("-e", "--err", help="Path for log of errors in parsing.", default=None)
    parser.add_argument("-b", "--bra", help="Expression for left-side of bracket.", default="{{")
    parser.add_argument("-k", "--ket", help="Expression for right-side of bracket.", default="}}")
    parser.add_argument("-a", "--add", help="Include param to add empty contents.", action='store_true')
    parser.add_argument("-c", "--cont", help="Name of variable contening main content (default \"content\")", default="content")
    parser.add_argument("-d", "--default", help="Default name of title variables when none found (default \"unnamed\")", default="unnamed")
    parser.add_argument("-n", "--norm", help="Index of bracketed expressions to normalize titles into.", default=None)
    parser.add_argument("-t", "--title", help="Name of bracketed expressions to extract content from.", default=None)
    parser.add_argument("-x", "--extr", help="Either a index or slice in format x:y (of element of split) or a regular expression (which variable name should match to extract value of)", default=None)
    parser.add_argument("-i", "--ign", help="Include param not to 'ignore' out of range errors during title normalization. Such errors will than stop execution, and title won't be normalized (instead of only being printed in error file).", action='store_false', default=True)

    args = parser.parse_args()
    wpp = Wiki_Page_Parser(args.ign, args.title, args.std)

    #define section titles normalisation function
    if args.norm:
        index = int(args.norm)
        section_titles_normalisation_funct = lambda title, context_titles: wpp.norm_bracket_expr(title, context_titles, lambda splitted, context_titles: [splitted[index]])
    else:
        section_titles_normalisation_funct = lambda title, context_titles: [title]

    #a function to check if args.extr is a valid input for list index
    def valid_index(param_str):
        reg_valid_index = re.compile("^(\-?[0-9]+):?(\-?[0-9]+)?$")
        return reg_valid_index.search(param_str)

    #if only one element is returned by extraction function, turn into a list
    def include_in_list_if_not_one(elem):
        if not isinstance(elem, list):
            return [elem]
        else:
            return elem

    #define content extraction function if numerical
    if valid_index(args.extr):
        index_double_colon = args.extr.find(":")
        if not index_double_colon == -1:
            x = int(args.extr[:index_double_colon])
            if not index_double_colon == len(args.extr) - 1:
                y = int(args.extr[index_double_colon+1:])
            else:
                y = None
            index = slice(x,y,1)
        else:
            index = int(args.extr)

        args.extr = lambda splitted, context_titles: include_in_list_if_not_one(splitted[index])
        

    norm_function = lambda expr, context_titles: wpp.norm_bracket_expr(expr, context_titles, args.extr, lambda expr, context_titles: expr, (args.bra, args.ket))
    if args.title:
        content_extraction_funct = lambda content, context_titles : wpp.extr_all_bracket_expr_by_name(content, context_titles, args.title, (args.bra, args.ket), norm_function, args.add)
    else:
        content_extraction_funct = lambda content, context_titles : wpp.extr_all_bracket_expr(content, context_titles, (args.bra, args.ket), norm_function, args.add)

    #parse
    wpp.parse_dump( lang=args.lang, 
                    path_to_dump=args.path, 
                    path_to_output=args.out, 
                    path_to_errors=args.err, 
                    section_titles_normalisation_funct=section_titles_normalisation_funct,
                    content_extraction_funct=content_extraction_funct,
                    add_empty_contents=args.add,
                    content_attribute_name=args.cont,
                    default_attribute_name=args.default
                    )

