# Produce a namespapce object populated from
# a  JSON config file.
#
# JSON permits the expression of a defaults
# with proper type.
# 
# in the follwo on command line parser, python...
# DOES  NTO replace a confg file default wiht a command line default.
# DOES replace a config fle  wiht an explicit command line switch
#
# Extras is a the command line stripped of the config switch and parameters
# so that the upper command line can be unawre of it.
#  Hmm how does this work with help?
import argparse
import json
import sys
import pprint

def get_from_config():
    # The following stanza pull jus tthe --cfg option
    # from  the command line.
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--cfg')
    #args =parser.parse_known_args(sys.argv)
    (args, extras) =parser.parse_known_args()
    if args.cfg:
        with open(args.cfg,'r') as json_data:
            d = json.load(json_data)
            for key in d.keys():
                args.__dict__[key] = d[key]
    return (args, remaining)


(args, cleaned_argv) = get_from_config()
parser = argparse.ArgumentParser()
parser.add_argument('--afloat',default=0.0, type=float, help="some float")
parser.add_argument('--cfg',help="config file") #so it appears in help
parser.parse_args(extras,namespace=cleaned_argv) # parse the cleaned_argv
print (args.afloat)
