# WikiPageParser

A general parser for wiki pages (from Wiktionary or Wikipedia), converts html dumps into its equivalent dict structure, respecting nested structure of its sections.

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

Parsing methods can be given through functional arguments used to extract datas from content section on-the-go.
A couple of generic methods for data extraction in wikis are given.


Command line parameters are :

    * -l <...> Language targeted. (i.e. 'en', 'fr', 'de', 'es'...)
    * -p <...> Path for dump.
    * -o <...> Path for output of parsing.
    * -s Print output on terminal
    * -e <...> Path for log of errors in parsing.
    * -b <...> Expression for left-side of bracket.
    * -k <...> Expression for right-side of bracket.
    * -a Include param to add empty contents.
    * -c <...> Name of variable contening main content (default "content")
    * -d <...> Default name of title variables when none found (default "unnamed")
    * -n <...> Index of bracketed expressions to normalize titles into.
    * -t <...> Name of bracketed expressions to extract content from.
    * -x <...> Either a index or slice in format x:y (of element of split) or a regular expression (which variable name should match to extract value of)
    * -i Include param not to 'ignore' out of range errors during title normalization. Such errors will than stop execution, and title won't be normalized (instead of only being printed in error file).


*usage*:

    #extract from english wiktionary dictionary with Language, Part-of-Speech and Pronuciation as a JSON
    python3 WikiPageParser.py -l "en" -p <Path for dump> -o "out_file" -e "errors_file" -c "prons" -t "IPA" -x 2: -s
    #extract from german wiktionary dictionary with Language, Part-of-Speech and Pronuciation as a JSON
    python3 WikiPageParser.py -l "de" -p <Path for dump> -o "out_file" -e "errors_file" -c "prons" -t "Lautschrift" -x 1 -n 1 -s
    #extract from french wiktionary dictionary with Language, Part-of-Speech and Pronuciation as a JSON
    python3 WikiPageParser.py -l "fr" -p <Path for dump> -o "out_file" -e "errors_file" -c "prons" -n 1 -t "pron" -x 1 -s

    #extract page links from wikipedia dumps as a JSON
    python3 WikiPageParser.py -l "fr" -p <Path for dump> -o "out_file" -e "errors_file" -c "links" -x 0 -b "[[" -k "]]" -s
