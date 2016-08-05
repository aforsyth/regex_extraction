# Field and value extraction from electronic health records

## Extract numerical values and check for phrases in electronic health records

### Usage

Example:

python extract_values.py --input_filename "/path/to/file.txt" --output_filename "/path_to_file.csv" --extract_numerical_value True --phrase "EF" --value_indicators "is,of,:"

Example could be used to extract the value 60 from strings like "EF is 60" or "EF: 60", for example.

input_filename: a path to an RPDR-formatted EHR text file.

output_filename: path to the output CSV file, which has one row per record in the input file with the following columns: EMPI, MRN_Type, MRN, Report_Number, Report_Date_Time, Report_Description, Report_Type and regex result

extract_numerical_value: True if extraction a numerical value, False if only checking whether the notes contain a phrase (i.e. a boolean 0 or 1). Defaults to False.

phrase: The phrase to check for either preceding the numerical value, or to check for its presence.

value_indicators (only used if extract_numerical_value is True): A string containing comma separated tokens or words expected to precede the numerical value.

### Code
