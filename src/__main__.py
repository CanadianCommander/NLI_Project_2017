
# system imports
from sys import argv
import sys
import os
import re

# add NLI_Project_2017 directory to system path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# user imports
from src.util.Argument import Argument, ArgumentType
from src.feature_extraction.Phoneme_extraction import extract_phonemes

def print_usage():
    print("python src [-e extract ] [options]\n")
    print("[-e extract ]")
    print("\textract_phoneme,<path to file or dir>")
    print("\t\t example: python src -e \"extract_phoneme,/tmp/data.txt\"")


def parse_argv():
    if len(argv) <= 1:
        print_usage()

    arg_list = []

    try:
        for i in range(0, len(argv)):

            # extraction section
            if argv[i] == "-e":

                ext_arg = re.match(r"([\w\d]+),([\w\d\\/_\-.]+)", argv[i + 1])
                # phoneme extraction
                if ext_arg.group(1) == "extract_phoneme":
                    arg_list.append(Argument(ext_arg.group(1),ArgumentType.EXTRACT_PHONEME,
                                             Argument(ext_arg.group(2),ArgumentType.RAW_STRING)))
                    i += 1 # we consumed two arguments (-e and extract_phoneme,<path>)


    except IndexError:
        print_usage()
        print("ERROR: Unknown argument error.")

    return arg_list



# /////////////// main /////////////////////
def main():
    args = parse_argv()

    for arg in args:
        # execute action based on arg type

        # feature extraction section
        if arg.get_type() == ArgumentType.EXTRACT_PHONEME:
            arr_file_path = arg.get_sub_args()
            if len(arr_file_path) > 0:
                extract_phonemes(arr_file_path[0].get_string())
            else:
                print("ERROR: Unknown argument error.")


    print("done!")


main()