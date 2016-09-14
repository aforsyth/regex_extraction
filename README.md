# Field and value extraction from RPDR formatted electronic health records

## Extract numerical values and check for phrases in RPDR free-text notes

### Initial Setup (for developers and non-developers)

Install npm (Node package manager) if you don't have it already by installing Nodejs here: https://nodejs.org/en/download/

Open up a terminal (search for it with Spotlight search on Mac). All of the following commands are run in the terminal.

Install [localturk](https://github.com/danvk/localturk) with: `npm install -g localturk`

Navigate to the directory at which you want to install my code. Then, `git clone https://github.com/aforsyth/regex_extraction.git` to clone my code into a directory called regex_extraction.

`cd` into regex_extraction, and then you can run my code as explained. below.

### Extraction Usage

Example:

`python extract_values.py "/path/to/input_file.txt" --extract_numerical_value True --phrases "EF"`

The example will extract the value 60 from notes including "EF is 60" or "EF: 60", for example. Note that phrase is case insenstive. When extracting numerical values following a phrase, anything like "[phrase] [num]", [phrase] is [num]", "[phrase] of [num]", "phrase: [num]" will be matched.

`input_filename`: a path to an RPDR-formatted EHR text file.

`output_filename`: path to the output CSV file, which has one row per record in the input file with the following columns: EMPI, MRN_Type, MRN, Report_Number, Report_Date_Time, Report_Description, Report_Type and regex result

`extract_numerical_value`: True if extraction a numerical value, False if only checking whether the notes contain a phrase (i.e. a boolean 0 or 1). Defaults to False.

`phrases`: A list of comma separated phrases to check for either preceding the numerical value, or to check for their presence. The output will return numerical values following
any of the phrases in the supplied list. Example: "phrase1,phrase2,phrase3"

`report_description` (optional): If specified, only reports that exactly match the report_description value passed in will be examined.

`report_type` (optional): If specified, only reports that exactly match the report_type value passed in will be examined.

`turk_csv_filename` (optional): If specified, a CSV file will be written with
this filename that can be used to verify regex extraction with localturk.

### Localturk usage

Install localturk from here: https://github.com/danvk/localturk

Run `localturk --static_dir . localturk/extract.html localturk/tasks.csv localturk/outputs.csv` where `extract.html` is the localturk html template included in this repository, and `turk_csv_filename.csv` is the csv output with turk `turk_csv_filename` option.
