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

`group_by_patient`: If specified, all patient notes for a single patient will be grouped together (i.e. there will be one output row per patient with a 1 if a phrase was present, else 0, or the first numerical value seen if extracting a numerical value). By default, this option enables the `context_size` option with a value of 10 because patient notes concatenated together would otherwise be too long to display in localturk.

`context_size`: Specified along with an integer, meaning that `context_size` number of words will be displayed before and after each regex match during localturk evaluation. This is useful 1) so that it's easier to identify matches, and 2) to reduce the total amount of text displayed, e.g. when a single note is too large to be loaded by localturk, such as when all notes for a single patient are concatenated when using the `group_by_patient` option. Around ~10 is a good starting value for this.

### Localturk usage

Install localturk from here: https://github.com/danvk/localturk

Run `localturk --static_dir . localturk/extract.html localturk/tasks.csv localturk/outputs.csv` where `extract.html` is the localturk html template included in this repository, and `turk_csv_filename.csv` is the csv output with turk `turk_csv_filename` option.

### Note Filtering Usage

`filter_notes.py` allows you to filter an RPDR note file to include only notes from patients of interest and only notes for those patients within a specified time range. This could be used, for example, to find notes for a patient that are within X days before and Y days after a certain procedure.

Running `filter_notes.py rpdr_filename filter_csv_filename` will output a RPDR notes file of the same format as the origin, but filtered as described. It will write this new file to the same filename as the input file, but with "_filtered" added to the same before the file extension. Optionally, you can specify the output filename with `--output_filename`.

Note that filter_csv_filename should point to a file that looks like:
empi,procedure_date,days_before,days_after,include
1111,5/12/2016,30,0,1
1121,5/13/2016,10,10,0

Patients with a 0 for include will not be included in the output notes file.
